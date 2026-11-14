# -*- coding: utf-8 -*-
"""engine — BizSpark 本地诊断引擎包（负责人：C）

对外只暴露两个 handler（经 main.py 注册到 §2.4 命令表）：
- diagnose(payload)      → DiagnoseResult（§3.3）
- get_idea(payload)      → IdeaDetail（§3.4，交 E/B 渲染）

铁律：全程不联网、不暴露权重、输出 ≤3 条、绝不返回空数组、不写用户数据到日志。
"""

import json
import os
import re

from .quiz import validate_answers
from .filter import hard_filter, relax_hours
from . import score as score_mod
from .score import SEEN_FACTOR, match_pct
from .why import build_why, build_tags
from . import zhpack
from . import money as _money
from . import detail as detail_mod

DEGRADE_NOTE = "Try a slightly bigger budget next time."


def answers_country():
    """当前答案里的国家（state.last_answers.country）；无答案回退 None。

    PM 2026-11-14：get_idea / export_plan 的货币口径要跟问卷所选国家走
    （老板反馈：选加拿大后详情/PDF 仍是 USD）。懒导入 state 避免循环
    （state.store 反向依赖 engine.zhpack）。
    """
    try:
        from state import store as _store  # 局部导入避免环
        st = _store.load_state()
        la = st.get("last_answers") if isinstance(st, dict) else None
        c = la.get("country") if isinstance(la, dict) else None
        return str(c).upper() if isinstance(c, str) and c.strip() else None
    except Exception:
        return None

# ---- C-09 库加载与整库损坏回退链（T-38）：current.json → baseline 只读副本 → fallback_ideas.json ----

_CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # apps/core
_DATA_DIR = os.path.join(_CORE_DIR, "data")

FALLBACK_CHAIN = [
    os.environ.get("BIZSPARK_LIBRARY_CURRENT", ""),          # F 维护的合并工作库（env 注入路径）
    os.environ.get("BIZSPARK_BASELINE_PATH", ""),            # 安装包内置只读副本（A 打包 resources/）
    os.path.join(_DATA_DIR, "baseline_v1.json"),             # 开发期仓库内 baseline
    os.path.join(_DATA_DIR, "fallback_ideas.json"),          # D 预置最小兜底 3 条
]


def _extract_ideas(obj):
    """库文件可能是数组或 {"ideas": [...]} / {"version":..,"ideas":[...]}。"""
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        ideas = obj.get("ideas")
        if isinstance(ideas, list):
            return ideas
    return None


def _quick_validate(idea):
    """运行期轻量快检（F03 步骤 1：只查 status/关键枚举），失败条目跳过不中断。"""
    if not isinstance(idea, dict) or not isinstance(idea.get("id"), str) or not idea.get("id"):
        return False
    if idea.get("status", "active") not in ("active", "retired"):
        return False
    if idea.get("capital_tier") not in ("<500", "500-2k", "2k-10k", "10k+"):
        return False
    if idea.get("hours_per_week") not in ("<10", "10-25", "full"):
        return False
    return True


def load_library(paths=None):
    """按回退链加载库。返回 (ideas: list, source: str)。

    - 逐条快检，非法条目跳过；全坏视同该文件损坏，尝试下一级
    - 全链失败 → 返回空并在 diagnose 内走内置最后兜底
    """
    for p in (paths or FALLBACK_CHAIN):
        if not p:
            continue
        try:
            with open(p, encoding="utf-8") as f:
                ideas = _extract_ideas(json.load(f))
        except (OSError, ValueError):
            continue
        if ideas is None:
            continue
        good = [i for i in ideas if _quick_validate(i)]
        if good:
            return good, os.path.basename(p)
    return [], "none"


def _dim_scores(idea, answers):
    """供 why 选池用的分维得分。"""
    return {
        "capital": score_mod._capital_score(idea, answers),
        "skills_resources": score_mod._skills_assets_score(idea, answers),
        "time": score_mod._time_score(idea, answers),
        "risk": score_mod._risk_score(idea, answers),
        "payback": score_mod._payback_score(idea),
        "channel": score_mod._channel_score(idea, answers),
        "trend": score_mod._trend_score(idea),
        "recurring": score_mod._recurring_score(idea),
    }


def _to_card(idea, total, answers):
    """§3.3 卡片对象 + B 兼容别名 summary（Results.vue 消费）。

    PM 2026-11-13：zh 包对标题/简介做内容覆盖（zhpack，缺项回退英文）。
    PM 2026-11-14：卡片 why / tags 的金额随所选国家货币本地化（老板反馈）。
    """
    shown = zhpack.overlay(idea)
    cur = _money.currency_for(answers.get("country") if isinstance(answers, dict) else None)
    fx = _money.load_fx()
    return {
        "rank": 0,  # 输出前回填
        "id": shown.get("id"),
        "title": shown.get("title"),
        "one_liner": shown.get("one_liner"),
        "summary": shown.get("one_liner"),  # B 兼容别名（契约字段仍是 one_liner）
        "match_pct": match_pct(total),
        "why": build_why(idea, answers, _dim_scores(idea, answers), currency=cur, fx=fx),
        "tags": build_tags(idea, currency=cur, fx=fx),
    }


def diagnose(payload, library=None):
    """诊断管线（§F03 步骤 1–9，顺序不得调换）。payload 可含 saved_ids（F 注入 state.saved）。"""
    answers, _fell_back = validate_answers(payload)
    saved_ids = set()
    raw_saved = payload.get("saved_ids") or payload.get("saved") or []
    if isinstance(raw_saved, list):
        saved_ids = {x for x in raw_saved if isinstance(x, str)}

    ideas, source = load_library() if library is None else (library, "provided")

    checked = len(ideas)
    degraded = False
    degrade_note = None
    relaxed = False

    kept, _sat = hard_filter(ideas, answers)
    if len(kept) < 3:  # 步骤 8：只放宽时间档一次
        relaxed_answers = relax_hours(answers)
        if relaxed_answers is not None:
            kept2, _sat2 = hard_filter(ideas, relaxed_answers)
            if len(kept2) > len(kept):
                kept, relaxed = kept2, True

    if len(kept) < 3:
        degraded = True
        degrade_note = zhpack.DEGRADE_NOTE_ZH if zhpack.is_zh() else DEGRADE_NOTE
    if not kept:
        # 最后兜底：绝不返回空数组——对全部 active 条目绕过硬过滤打分取优
        kept = [(i, i.get("maturity") == "saturated") for i in ideas if i.get("status", "active") == "active"]
        if not kept:
            kept = [(i, False) for i in ideas]

    # 步骤 3–5：打分 → 已看降权 → 排序（三级 tiebreak，保证可重复）
    scored = [(score_mod.score_idea(i, answers) * (SEEN_FACTOR if i.get("id") in saved_ids else 1.0), i, sat)
              for i, sat in kept]
    scored = sorted(scored, key=lambda t: (-t[0],
                                           t[1].get("payback_days") if isinstance(t[1].get("payback_days"), (int, float)) else 10**9,
                                           str(t[1].get("id", ""))))

    # 步骤 6：克制输出 Top3；saturated 不进 Top3（可用条目不足除外）
    # PM 2026-11-14（老板反馈 bug）：库里同一门生意有多个地点变体（如擦玻璃 11 条），
    # 直接取前 3 会出现"3 个席位全是同一门生意换个地名"。
    # 修复：按业务簇（id 去掉尾部 -NNN）去重——Top3 必须来自 3 门不同的生意；
    # 簇内代表 = 该用户条件下得分最高的变体（排序天然保证）。打分本身不动。
    def _cluster_key(entry):
        return re.sub(r"-\d+$", "", str(entry.get("id", "")))

    def _diversify(candidates, limit):
        picked, seen = [], set()
        for item in candidates:
            key = _cluster_key(item[1])
            if key in seen:
                continue
            seen.add(key)
            picked.append(item)
            if len(picked) >= limit:
                break
        return picked

    non_sat = [t for t in scored if not t[2]]
    sat_only = [t for t in scored if t[2]]
    take = _diversify(non_sat, 3)
    if len(take) < 3:  # 可用条目不足时才允许 saturated 补位（仍遵守簇去重）
        taken_ids = {t[1].get("id") for t in take}
        take += _diversify([t for t in sat_only if t[1].get("id") not in taken_ids], 3 - len(take))
    top, top_filled = [], 0
    for _total, idea, _sat in take:
        card = _to_card(idea, _total, answers)
        top_filled += 1
        card["rank"] = top_filled
        top.append(card)

    # 步骤 9：统计
    filtered = checked - len(top)
    result = {
        "ideas": top,
        "checked": checked,
        "filtered": filtered,
        "degraded": degraded,
        "degrade_note": degrade_note,
        "_source": source,       # 内部调试用（前端可忽略）
        "_relaxed_hours": relaxed,
    }
    return result, None


def get_idea(payload):
    """C-10：get_idea(id) 装配（§3.4）——合并国家覆盖 + 3 个派生字段，交 E/B。

    PM 2026-11-14：country 缺省时回退问卷答案里的国家（货币口径全链路一致）。
    """
    idea_id = payload.get("id") if isinstance(payload, dict) else None
    if not idea_id:
        return None, {"code": "E_BAD_REQUEST", "message": "id is required", "recoverable": True}
    country = payload.get("country") if isinstance(payload.get("country"), str) else None
    if not country or not country.strip():
        country = answers_country()
    ideas, _src = load_library()
    found = next((i for i in ideas if i.get("id") == idea_id), None)
    if found is None:
        return None, {"code": "E_IDEA_NOT_FOUND", "message": str(idea_id), "recoverable": False}
    detail = detail_mod.assemble(found, country)
    return detail, None
