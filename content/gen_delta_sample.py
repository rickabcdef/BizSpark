# -*- coding: utf-8 -*-
"""content.gen_delta_sample — D-09：首月 delta 样例生产（负责人：D，§5.5 SOP）

产出片段：hosting/_adds_2026-12.json（14 条 bi-agent 新商机）+ _revises_2026-12.json（5 条白名单 revise）
随后用 library.delta_tool 组装 hosting/delta_2026-12.json（retire 1 条在 delta_tool 命令行给出）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from industries import INDUSTRIES, COUNTRY_DATA  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTING = os.path.join(ROOT, "hosting")
AGT = next(i for i in INDUSTRIES if i["slug"] == "ai-agent-setup-local")
COUNTRIES6 = ["US", "UK", "CA", "AU", "SG", "PH"]
TIER_RANGE = {"<500": (30, 480), "500-2k": (520, 1900), "2k-10k": (2100, 9000), "10k+": (10500, 18000)}
TIERS = ["<500", "500-2k", "2k-10k", "10k+"]
HOURS = ["<10", "10-25", "full"]

# 14 条 bi-agent：预约/报价/表单/归档等智能体场景（AI 合计占比合并后 39/326≈12.0% 之内）
VARIANTS = [
    ("booking", "Booking-bot for salons and barbers", "$390 setup + $49/month"),
    ("quote", "Quote-bot for trades on the go", "$340 setup + $39/month"),
    ("faq", "FAQ-bot for dental and physio clinics", "$420 setup + $59/month"),
    ("intake", "Client intake form agent for law offices", "$460 setup + $69/month"),
    ("roster", "Staff roster agent for small cafés", "$300 setup + $35/month"),
    ("lead", "Lead-reply agent for landscapers", "$360 setup + $45/month"),
    ("invoice", "Invoice reminder agent for tutors", "$280 setup + $29/month"),
    ("stock", "Parts-stock alert agent for garages", "$480 setup + $59/month"),
    ("review", "Review-request agent for cleaners", "$320 setup + $39/month"),
    ("menu", "Menu-update agent for food trucks", "$260 setup + $25/month"),
    ("cb", "Callback scheduler for plumbers", "$410 setup + $55/month"),
    ("archive", "Job-photo archive agent for builders", "$440 setup + $49/month"),
    ("shift", "Shift-swap agent for care teams", "$370 setup + $49/month"),
    ("order", "Takeaway order-taking agent for bistros", "$450 setup + $59/month"),
]
SLUG = {"booking": "booking", "quote": "quote", "faq": "faq", "intake": "intake", "roster": "roster",
        "lead": "lead", "invoice": "invoice", "stock": "stock", "review": "review", "menu": "menu",
        "cb": "callback", "archive": "archive", "shift": "shift", "order": "order"}


def make_add(i, variant):
    tag, title, pricing = variant
    rng_seed = 700000 + i
    tier = TIERS[i % 4]
    lo, hi = TIER_RANGE[tier]
    capital = int(round((lo + (i * 173) % (hi - lo)) / 5.0)) * 5
    costs, alloc = [], 0
    for j, (label, frac) in enumerate(AGT["costs"]):
        if j == len(AGT["costs"]) - 1:
            amount = capital - alloc
        else:
            amount = max(1, int(round(capital * frac)))
            amount = min(amount, capital - alloc - (len(AGT["costs"]) - 1 - j))
            alloc += amount
        costs.append({"item": label, "amount": amount})
    countries = [c for c in COUNTRIES6 if i % 7 != 5 or c != "AU"]  # 逐条略有差异
    main = "US" if "US" in countries else countries[0]
    fc = [COUNTRY_DATA[main]["fc"][(i + k) % 4] for k in range(4)]
    overrides = {c: {"currency": COUNTRY_DATA[c]["currency"],
                     "compliance_note": COUNTRY_DATA[c]["note"],
                     "first_customers": [COUNTRY_DATA[c]["fc"][(i + k) % len(COUNTRY_DATA[c]["fc"])]
                                          for k in range(3)]}
                 for c in countries}
    n = [5, 10, 15, 20][i % 4]
    return {
        "id": "bs-agt-{}-{:03d}".format(SLUG[tag], 312 + i),
        "title": title,
        "one_liner": AGT["one_liner"],
        "min_capital": capital, "capital_tier": tier,
        "hours_per_week": HOURS[i % 3],
        "countries": countries,
        "online_or_offline": ["hybrid", "online", "offline"][i % 3],
        "legal_blocks": [],
        "skills_needed": list(AGT["skills"]), "assets_needed": list(AGT["assets"]),
        "risk_level": AGT["risk"], "payback_days": AGT["payback"][i % 3],
        "recurring": True, "channel_ids": list(AGT["channels"]),
        "cost_breakdown": costs, "steps": [s.format(n=n, p=pricing) for s in AGT["steps"]],
        "pricing_hint": pricing, "first_customers": fc,
        "pitfalls": list(AGT["pitfalls"]),
        "compliance_note": COUNTRY_DATA[main]["note"],
        "wave": "bi-agent", "trend_tags": ["bi-agent", "local", "retainer", tag],
        "first_seen": "2026-12", "maturity": ["emerging", "growing"][i % 2],
        "version": 1, "updated_at": "2026-12-01", "status": "active",
        "overrides": overrides,
    }


def main():
    adds = [make_add(i, v) for i, v in enumerate(VARIANTS)]
    with open(os.path.join(HOSTING, "_adds_2026-12.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(adds, f, ensure_ascii=False, indent=1)

    revises = [
        # 过气条目只降 maturity（永不删除）+ version/updated_at 同步（白名单内）
        {"id": "bs-svc-review-reply-001", "maturity": "growing", "version": 2, "updated_at": "2026-12-01"},
        {"id": "bs-onl-product-photo-088", "pricing_hint": "$15 per product, 5 photos", "version": 2, "updated_at": "2026-12-01"},
        {"id": "bs-hnd-market-stall-263", "channel_ids": ["walk-in", "facebook", "local-groups", "whatsapp"],
         "version": 2, "updated_at": "2026-12-01"},
        {"id": "bs-b2b-google-maps-setup-175", "first_customers": ["Google Maps clinics with incomplete profiles",
                                                                    "Chamber of commerce newsletter",
                                                                    "Walk-in visits on quiet afternoons"],
         "version": 2, "updated_at": "2026-12-01"},
        {"id": "bs-cnt-template-packs-219", "compliance_note": "US: check sales-tax rules for digital goods.",
         "version": 2, "updated_at": "2026-12-01"},
    ]
    with open(os.path.join(HOSTING, "_revises_2026-12.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(revises, f, ensure_ascii=False, indent=1)
    print(f"adds: {len(adds)}, revises: {len(revises)} -> hosting/_*_2026-12.json")


if __name__ == "__main__":
    main()
