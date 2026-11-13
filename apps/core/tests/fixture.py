# -*- coding: utf-8 -*-
"""tests.fixture — 312 条商机测试夹具（确定性生成，可重复）

遵循 §3.2 Idea 契约全字段；分布跨 4 个资金档 / 3 个时间档 / 6 国 / 6 wave / 4 maturity，
并固定混入 saturated、legal_blocks、retired、坏字段条目供 T-10/T-11/T-38 使用。
"""
import random

COUNTRIES = ["US", "CA", "UK", "AU", "SG", "PH"]
TIERS = ["<500", "500-2k", "2k-10k", "10k+"]
HOURS = ["<10", "10-25", "full"]
WAVES = ["mobile-internet", "ai-llm", "ai-agent", "bi-agent", "local-service", "digital-product"]
MATURITIES = ["emerging", "growing", "mature", "saturated"]
RISK_LEVELS = ["low", "medium", "high"]
CHANNELS = ["google-maps", "nextdoor", "thumbtack", "etsy", "shopify", "facebook",
            "whatsapp", "walk-in", "chamber", "referral", "local-groups"]
TIER_CAP = {"<500": 480, "500-2k": 1900, "2k-10k": 9000, "10k+": 15000}

WORDS = ["map", "clean", "bake", "repair", "walk", "tutor", "photo", "print", "plan", "sort"]
NOUNS = ["crew", "desk", "cart", "loop", "kit", "path", "list", "post", "note", "lane"]


def make_idea(i, total=312):
    """第 i 条商机（0-based）。确定性：不用全局随机状态以外的输入。"""
    rng = random.Random(20261113 + i * 7919)
    slug = "{}-{}-{}-{:03d}".format(
        "us", ["svc", "dig", "ret", "edu"][i % 4][: rng.choice([2, 3, 4])],
        WORDS[i % len(WORDS)] + NOUNS[(i // 3) % len(NOUNS)], (i % 1000))
    tier = TIERS[i % 4]
    hours = HOURS[(i // 4) % 3]
    wave = WAVES[i % 6]
    maturity = MATURITIES[i % 4]
    # 特殊条目（固定位置，供边界用例）
    if i == 5:
        maturity = "saturated"  # saturated 永不进 Top3（T-17）
        tier = "500-2k"         # 保证该条可通过 500-2k/<10 过滤，验证"标记不剔"
        hours = "<10"
    if i == 7:
        tier = "10k+"  # 高资金档
    if i == 11:
        hours = "full"
    status = "retired" if i % 53 == 52 else "active"  # 每 53 条 1 条 retired
    capital = 10 + (i * 37) % TIER_CAP[tier]
    countries = [COUNTRIES[k % 6] for k in range(i % 6 + 1)]
    legal = ["SG"] if i % 29 == 28 else []
    return {
        "id": slug,
        "title": "Test idea {} {}".format(WORDS[i % len(WORDS)], NOUNS[(i // 7) % len(NOUNS)]),
        "one_liner": "Local customers pay for test service {} — clear who pays and why.".format(i),
        "min_capital": capital,
        "capital_tier": tier,
        "hours_per_week": hours,
        "countries": countries,
        "online_or_offline": ["online", "offline", "hybrid"][i % 3],
        "legal_blocks": legal,
        "skills_needed": [["none"], ["writing"], ["design", "coding"], ["sales"]][i % 4],
        "assets_needed": [["none"], ["laptop"], ["car", "laptop"], ["kitchen"]][i % 4],
        "risk_level": RISK_LEVELS[i % 3],
        "payback_days": [7, 21, 45, 88, 150, 300][i % 6],
        "recurring": i % 2 == 0,
        "channel_ids": [CHANNELS[k % len(CHANNELS)] for k in range(i % 5 + 1)],
        "cost_breakdown": [{"item": "Tools", "amount": max(1, capital // 2)},
                           {"item": "Materials", "amount": max(1, capital - capital // 2)}],
        "steps": ["Step {} one".format(i), "Step two", "Step three", "Step four",
                  "Step five", "Step six", "Step seven"],
        "pricing_hint": "from {} per job".format(20 + i % 80),
        "first_customers": ["Google Maps shops", "Nextdoor posts", "Referrals from first client"],
        "pitfalls": ["Confirm fees before quoting", "Never skip the before photo", "Price the plan, not the hour"],
        "compliance_note": "Check local registration rules.",
        "wave": wave,
        "trend_tags": ["tag{}".format(i % 9)],
        "first_seen": "2025-{:02d}".format(i % 12 + 1),
        "maturity": maturity,
        "version": 1,
        "updated_at": "2026-11-01",
        "status": status,
    }


def make_library(total=312):
    """312 条全量夹具（确定性顺序）。"""
    return [make_idea(i, total) for i in range(total)]
