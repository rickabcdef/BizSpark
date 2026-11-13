# -*- coding: utf-8 -*-
"""engine.why — C-06 Why 文案（6 组模板池）+ 3 个标签（用例 T-16 / T-17）

规则（§F03 步骤 6 / §3.3）：
- why 必须引用答案里的具体词（资金档 / 时间 / 资产 / 国家名）
- 模板池按命中维度分 6 组
- **禁止**出现 algorithm / AI / score / recommended by / based on intelligent 等词
- tags 恰好 3 个：起步成本 / 时间 / 线上或本地（或复购）
"""

from .quiz import CAPITAL_LABELS, HOURS_LABELS, COUNTRY_NAMES, ASSET_NAMES

# 禁词守卫（大小写不敏感；why 文案绝不出现）
FORBIDDEN = ["algorithm", " ai ", "ai-", "score", "recommended by", "based on intelligent", "智能"]

# 6 组模板池：按命中维度取最强两维决定组别；占位符用答案具体词填充
WHY_POOLS = {
    "capital_time": [
        "Low money and {hours} — {capital} is all it takes to get going.",
        "Fits {capital} and {hours}: you can start without touching savings.",
        "Lean budget, light schedule — this one matches both at once.",
    ],
    "local_assets": [
        "You have {assets_list} and a fixed local area — the highest-margin match in your city.",
        "{assets_list} plus your local network is exactly what this one runs on.",
        "This works street-by-street, and {assets_list} is all the gear you need.",
    ],
    "payback": [
        "Most people covering costs within weeks — {payback_days} days here is realistic with {hours}.",
        "Quick payback: about {payback_days} days before this pays for itself.",
    ],
    "online_laptop": [
        "Runs online with {assets_list} and {hours} — start this week from your kitchen table.",
        "No shop, no stock: {assets_list} is enough to serve your first paying customers.",
    ],
    "recurring": [
        "Repeat monthly income — one client here tends to stay, which fits {hours} nicely.",
        "Clients come back every month, so the hours you put in keep paying off.",
    ],
    "general": [
        "Matches {capital}, {hours}, and what you already have ({assets_list}) in {country}.",
        "A straightforward fit for your budget and schedule in {country}.",
    ],
}
FORBIDDEN_SAFE_FALLBACK = "Fits {capital} and {hours} with what you already have in {country}."


def _contains_forbidden(text):
    t = " " + text.lower() + " "
    return any(f in t for f in FORBIDDEN)


def pick_pool(idea, dim_scores):
    """按命中维度选模板组：取权重贡献最高的维度映射到池。"""
    best = max(dim_scores.items(), key=lambda kv: kv[1])[0] if dim_scores else "general"
    return {
        "capital": "capital_time", "time": "capital_time",
        "skills_resources": "local_assets", "channel": "local_assets",
        "payback": "payback", "risk": "payback",
        "trend": "online_laptop", "recurring": "recurring",
    }.get(best, "general")


def build_why(idea, answers, dim_scores):
    """生成一句 why。模板 + 答案具体词；触发禁词则回退到安全模板（防御性）。"""
    ctx = {
        "capital": CAPITAL_LABELS.get(answers.get("capital", "<500"), "a small budget"),
        "hours": HOURS_LABELS.get(answers.get("hours", "<10"), "a few hours a week"),
        "country": COUNTRY_NAMES.get(answers.get("country", "US"), "your area"),
        "assets_list": ", ".join(ASSET_NAMES.get(a, a) for a in answers.get("assets", [])) or "what you already have",
        "payback_days": str(idea.get("payback_days", 60)),
    }
    pool = WHY_POOLS.get(pick_pool(idea, dim_scores), WHY_POOLS["general"])
    for tpl in pool:
        text = tpl.format(**ctx)
        if not _contains_forbidden(text):
            return text
    return FORBIDDEN_SAFE_FALLBACK.format(**ctx)


def build_tags(idea):
    """tags 恰好 3 个：起步成本 / 时间 / 线上或本地（复购型则给复购标签）。"""
    cap = idea.get("min_capital")
    # 内容数据：起步成本标签（来自 D 的库数据，运行期拼装，非源码硬编码售价）
    cap_tag = ("From " + str(int(cap))) if isinstance(cap, (int, float)) and cap > 0 else "Low startup cost"
    h = idea.get("hours_per_week")
    time_tag = {"<10": "<10 h/wk", "10-25": "10–25 h/wk", "full": "Full-time"}.get(h, "Flexible hours")
    if idea.get("recurring") is True:
        third = "Monthly repeat"
    else:
        third = {"online": "Online", "offline": "Local", "hybrid": "Online + local"}.get(
            idea.get("online_or_offline"), "Online")
    return [cap_tag, time_tag, third]
