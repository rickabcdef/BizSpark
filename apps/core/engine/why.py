# -*- coding: utf-8 -*-
"""engine.why — C-06 Why 文案（6 组模板池）+ 3 个标签（用例 T-16 / T-17）

规则（§F03 步骤 6 / §3.3）：
- why 必须引用答案里的具体词（资金档 / 时间 / 资产 / 国家名）
- 模板池按命中维度分 6 组
- **禁止**出现 algorithm / AI / score / recommended by / based on intelligent 等词
- tags 恰好 3 个：起步成本 / 时间 / 线上或本地（或复购）
"""

from .quiz import CAPITAL_LABELS, HOURS_LABELS, COUNTRY_NAMES, ASSET_NAMES  # noqa: F401（英文缺省路径仍被 answer_labels 引用）
from . import zhpack

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
    """生成一句 why。模板 + 答案具体词；触发禁词则回退到安全模板（防御性）。

    PM 2026-11-13：locale 感知——BIZSPARK_LOCALE=zh-CN 时走 zhpack 的中文模板池与标签，
    缺省行为与原实现完全一致（英文）。
    """
    cap_map, hrs_map, cty_map, ast_map, pools, safe_fb = zhpack.answer_labels()
    zh = zhpack.is_zh()
    ctx = {
        "capital": cap_map.get(answers.get("capital", "<500"), "500 美元以内" if zh else "a small budget"),
        "hours": hrs_map.get(answers.get("hours", "<10"), "每周几小时" if zh else "a few hours a week"),
        "country": cty_map.get(answers.get("country", "US"), "本地" if zh else "your area"),
        "assets_list": ("、".join(ast_map.get(a, a) for a in answers.get("assets", [])) if zh
                        else ", ".join(ast_map.get(a, a) for a in answers.get("assets", [])))
                       or ("你已有的资源" if zh else "what you already have"),
        "payback_days": str(idea.get("payback_days", 60)),
    }
    pool = pools.get(pick_pool(idea, dim_scores), pools["general"])
    for tpl in pool:
        text = tpl.format(**ctx)
        if not _contains_forbidden(text):
            return text
    return safe_fb.format(**ctx)


def build_tags(idea):
    """tags 恰好 3 个：起步成本 / 时间 / 线上或本地（复购型则给复购标签）。

    PM 2026-11-13：zh 包标签走中文（金额数字不变；en 缺省行为不变）。
    """
    zh = zhpack.is_zh()
    cap = idea.get("min_capital")
    # 内容数据：起步成本标签（来自 D 的库数据，运行期拼装，非源码硬编码售价）
    if isinstance(cap, (int, float)) and cap > 0:
        cap_tag = ("起步 " + str(int(cap))) if zh else ("From " + str(int(cap)))
    else:
        cap_tag = "起步成本低" if zh else "Low startup cost"
    h = idea.get("hours_per_week")
    time_tag = {"<10": "每周 <10 小时", "10-25": "每周 10–25 小时", "full": "全职"}.get(h, "时间灵活") if zh \
        else {"<10": "<10 h/wk", "10-25": "10–25 h/wk", "full": "Full-time"}.get(h, "Flexible hours")
    if idea.get("recurring") is True:
        third = "按月回头" if zh else "Monthly repeat"
    else:
        third = ({"online": "线上", "offline": "本地", "hybrid": "线上+本地"}.get(
            idea.get("online_or_offline"), "线上") if zh
            else {"online": "Online", "offline": "Local", "hybrid": "Online + local"}.get(
                idea.get("online_or_offline"), "Online"))
    return [cap_tag, time_tag, third]
