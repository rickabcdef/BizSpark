# -*- coding: utf-8 -*-
"""state.settings — F-04 设置（F11：6 项封顶，负责人：F）

6 项写死，多一项都不做（F11 表）：
  1 country                    6 国下拉，默认系统猜测
  2 language                   仅 English（自检包显示 中文（自检）且不可切换；软件内无切换按钮）
  3 export_dir                 $DOCUMENTS/BizSpark
  4 library_check              默认开（关掉 = 100% 离线）
  5 follow_system_appearance   默认开
  6 crash_notes                默认关；开启后日志内容白名单 = 错误码 + 版本 + 时间戳

规则：非法键/非法值**静默忽略**不报错（F11 步骤 1、§2.6 禁止把错误码暴露给用户）。
"""

import json
import os
import time

from . import paths

SETTINGS_KEYS = ("country", "language", "export_dir",
                 "library_check", "follow_system_appearance", "crash_notes")

SUPPORTED_COUNTRIES = ("US", "CA", "UK", "AU", "SG", "PH")

# 崩溃日志白名单：只允许这三个字段，禁止答案/点子 id/路径/设备指纹（F11 步骤 4）
CRASH_LOG_FIELDS = ("ts", "code", "version")


def default_country():
    """系统猜测：按 locale 语言到 6 国的保守映射，猜不到默认 US。"""
    lang = (os.environ.get("LC_ALL") or os.environ.get("LANG") or "").lower()
    if lang.startswith("en_gb") or "en-gb" in lang:
        return "UK"
    if lang.startswith("en_ca") or "en-ca" in lang:
        return "CA"
    if lang.startswith("en_au") or "en-au" in lang:
        return "AU"
    if "sg" in lang:
        return "SG"
    if "ph" in lang:
        return "PH"
    return "US"


def defaults():
    """6 项默认值（F11 表；language 由构建模式决定，软件内不可切换）。"""
    cn = paths.build_mode() == "cn-selfcheck"
    return {
        "country": default_country(),
        "language": "zh-CN" if cn else "en-US",
        "export_dir": paths.default_export_dir(),
        "library_check": True,
        "follow_system_appearance": True,
        "crash_notes": False,
    }


def _valid(key, value):
    """类型/枚举校验：非法值静默忽略（保留旧值）。"""
    if key == "country":
        return isinstance(value, str) and value.upper() in SUPPORTED_COUNTRIES
    if key == "language":
        # 仅允许当前构建的语言值：自检包 zh-CN，售卖版 en-US（禁止切换，§F14.3）
        return value == ("zh-CN" if paths.build_mode() == "cn-selfcheck" else "en-US")
    if key == "export_dir":
        return isinstance(value, str) and bool(value.strip())
    return isinstance(value, bool)


def normalize(stored):
    """读盘后补齐缺失键 + 丢弃非法值；返回 6 项完整设置。"""
    out = defaults()
    if isinstance(stored, dict):
        for k in SETTINGS_KEYS:
            if k in stored and _valid(k, stored[k]):
                out[k] = stored[k].strip() if k == "export_dir" and isinstance(stored[k], str) else stored[k]
    return out


def apply_patch(stored, patch):
    """写设置：只认 6 个键，逐个校验，非法键/值忽略（不报错）。返回新设置。"""
    current = normalize(stored)
    if isinstance(patch, dict):
        for k, v in patch.items():
            if k in SETTINGS_KEYS and _valid(k, v):
                current[k] = v.strip() if k == "export_dir" and isinstance(v, str) else v
    return current


def log_crash(code, version, settings):
    """F-04 崩溃日志（默认关）：仅 enabled 时写；内容白名单 = 时间戳 + 错误码 + 版本。

    禁止写入：答案、点子 id、文件路径、设备指纹、任何用户内容（F11 步骤 4）。
    """
    cfg = normalize(settings)
    if not cfg.get("crash_notes"):
        return False
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "code": str(code or "")[:40],
        "version": str(version or "")[:20],
    }
    try:
        os.makedirs(os.path.dirname(paths.crash_log_path()), exist_ok=True)
        with open(paths.crash_log_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps({k: record[k] for k in CRASH_LOG_FIELDS},
                               ensure_ascii=False, sort_keys=True) + "\n")
        return True
    except OSError:
        return False  # 日志写不了也绝不打扰用户


# ---------------------------------------------------------------- §2.4 handlers

def _store():
    """延迟导入：store 依赖 settings，避免循环导入。"""
    from . import store
    return store


def get_settings(payload=None):
    """§2.4 get_settings：读 6 项（缺失/非法值补齐为默认，不报错）。"""
    st = _store().load_state()
    cfg = normalize(st.get("settings"))
    # export_dir 与 state.export_dir（F-10 导出目录记忆）保持一致，先记住的优先
    if isinstance(st.get("export_dir"), str) and st["export_dir"]:
        cfg["export_dir"] = st["export_dir"]
    return cfg, None


def set_settings(payload):
    """§2.4 set_settings：写 6 项；非法键/非法值静默忽略（F11 步骤 1）。"""
    patch = payload.get("patch") if isinstance(payload, dict) else None
    if not isinstance(patch, dict):
        patch = payload if isinstance(payload, dict) else {}
    store = _store()
    st = store.load_state()
    st["settings"] = apply_patch(st.get("settings"), patch)
    if isinstance(patch.get("export_dir"), str) and patch["export_dir"].strip():
        st["export_dir"] = patch["export_dir"].strip()  # F-10
    store.save_state(st)
    return normalize(st["settings"]), None


def log_crash_handler(payload):
    """§2.4 log_crash：默认关；开启时只写 错误码 + 版本 + 时间戳。"""
    payload = payload if isinstance(payload, dict) else {}
    st = _store().load_state()
    written = log_crash(payload.get("code"), payload.get("version"), st.get("settings"))
    return {"ok": True, "written": bool(written)}, None
