# -*- coding: utf-8 -*-
"""engine.quiz — C-02 问卷答案校验（§3.1 契约，用例 T-09）

规则（§3.1）：
- country/capital/hours/risk 必须命中枚举；assets 元素必须命中枚举
- 未知字段忽略不报错
- assets 非数组时按 [] 处理（不弹错）
- 非法值**静默回退**（F13：不弹窗、不报错），回退后引擎照常工作
"""

COUNTRIES = ["US", "CA", "UK", "AU", "SG", "PH"]
CAPITAL_TIERS = ["<500", "500-2k", "2k-10k", "10k+"]
HOURS_TIERS = ["<10", "10-25", "full"]
ASSET_ENUM = ["car", "kitchen", "laptop", "design", "coding", "spare_room", "local_network"]
RISK_ENUM = ["no_impact", "small_loss", "can_absorb"]

# 内容数据：答案复述用标签（§3.1 题目表原文，非商品售价，T-59 边界同 locales）
CAPITAL_LABELS = {"<500": "under $500", "500-2k": "$500–$2,000", "2k-10k": "$2,000–$10,000", "10k+": "$10,000+"}
HOURS_LABELS = {"<10": "under 10 hours a week", "10-25": "10–25 hours a week", "full": "full-time hours"}
COUNTRY_NAMES = {"US": "the United States", "CA": "Canada", "UK": "the United Kingdom",
                 "AU": "Australia", "SG": "Singapore", "PH": "the Philippines"}
ASSET_NAMES = {"car": "a car", "kitchen": "a kitchen", "laptop": "a laptop", "design": "design skills",
               "coding": "basic coding", "spare_room": "a spare room", "local_network": "a local network"}
# 用户资产 → 隐含技能（§F03 步骤 3 "用户隐含技能"）
ASSET_SKILL_HINTS = {
    "design": ["design"], "coding": ["coding"], "kitchen": ["cooking"],
    "car": ["driving"], "spare_room": ["handyman"], "local_network": ["sales"],
    "laptop": ["writing", "basic_english"],
}


def _norm(value, enum, fallback):
    return value if isinstance(value, str) and value in enum else fallback


def validate_answers(payload):
    """校验并规范化 QuizAnswers。返回 (normalized: dict, fell_back: list[str])。

    - payload 可为答案本身，或 {"answers": {...}}（B 的 cmd.ts 包装格式），两者都接受
    - 非法值静默回退到最保守档位，绝不抛错（T-09）
    """
    if isinstance(payload, dict) and isinstance(payload.get("answers"), dict):
        payload = payload["answers"]
    if not isinstance(payload, dict):
        payload = {}

    fell_back = []
    country = _norm(payload.get("country"), COUNTRIES, "US")
    if country != payload.get("country"):
        fell_back.append("country")
    capital = _norm(payload.get("capital"), CAPITAL_TIERS, "<500")
    if capital != payload.get("capital"):
        fell_back.append("capital")
    hours = _norm(payload.get("hours"), HOURS_TIERS, "<10")
    if hours != payload.get("hours"):
        fell_back.append("hours")
    risk = _norm(payload.get("risk"), RISK_ENUM, "no_impact")
    if risk != payload.get("risk"):
        fell_back.append("risk")

    raw_assets = payload.get("assets")
    if not isinstance(raw_assets, list):  # 非数组按 [] 处理（§3.1，不弹错）
        if raw_assets is not None:
            fell_back.append("assets")
        raw_assets = []
    assets = []
    for a in raw_assets:
        if isinstance(a, str) and a in ASSET_ENUM and a not in assets:
            assets.append(a)
        elif a not in (None, ""):
            fell_back.append("assets")

    normalized = {"country": country, "capital": capital, "hours": hours,
                  "assets": assets, "risk": risk}
    # 未知字段忽略不报错：不拷贝 payload 其他键
    return normalized, sorted(set(fell_back))
