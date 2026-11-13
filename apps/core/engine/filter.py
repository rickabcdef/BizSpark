# -*- coding: utf-8 -*-
"""engine.filter — C-03 硬过滤（§F03 步骤 2，用例 T-10 / T-11）

规则：
- 资金档**向上兼容，不向下**：<500 只留 <500；500-2k 留 <500+500-2k；2k-10k 留前三档；10k+ 全部
- 时间档同样向上：<10 只留 <10；10-25 留 <10+10-25；full 全部
- countries 含所选国家，且 legal_blocks 不含该国
- status == active
- maturity == saturated → 标记但不剔除（排序阶段使用）
"""

from .quiz import CAPITAL_TIERS, HOURS_TIERS

# 资金档向上兼容映射：用户所选档 → 允许的 idea.capital_tier 集合
CAPITAL_ALLOWED = {
    "<500": {"<500"},
    "500-2k": {"<500", "500-2k"},
    "2k-10k": {"<500", "500-2k", "2k-10k"},
    "10k+": {"<500", "500-2k", "2k-10k", "10k+"},
}
# 时间档向上兼容映射
HOURS_ALLOWED = {
    "<10": {"<10"},
    "10-25": {"<10", "10-25"},
    "full": {"<10", "10-25", "full"},
}
# 降级放宽时间档（只放宽一次，F03 步骤 8）
HOURS_RELAX_NEXT = {"<10": "10-25", "10-25": "full", "full": None}


def hard_filter(ideas, answers):
    """硬过滤。返回 (kept, saturated_count)。

    kept 元素为 (idea, is_saturated) 元组；saturated 标记不剔除。
    每条 idea 的缺失/非法字段按"不满足"处理（跳过该条，不中断）。
    """
    country = answers.get("country", "US")
    capital_ok = CAPITAL_ALLOWED.get(answers.get("capital"), CAPITAL_ALLOWED["<500"])
    hours_ok = HOURS_ALLOWED.get(answers.get("hours"), HOURS_ALLOWED["<10"])

    kept = []
    saturated = 0
    for idea in ideas:
        if not isinstance(idea, dict):
            continue
        if idea.get("status", "active") != "active":
            continue
        if idea.get("capital_tier") not in capital_ok:
            continue
        if idea.get("hours_per_week") not in hours_ok:
            continue
        countries = idea.get("countries")
        if not isinstance(countries, list) or country not in countries:
            continue
        legal_blocks = idea.get("legal_blocks") or []
        if isinstance(legal_blocks, list) and country in legal_blocks:
            continue
        if idea.get("maturity") == "saturated":
            kept.append((idea, True))
            saturated += 1
        else:
            kept.append((idea, False))
    return kept, saturated


def relax_hours(answers):
    """降级：时间档放宽一次。full 不再放宽，返回 None。"""
    nxt = HOURS_RELAX_NEXT.get(answers.get("hours"))
    if nxt is None:
        return None
    relaxed = dict(answers)
    relaxed["hours"] = nxt
    return relaxed
