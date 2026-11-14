# -*- coding: utf-8 -*-
"""state.store — F-01/F-02/F-03/F-10 本地状态（§2.5 / F07 / F11 / 负责人：F）

state.json 结构（K-6 契约，冻结）：
{
  "v": 1,
  "first_run": true,
  "last_answers": {country, capital, hours, assets[], risk},
  "last_result": {ideas[], checked, filtered, cached_at},   # 结果页超时兜底（T-31）
  "saved": [{id, saved_at, match_pct, min_capital}],         # F07 存档（同 id 去重）
  "settings": {6 项},
  "library_version": "2026.11",
  "library_ideas": 312,
  "timeline": [{date, release, ideas}],
  "export_dir": null,
  "last_library_check": null
}

降级（F13，T-35）：
- 不存在 → 创建空状态（首次启动）
- 损坏（JSON 解析失败/根不是 dict）→ 备份为 state.json.corrupt-<ts> → **静默重建**空存档，不动其他文件、不弹窗
- 写盘原子（tmp + os.replace），断电不产生半截文件

铁律：不联网、不写用户数据到日志、不硬删库条目、任何用户操作都不改 baseline_v1.json。
"""

import json
import os
import time

from . import paths
from . import settings as settings_mod

# PM 2026-11-14：存档行标题要与详情页同口径走 zhpack 中文覆盖（老板反馈：
# 结果页/详情是中文，「我的点子」列表却是英文标题）。engine 不反向依赖 state，
# 此导入无环。
from engine import zhpack as _zhpack
from engine import money as _money

STATE_V = 1
DEFAULT_LIBRARY_VERSION = "2026.11"

SAVED_MAX = 500  # 存档上限（防无限增长；超出丢最旧，不弹提示）

# 展示用货币符号（min_capital 只是列表行文案；金额数字始终来自库字段，不写死售价）
CURRENCY_SYMBOL = {"USD": "$", "CAD": "CA$", "GBP": "£", "AUD": "A$", "SGD": "S$", "PHP": "₱"}

# 库缓存（1MB JSON，避免每次调用重复读盘；mtime 变化即失效）
_LIB_CACHE = {"path": None, "mtime": None, "ideas": []}


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _today():
    return time.strftime("%Y-%m-%d", time.localtime())


def default_state():
    return {
        "v": STATE_V,
        "first_run": True,
        "last_answers": None,
        "last_result": None,
        "saved": [],
        "settings": settings_mod.defaults(),
        "library_version": DEFAULT_LIBRARY_VERSION,
        "library_ideas": 0,
        "timeline": [],
        "export_dir": None,
        "last_library_check": None,
    }


def _atomic_write_json(path, obj):
    """原子写：同目录 tmp + os.replace（Windows 下也可跨进程安全替换）。"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = "%s.tmp-%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _repair(raw_path):
    """损坏静默重建：把坏文件改名留档（不删除用户数据），返回空状态。"""
    try:
        os.replace(raw_path, "%s.corrupt-%d" % (raw_path, int(time.time())))
    except OSError:
        pass
    return default_state()


def load_state():
    """读 state.json；不存在→创建；损坏→静默重建（T-35）。永不抛异常。"""
    path = paths.state_path()
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            return _repair(path)
    except FileNotFoundError:
        st = default_state()
        try:
            paths.ensure_app_dirs()
            _atomic_write_json(path, st)
        except OSError:
            pass
        return st
    except (OSError, ValueError):
        return _repair(path)

    # 逐键补齐（老版本/被手改过也能用），过非法结构一律回默认
    st = default_state()
    st.update({k: v for k, v in raw.items() if k in st})
    if not isinstance(st.get("saved"), list):
        st["saved"] = []
    st["saved"] = [s for s in st["saved"] if isinstance(s, dict) and isinstance(s.get("id"), str)]
    if not isinstance(st.get("timeline"), list):
        st["timeline"] = []
    if not isinstance(st.get("last_answers"), (dict, type(None))):
        st["last_answers"] = None
    if not isinstance(st.get("last_result"), (dict, type(None))):
        st["last_result"] = None
    st["settings"] = settings_mod.normalize(st.get("settings"))
    if not isinstance(st.get("library_version"), str) or not st["library_version"]:
        st["library_version"] = DEFAULT_LIBRARY_VERSION
    if not isinstance(st.get("library_ideas"), int):
        st["library_ideas"] = 0
    return st


def save_state(st):
    """原子写回；失败静默（状态写不了也不能阻断主链路）。返回 bool。"""
    try:
        paths.ensure_app_dirs()
        _atomic_write_json(paths.state_path(), st)
        return True
    except OSError:
        return False


# ---------------------------------------------------------------- 库读取（只读）

def load_ideas():
    """读工作库（F 的 current.json 优先，回退内置只读副本）。带 mtime 缓存，永不写库。"""
    for path in (paths.current_library_path(), paths.baseline_readonly_path()):
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        if _LIB_CACHE["path"] == path and _LIB_CACHE["mtime"] == mtime:
            return _LIB_CACHE["ideas"]
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        ideas = data if isinstance(data, list) else (data.get("ideas") if isinstance(data, dict) else None)
        if isinstance(ideas, list) and ideas:
            _LIB_CACHE.update({"path": path, "mtime": mtime, "ideas": ideas})
            return ideas
    # 最后兜底：D 预置 3 条（整库损坏）
    try:
        with open(paths.fallback_ideas_path(), encoding="utf-8") as f:
            data = json.load(f)
        ideas = data if isinstance(data, list) else data.get("ideas", [])
        return ideas if isinstance(ideas, list) else []
    except (OSError, ValueError):
        return []


def find_idea(idea_id):
    for idea in load_ideas():
        if isinstance(idea, dict) and idea.get("id") == idea_id:
            return idea
    return None


def _idea_card(item):
    """给存档行用的展示字段（金额来自库 + currency 覆盖，不写死售价）。

    PM 2026-11-14：标题与详情页同口径——先过 zhpack 中文覆盖（is_zh 时），
    缺项回退英文原文。金额随所选国家货币换算（问卷答案国家优先，设置国家兜底），
    USD 保持旧格式（From + 符号 + 原值），非 USD 用货币符号前缀 + 换算金额。
    """
    shown = _zhpack.overlay(item) if isinstance(item, dict) else item
    title = shown.get("title") if isinstance(shown.get("title"), str) else item.get("id")
    capital = item.get("min_capital")
    currency = "USD"
    overrides = item.get("overrides") if isinstance(item.get("overrides"), dict) else {}
    # 国家：问卷答案优先（货币口径与结果页/详情一致），缺省用设置里的国家
    country = None
    st = load_state()
    la = st.get("last_answers") if isinstance(st, dict) else None
    if isinstance(la, dict) and isinstance(la.get("country"), str) and la.get("country").strip():
        country = la["country"].strip().upper()
    if not country:
        try:
            country = settings_mod.normalize(load_state().get("settings")).get("country")
        except OSError:
            country = None
    if country and isinstance(overrides.get(country), dict) and overrides[country].get("currency"):
        currency = overrides[country]["currency"]
    else:
        currency = _money.currency_for(country, overrides)
    min_capital = None
    if isinstance(capital, (int, float)):
        if currency == "USD":
            symbol = CURRENCY_SYMBOL.get("USD", "$")
            min_capital = "From %s%s" % (symbol, format(int(capital), ","))
        else:
            amount = _money.fmt_symbol(capital, currency)
            min_capital = ("起步 " + amount) if _zhpack.is_zh() else ("From " + amount)
    return {"title": title, "min_capital": min_capital}


# ---------------------------------------------------------------- §2.4 handlers

def get_state(payload=None):
    """§2.4 get_state：存档、设置、库版本、授权状态、首启标记、两处缓存。"""
    st = load_state()
    license_state = "activated" if os.path.isfile(paths.license_path()) else "none"
    ideas = load_ideas()
    library_version = st["library_version"]
    ideas_count = len(ideas) or st["library_ideas"]
    # 工作库尚未建立（首次启动）→ 顺手建好，保证 C 读到的是同一份库
    if not os.path.isfile(paths.current_library_path()):
        try:
            from . import merge as merge_mod
            merge_mod.ensure_working_library()
            library_version = merge_mod.library_info().get("version", library_version)
        except OSError:
            pass
    return {
        "saved_count": len(st["saved"]),
        "saved": st["saved"],
        "last_answers": st["last_answers"],
        "last_result": st["last_result"],
        "settings": settings_mod.normalize(st["settings"]),
        "export_dir": st.get("export_dir") or settings_mod.normalize(st["settings"])["export_dir"],
        "library_version": library_version,
        "library_ideas": ideas_count,
        "library": {"version": library_version, "ideas": ideas_count,
                    "industries": 26, "countries": 6},
        "license_state": license_state,
        "first_run": bool(st.get("first_run", True)),
        "timeline": st.get("timeline") or [],
        # PM 2026-11-14：静态汇率表（USD→本地乘数）给前端做问卷资金档/复述句本地化
        "fx": _money.load_fx(),
        "paths": paths.all_paths(),
    }, None


def save_answers(payload):
    """§2.4 save_answers：5 题答案落 last_answers（逐题增量合并，仅本地缓存）。"""
    st = load_state()
    incoming = payload.get("answers") if isinstance(payload, dict) else None
    if not isinstance(incoming, dict):
        incoming = payload if isinstance(payload, dict) else {}
    merged = dict(st["last_answers"]) if isinstance(st["last_answers"], dict) else {}
    for k, v in incoming.items():
        if k == "answers":
            continue
        if isinstance(v, (str, int, float, bool)) or (isinstance(v, list) and
                                                      all(isinstance(x, str) for x in v)):
            merged[k] = v
    st["last_answers"] = merged or None
    st["first_run"] = False  # 用户已开始使用，首启标记落定
    save_state(st)
    return {"ok": True}, None


def save_last_result(result):
    """F-02：缓存上一轮诊断结果（F04 步骤 10 / T-31 超时兜底用）。非 §2.4 cmd，内部调用。"""
    if not isinstance(result, dict):
        return
    st = load_state()
    st["last_result"] = {
        "ideas": result.get("ideas") if isinstance(result.get("ideas"), list) else [],
        "checked": result.get("checked") if isinstance(result.get("checked"), int) else 0,
        "filtered": result.get("filtered") if isinstance(result.get("filtered"), int) else 0,
        "cached_at": _now_iso(),
    }
    save_state(st)


def save_idea(payload):
    """F07 步骤 1：存档追加；**同 id 去重，不覆盖时间**（幂等）。"""
    idea_id = payload.get("id") if isinstance(payload, dict) else None
    if not isinstance(idea_id, str) or not idea_id:
        return None, {"code": "E_BAD_REQUEST", "message": "id is required", "recoverable": True}
    st = load_state()
    if any(s.get("id") == idea_id for s in st["saved"]):
        return {"ok": True, "duplicate": True, "count": len(st["saved"])}, None
    item = find_idea(idea_id) or {"id": idea_id}
    card = _idea_card(item)
    entry = {"id": idea_id, "saved_at": _today(), "match_pct": None, "min_capital": card["min_capital"],
             "title": card["title"]}
    match = payload.get("match_pct")
    if isinstance(match, (int, float)):
        entry["match_pct"] = int(match)
    st["saved"].append(entry)
    if len(st["saved"]) > SAVED_MAX:
        st["saved"] = st["saved"][-SAVED_MAX:]
    save_state(st)
    return {"ok": True, "count": len(st["saved"])}, None


def list_saved(payload=None):
    """F07 步骤 2：按 saved_at 倒序（同日保持插入序）。archive 中已 retire 的仍返回（不显示标注）。"""
    st = load_state()
    items = list(st["saved"])
    items.sort(key=lambda s: str(s.get("saved_at") or ""), reverse=True)
    # 标题按当前 locale 重算（PM 2026-11-14：存档时刻的语言可能与当前不同，
    # 且旧条目存的是英文名；库内还在的条目用 _idea_card 覆盖口径重算，
    # 已 retire / 库中删除的条目保留存量标题）。
    for it in items:
        lib_item = find_idea(it.get("id"))
        if lib_item is not None:
            card = _idea_card(lib_item)
            it["title"] = card["title"]
            if it.get("min_capital") is None:
                it["min_capital"] = card["min_capital"]
        elif not it.get("title") or it.get("min_capital") is None:
            card = _idea_card({"id": it.get("id")})
            it["title"] = it.get("title") or card["title"]
            if it.get("min_capital") is None:
                it["min_capital"] = card["min_capital"]
    return {"items": items}, None


def clear_saved(payload=None):
    """F07 步骤 2：清空（二次确认由 B 视图层负责，本层幂等）。"""
    st = load_state()
    st["saved"] = []
    save_state(st)
    return {"ok": True, "count": 0}, None


def _hours_label(idea):
    return {"<10": "Under 10 h/wk", "10-25": "10–25 h/wk", "full": "Full-time"}.get(
        idea.get("hours_per_week"), "—")


def _payback_label(idea):
    days = idea.get("payback_days")
    return "~%d days" % int(days) if isinstance(days, (int, float)) else "—"


def _cost_label(idea):
    """F07 对比卡「起步成本」：与存档行同口径（min_capital + 国家币种），避免同概念两个数。"""
    card = _idea_card(idea)
    if card.get("min_capital"):
        return card["min_capital"]
    return "—"


def compare_ideas(payload):
    """F07 步骤 4/5：只返三项（起步成本 / 每周时间 / 回本天数）+ 标题，不返评分/权重。

    PM 2026-11-13：键改为稳定 id（cost/hours/payback），展示文案由前端 locales 负责
    （中文包对比页不再露出英文行名）；title 仍是标题数据（前端已过滤不进行）。
    """
    ids = payload.get("ids") if isinstance(payload, dict) else None
    if not isinstance(ids, list) or len(ids) < 2:
        return None, {"code": "E_BAD_REQUEST", "message": "ids needs 2 items", "recoverable": True}
    sides = {}
    for side, idea_id in (("left", ids[0]), ("right", ids[1])):
        idea = find_idea(idea_id)
        if idea is None:
            return None, {"code": "E_IDEA_NOT_FOUND", "message": str(idea_id), "recoverable": True}
        sides[side] = {
            "title": idea.get("title") or idea_id,
            "cost": _cost_label(idea),
            "hours": _hours_label(idea),
            "payback": _payback_label(idea),
        }
    return sides, None


def remember_export_dir(path):
    """F-10：导出成功后记住目录（下次默认带上；设置页可改）。非 §2.4 cmd，内部调用。"""
    if not isinstance(path, str) or not path.strip():
        return
    directory = path if os.path.isdir(path) else os.path.dirname(path)
    if not directory:
        return
    st = load_state()
    st["export_dir"] = directory
    st["settings"] = settings_mod.apply_patch(st["settings"], {"export_dir": directory})
    save_state(st)
