# -*- coding: utf-8 -*-
"""state.merge — F-05/F-06/F-07/F-09 月度增量合并与回滚（F09 / §3.7 / 负责人：F）

职责（客户端侧；拉取由 A、生成由 D）：
- 工作库 `library/current.json` 是**唯一可写库**；`baseline_v1.json` 只读，任何操作不改它（F-09）
- 合并前备份 → `library/rollback/{release}.json`，只保留最近 3 份（F-06）
- 按 §3.7 应用 add/revise/retire（revise 仅白名单字段、retire 只置 status=retired，不硬删）
- 合并后跑 V-01 / V-02 / V-11；**失败整体回滚**，用户无感（F-05）
- 成功后更新 state.library_version + 本地时间线（不上传任何确认，F-07）
- 断网一月回来：`apply_sequence` 按 release 顺序逐包合并（T-30-6）

复用 D 的纯函数 `library.delta_tool.merge_delta`（不重写、不修改 D 的文件）。
"""

import hashlib
import json
import os
import re
import shutil
import time

from . import paths
from . import store

ROLLBACK_KEEP = 3          # F-06：只保留最近 3 份
TARGET_BASELINE = "v1"     # §3.7
RELEASE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DELTA_MAX_BYTES = 200 * 1024  # T-30-5：单包 >200KB 静默跳过（防超大包写爆工作库）


# ---------------------------------------------------------------- 工作库

def ensure_working_library(force_rebuild=False):
    """F-08 步骤 5：首次启动把内置只读副本复制为工作库（幂等，绝不反向写 baseline）。

    force_rebuild=True：工作库存在但内容损坏（F13 整库损坏）时从只读副本重建。
    """
    current = paths.current_library_path()
    if os.path.isfile(current) and not force_rebuild:
        return current
    paths.ensure_app_dirs()
    src = paths.baseline_readonly_path()
    try:
        with open(src, encoding="utf-8") as f:
            data = json.load(f)
        ideas = data if isinstance(data, list) else data.get("ideas", [])
        lib = {"version": store.DEFAULT_LIBRARY_VERSION, "baseline": TARGET_BASELINE,
               "updated_at": store._now_iso(), "ideas": ideas}
        _atomic_write_json(current, lib)
        # state 里的库版本与条数同步（首次启动）
        st = store.load_state()
        st["library_version"] = lib["version"]
        st["library_ideas"] = len(ideas)
        store.save_state(st)
    except (OSError, ValueError):
        return current  # 复制失败不阻断启动：C 会回退只读副本/fallback
    return current


def read_current():
    """读工作库。损坏/缺失 → 从只读副本重建（F13 整库损坏降级），返回 (lib, rebuilt)。"""
    path = paths.current_library_path()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        ideas = data if isinstance(data, list) else data.get("ideas")
        if isinstance(ideas, list) and ideas:
            if isinstance(data, dict):
                return data, False
            return {"version": store.DEFAULT_LIBRARY_VERSION, "ideas": ideas}, False
    except (OSError, ValueError):
        pass
    ensure_working_library(force_rebuild=True)   # 损坏 → 从只读副本重建（F13）
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), True
    except (OSError, ValueError):
        return {"version": store.DEFAULT_LIBRARY_VERSION, "ideas": []}, True


def library_info():
    """当前库版本与条数（Library 页 / check_library 用）。"""
    lib, _ = read_current()
    ideas = lib.get("ideas") if isinstance(lib, dict) else []
    ideas = ideas if isinstance(ideas, list) else []
    return {
        "version": lib.get("version") or store.DEFAULT_LIBRARY_VERSION,
        "ideas": len(ideas),
        "industries": 26,
        "countries": 6,
        "baseline": lib.get("baseline") or TARGET_BASELINE,
        "updated_at": lib.get("updated_at"),
    }


def baseline_checksum():
    """F-09 验收：baseline 校验和（任何用户操作前后必须不变）。"""
    path = paths.baseline_readonly_path()
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


# ---------------------------------------------------------------- 备份 / 回滚

def _backup(release):
    current = paths.current_library_path()
    if not os.path.isfile(current):
        return None
    paths.rollback_dir(create=True)
    dst = os.path.join(paths.rollback_dir(), "%s.json" % release)
    try:
        shutil.copy2(current, dst)
    except OSError:
        return None
    _prune_rollbacks()
    return dst


def _prune_rollbacks(keep=ROLLBACK_KEEP):
    """F-06：只保留最近 3 份（文件名即 release，字典序=时间序）。"""
    try:
        names = sorted(n for n in os.listdir(paths.rollback_dir()) if n.endswith(".json"))
    except OSError:
        return
    for old in names[:-keep] if len(names) > keep else []:
        try:
            os.remove(os.path.join(paths.rollback_dir(), old))
        except OSError:
            pass


def _restore(backup_path):
    """整体回滚：把备份原样放回工作库（原子替换）。"""
    if not backup_path or not os.path.isfile(backup_path):
        return False
    try:
        tmp = paths.current_library_path() + ".restore-%d" % os.getpid()
        shutil.copy2(backup_path, tmp)
        os.replace(tmp, paths.current_library_path())
        return True
    except OSError:
        return False


def _atomic_write_json(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = "%s.tmp-%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


# ---------------------------------------------------------------- 校验（V-01/V-02/V-11）

def _validate_library(ideas):
    """V-01 唯一性 + V-02 全字段校验；返回错误列表（空 = 通过）。"""
    errors = []
    seen = set()
    for idea in ideas:
        if not isinstance(idea, dict) or not isinstance(idea.get("id"), str):
            errors.append("V-02 invalid item")
            continue
        if idea["id"] in seen:
            errors.append("V-01 duplicate id %s" % idea["id"])
            continue
        seen.add(idea["id"])
    try:
        from library.validate import validate_idea
        for idea in ideas:
            if isinstance(idea, dict):
                validate_idea(idea, errors, [])
    except Exception:
        # 校验器不可用时不阻断合并（宁可放行也不误伤用户）；V-01 已在上方独立完成
        pass
    return errors


def _version_of(release):
    """release(2026-12-01) → 展示版本 2026.12（Library 页一行）。"""
    return release[:7].replace("-", ".")


# ---------------------------------------------------------------- 合并

def apply_delta(payload):
    """F-05：应用一个 delta（§2.4 apply_delta）。失败整体回滚，用户无感。

    payload 既可是 delta 本体（B 的 applyDelta 直传），也可是 {"delta": {...}}。
    """
    delta = payload.get("delta") if isinstance(payload, dict) and isinstance(payload.get("delta"), dict) else payload
    if not isinstance(delta, dict):
        return None, {"code": "E_BAD_REQUEST", "message": "delta required", "recoverable": True}

    release = delta.get("release")
    if not isinstance(release, str) or not RELEASE_RE.match(release):
        return None, {"code": "E_DELTA_INVALID", "message": "release not YYYY-MM-DD",
                      "recoverable": True}
    target = delta.get("target_baseline") or TARGET_BASELINE
    if target != TARGET_BASELINE:
        # 老客户端不强行吃新包（F09 步骤 4 同口径）
        return None, {"code": "E_DELTA_INVALID", "message": "target_baseline mismatch",
                      "recoverable": True}

    lib, _rebuilt = read_current()
    current_version = lib.get("version") or store.DEFAULT_LIBRARY_VERSION

    # D-04/D-05 修复（PM）：运行期防线——
    # 1) 体积闸门：>200KB 的包静默跳过，不备份不写盘（T-30-5）
    try:
        raw_size = len(json.dumps(delta))
    except (TypeError, ValueError):
        return None, {"code": "E_DELTA_INVALID", "message": "delta not JSON-serializable",
                      "recoverable": True}
    if raw_size > DELTA_MAX_BYTES:
        return {"version": current_version, "ideas": len(lib.get("ideas") or []),
                "applied": False, "skipped": "oversized"}, None

    # 2) revise 白名单复用（V-11）：create_delta 只在生成期校验，这里运行期兜底
    try:
        from library.validate import REVISE_WHITELIST, validate_idea  # noqa: E401
    except ImportError:  # Store 裁剪极端情况下降级为只做体积/结构防线
        REVISE_WHITELIST = None  # type: ignore[assignment]
        validate_idea = None     # type: ignore[assignment]
    for r in delta.get("revise") or []:
        if isinstance(r, dict) and REVISE_WHITELIST is not None:
            bad = set(r.keys()) - REVISE_WHITELIST - {"id"}
            if bad:
                return None, {"code": "E_DELTA_INVALID",
                              "message": "revise %s has non-whitelisted fields: %s"
                                         % (r.get("id"), sorted(bad)),
                              "recoverable": True}
    for a in delta.get("add") or []:
        if not isinstance(a, dict) or not a.get("id"):
            return None, {"code": "E_DELTA_INVALID", "message": "add item missing id",
                          "recoverable": True}
        if validate_idea is not None:
            _errs, _warns = [], []
            validate_idea(a, _errs, _warns)
            if _errs:
                return None, {"code": "E_DELTA_INVALID", "message": _errs[0],
                              "recoverable": True}

    new_version = _version_of(release)
    if new_version <= current_version:
        # 幂等：已合并过或更旧的包，静默跳过（A 的 manifest 判断之外的二次保险）
        return {"version": current_version, "ideas": len(lib.get("ideas") or []),
                "applied": False}, None

    ideas = lib.get("ideas") if isinstance(lib.get("ideas"), list) else []

    # 1) 合并前先备份（F-05/T-40：失败可整体回滚）
    backup = _backup(release)

    # 2) 合并（D 的纯函数；ValueError = V-11/白名单/重复 add）
    try:
        from library.delta_tool import merge_delta
        merged = merge_delta(ideas, delta)
    except ValueError as exc:
        return None, {"code": "E_DELTA_INVALID", "message": str(exc), "recoverable": True}
    except Exception as exc:
        return None, {"code": "E_DELTA_INVALID", "message": "merge failed: %s" % exc,
                      "recoverable": True}

    # 3) 合并后校验 V-01/V-02（失败整体回滚，磁盘库保持原样）
    errors = _validate_library(merged)
    if errors:
        _restore(backup)  # 未写盘，仍显式恢复一次，保证"失败即原样"
        return None, {"code": "E_DELTA_INVALID", "message": errors[0], "recoverable": True}

    # 4) 原子写工作库（只写 current.json，绝不碰 baseline）
    new_lib = {"version": new_version, "baseline": TARGET_BASELINE,
               "updated_at": store._now_iso(), "ideas": merged}
    try:
        _atomic_write_json(paths.current_library_path(), new_lib)
    except OSError:
        _restore(backup)
        return None, {"code": "E_LIBRARY_WRITE", "message": "write failed", "recoverable": True}

    # 5) 成功：更新 state（版本 + 时间线；不上传确认，F-07）
    st = store.load_state()
    st["library_version"] = new_version
    st["library_ideas"] = len(merged)
    st["last_library_check"] = store._now_iso()
    timeline = st.get("timeline") if isinstance(st.get("timeline"), list) else []
    timeline.append({"date": release, "release": release, "ideas": len(merged),
                     "added": len(delta.get("add") or []),
                     "revised": len(delta.get("revise") or []),
                     "retired": len(delta.get("retire") or [])})
    st["timeline"] = timeline[-24:]  # 两年内足够 Library 页展示
    store.save_state(st)

    return {"version": new_version, "ideas": len(merged), "applied": True}, None


def apply_sequence(deltas):
    """F-06 / T-30-6：断网一月回来，按 release 顺序逐包合并；任一失败即停（已成功的保留）。"""
    if not isinstance(deltas, list) or not deltas:
        return None, {"code": "E_BAD_REQUEST", "message": "deltas required", "recoverable": True}
    ordered = sorted([d for d in deltas if isinstance(d, dict)],
                     key=lambda d: str(d.get("release") or ""))
    last = None
    for delta in ordered:
        data, err = apply_delta(delta)
        if err:
            return last, err
        last = data
    return last, None


def check_library(payload=None):
    """§2.4 check_library（F+A）：F 只报告本地版本，**不联网**（拉取在 A 的 Rust 层）。

    失败/无网时静默返回本地版本，界面无任何变化（F13）。
    """
    info = library_info()
    if not os.path.isfile(paths.current_library_path()):
        ensure_working_library()
        info = library_info()
    st = store.load_state()
    st["last_library_check"] = store._now_iso()
    store.save_state(st)
    info["up_to_date"] = True
    return info, None


def is_newer(latest_version, local_version=None):
    """F+A 边界：manifest.latest 与本地版本比较（YYYY.MM 字符串可比）。"""
    local = local_version or library_info().get("version") or ""
    return str(latest_version) > str(local)
