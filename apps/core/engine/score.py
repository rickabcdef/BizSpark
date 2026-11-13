# -*- coding: utf-8 -*-
"""engine.score — C-04/C-05 八维打分 + 已看降权 + 排序 + match_pct（用例 T-12/T-13/T-14/T-15）

铁律：
- 权重写死为常量，不给用户调、不写进设置、不暴露给前端
- **趋势新鲜度锁死 5%**，禁止为追 AI 浪潮调高（V-08 从数据侧再兜一层）
- 排序三级 tiebreak 保证同答案重跑完全一致（可重复、可测试）
"""

from .quiz import ASSET_SKILL_HINTS

# 8 维权重（分派表写死）：资金20 / 技能资源20 / 时间15 / 风险15 / 回本10 / 渠道10 / 趋势5 / 复购5
WEIGHTS = {
    "capital": 0.20,
    "skills_resources": 0.20,
    "time": 0.15,
    "risk": 0.15,
    "payback": 0.10,
    "channel": 0.10,
    "trend": 0.05,   # 锁死，勿动（T-14 校验此常量）
    "recurring": 0.05,
}
SEEN_FACTOR = 0.85  # 已看降权（C-05 / T-15）

# 资金档区间（USD），打分用；10k+ 上界按两倍衰减终点
CAPITAL_RANGE = {"<500": (0, 500), "500-2k": (500, 2000),
                 "2k-10k": (2000, 10000), "10k+": (10000, 20000)}
# 时间/风险档的相邻距离分
_ADJ = {0: 1.0, 1: 0.6, 2: 0.3}
RISK_MAP = {"no_impact": "low", "small_loss": "medium", "can_absorb": "high"}
RISK_ORDER = ["low", "medium", "high"]
# wave 新旧序（1 旧 → 5 新）；maturity 加成
WAVE_RANK = {"mobile-internet": 1, "digital-product": 2, "local-service": 2,
             "ai-llm": 3, "ai-agent": 4, "bi-agent": 5}
MATURITY_FACTOR = {"emerging": 1.0, "growing": 0.9, "mature": 0.5, "saturated": 0.0}
# 渠道按国家可得性（D 的渠道数据到位前的内部近似；仅用于打分，不展示）
CHANNELS_BY_COUNTRY = {
    "US": {"google-maps", "nextdoor", "thumbtack", "etsy", "shopify", "facebook", "referral", "local-groups", "chamber", "walk-in"},
    "CA": {"google-maps", "nextdoor", "etsy", "shopify", "facebook", "referral", "local-groups", "walk-in"},
    "UK": {"google-maps", "thumbtack", "etsy", "shopify", "facebook", "whatsapp", "referral", "local-groups", "walk-in"},
    "AU": {"google-maps", "nextdoor", "etsy", "shopify", "facebook", "referral", "local-groups", "walk-in"},
    "SG": {"google-maps", "shopify", "facebook", "whatsapp", "referral", "local-groups", "walk-in", "chamber"},
    "PH": {"google-maps", "etsy", "shopify", "facebook", "whatsapp", "referral", "local-groups", "walk-in"},
}


def _capital_score(idea, answers):
    """资金贴合度：min_capital 落在该档内得满分，越界线性衰减；低于档位下限视为轻松负担（满分）。"""
    tier = answers.get("capital", "<500")
    lo, hi = CAPITAL_RANGE.get(tier, (0, 500))
    cap = idea.get("min_capital")
    if not isinstance(cap, (int, float)) or cap < 0:
        return 0.0
    if cap <= hi:
        return 1.0
    # 越界向上线性衰减：hi → 1.0，2×hi → 0.0
    return max(0.0, 1.0 - (cap - hi) / float(hi - lo + 1 or 1) / 1.0) if cap < 2 * hi else 0.0


def _skills_assets_score(idea, answers):
    """技能/资源匹配：skills_needed ∩ 用户隐含技能 与 assets_needed ∩ assets 的均值；none/空视为全匹配。"""
    user_skills = set()
    for a in answers.get("assets", []):
        user_skills.update(ASSET_SKILL_HINTS.get(a, []))
    user_assets = set(answers.get("assets", []))

    skills = idea.get("skills_needed") or []
    if not isinstance(skills, list) or not skills or "none" in skills:
        s = 1.0
    else:
        s = len([x for x in skills if x in user_skills]) / float(len(skills))
    assets = idea.get("assets_needed") or []
    if not isinstance(assets, list) or not assets or "none" in assets:
        a = 1.0
    else:
        a = len([x for x in assets if x in user_assets]) / float(len(assets))
    return (s + a) / 2.0


def _time_score(idea, answers):
    order = HOURS_ORDER
    h = idea.get("hours_per_week")
    if h not in order:
        return 0.0
    return _ADJ.get(abs(order.index(h) - order.index(answers.get("hours", "<10"))), 0.3)


HOURS_ORDER = ["<10", "10-25", "full"]


def _risk_score(idea, answers):
    user_level = RISK_MAP.get(answers.get("risk", "no_impact"), "low")
    lv = idea.get("risk_level")
    if lv not in RISK_ORDER:
        return 0.0
    d = abs(RISK_ORDER.index(lv) - RISK_ORDER.index(user_level))
    return 1.0 if d == 0 else (0.6 if d == 1 else 0.3)


def _payback_score(idea):
    d = idea.get("payback_days")
    if not isinstance(d, (int, float)) or d < 1:
        return 0.0
    if d <= 30:
        return 1.0
    if d <= 90:
        return 0.7
    if d <= 180:
        return 0.4
    return 0.2


def _channel_score(idea, answers):
    chans = idea.get("channel_ids") or []
    if not isinstance(chans, list) or not chans:
        return 0.0
    avail = CHANNELS_BY_COUNTRY.get(answers.get("country", "US"), set())
    return len([c for c in chans if c in avail]) / float(len(chans))


def _trend_score(idea):
    """趋势新鲜度（权重锁死 5%）：wave 越新越高；maturity emerging/growing 加分，mature 减半，saturated 记 0。"""
    wave = WAVE_RANK.get(idea.get("wave"), 1) / 5.0
    mat = MATURITY_FACTOR.get(idea.get("maturity", "mature"), 0.5)
    return wave * 0.5 + wave * mat * 0.5


def _recurring_score(idea):
    return 1.0 if idea.get("recurring") is True else 0.5


def score_idea(idea, answers):
    """返回 0–1 的总分（未乘已看降权）。"""
    parts = {
        "capital": _capital_score(idea, answers),
        "skills_resources": _skills_assets_score(idea, answers),
        "time": _time_score(idea, answers),
        "risk": _risk_score(idea, answers),
        "payback": _payback_score(idea),
        "channel": _channel_score(idea, answers),
        "trend": _trend_score(idea),
        "recurring": _recurring_score(idea),
    }
    return sum(parts[k] * WEIGHTS[k] for k in WEIGHTS)


def rank_ideas(scored):
    """排序：总分降序 → payback_days 升序 → id 字典序（保证可重复，T-15）。"""
    return sorted(scored, key=lambda t: (-t[0], t[1].get("payback_days") if isinstance(t[1].get("payback_days"), (int, float)) else 10**9, str(t[1].get("id", ""))))


def match_pct(total):
    """总分线性映射到 60–99 整数，仅展示用（不暴露权重）。"""
    return 60 + int(round(max(0.0, min(1.0, total)) * 39))
