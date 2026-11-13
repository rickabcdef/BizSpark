# -*- coding: utf-8 -*-
"""content.build_baseline — D-03/D-04：312 条 baseline 确定性生成器（负责人：D）

输出：
- apps/core/data/baseline_v1.json（312 条，§5.1 分布精确命中）
- content/ideas/<slug>.json（26 行业分文件）
- content/distribution.csv（目标 vs 实际，偏差 ≤2%）

用法：python content/build_baseline.py（仓库根目录运行或任意目录，路径按仓库根解析）
确定性：固定随机种子，重复运行产物逐字节一致。
"""
import csv
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from industries import INDUSTRIES, COUNTRY_DATA, GROUP_COUNTS, GROUP_CODE  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, "apps", "core", "data")
IDEAS_DIR = os.path.join(REPO, "content", "ideas")

TIERS = ["<500", "500-2k", "2k-10k", "10k+"]
TIER_TARGET = [125, 100, 62, 25]
HOURS = ["<10", "10-25", "full"]
HOURS_TARGET = [140, 110, 62]
FORMS = ["online", "offline", "hybrid"]
FORM_TARGET = [140, 109, 63]
MATURITIES = ["emerging", "growing", "mature", "saturated"]
MATURITY_TARGET = [47, 109, 110, 46]
COUNTRY_TARGET = {"US": 297, "UK": 296, "CA": 262, "AU": 256, "SG": 200, "PH": 194}

# 每行业条数（合计=312）
PER_INDUSTRY = {"review-reply": 11, "home-cleaning": 11, "pet-care": 11, "lawn-garden": 11,
                "mobile-car-wash": 11, "errand-runner": 11, "window-cleaning": 11,
                "appliance-tuneup": 10, "product-photo": 13, "resume-polish": 13,
                "ebook-formatting": 13, "calendar-va": 12, "transcription-local": 12,
                "online-tutoring": 12, "invoice-chasing": 12, "google-maps-setup": 11,
                "simple-bookkeeping": 11, "quote-templates": 11, "inbox-tidy": 11,
                "template-packs": 11, "neighbourhood-newsletter": 11, "local-guide-pdf": 11,
                "stock-photo-local": 11, "market-stall": 16, "repair-corner": 15,
                "ai-agent-setup-local": 19}
assert sum(PER_INDUSTRY.values()) == 312
assert sum(GROUP_COUNTS.values()) == 312

# 每行业的维度偏好（最大余数法保证全局精确命中目标）
TIER_W = {"svc": [.55, .35, .10, 0], "onl": [.40, .40, .20, 0], "b2b": [.20, .30, .30, .20],
          "cnt": [.30, .40, .30, 0], "hnd": [.80, .20, 0, 0], "agt": [.20, .40, .30, .10]}
HOURS_W = {"svc": [.25, .40, .35], "onl": [.60, .30, .10], "b2b": [.50, .35, .15],
           "cnt": [.50, .30, .20], "hnd": [.20, .45, .35], "agt": [.40, .40, .20]}
FORM_W = {"svc": [.10, .60, .30], "onl": [.80, .05, .15], "b2b": [.70, .10, .20],
          "cnt": [.85, 0, .15], "hnd": [.10, .80, .10], "agt": [.50, .10, .40]}
MAT_W = {"svc": [.10, .30, .40, .20], "onl": [.20, .40, .30, .10], "b2b": [.15, .35, .35, .15],
         "cnt": [.20, .40, .30, .10], "hnd": [.05, .20, .40, .35], "agt": [.30, .45, .20, .05]}

# 基线内 wave 微调：review-reply 前 6 条 ai-llm；agt 行业三种 ai wave 轮转
WAVE_OVERRIDE = {"review-reply": (6, "ai-llm")}
AGT_WAVES = ["ai-agent", "ai-llm", "bi-agent"]

# 资金档金额范围（USD）
TIER_RANGE = {"<500": (30, 480), "500-2k": (520, 1900), "2k-10k": (2100, 9000), "10k+": (10500, 18000)}
AREA_SUFFIX = ["", " (north)", " (east)", " (riverside)", " (old town)", " (hillside)",
               " (central)", " (bayside)", " (market)", " ( lakeside)".replace(" ", "")]
SLUG_SHORT = {"neighbourhood-newsletter": "nbhd-newsletter"}


def largest_remainder(total, weights):
    """按权重把 total 拆成整数份（最大余数法，和恰为 total）。"""
    s = sum(weights)
    raw = [w / s * total for w in weights]
    base = [int(x) for x in raw]
    rem = total - sum(base)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - base[i], reverse=True)
    for i in order[:rem]:
        base[i] += 1
    return base


def build_schedule():
    """生成 312 条 (industry, tier, hours, form, maturity) 调度，全局精确命中目标。"""
    rng = random.Random(20261113)
    entries = []
    for ind in INDUSTRIES:
        n = PER_INDUSTRY[ind["slug"]]
        g = ind["group"]
        for dim, weights, target in ((0, TIER_W[g], TIER_TARGET), (1, HOURS_W[g], HOURS_TARGET),
                                     (2, FORM_W[g], FORM_TARGET), (3, MAT_W[g], MATURITY_TARGET)):
            alloc = largest_remainder(n, weights)
            if dim == 0:
                tiers = [v for v, c in zip(TIERS, alloc) for _ in range(c)]
            elif dim == 1:
                hours = [v for v, c in zip(HOURS, alloc) for _ in range(c)]
            elif dim == 2:
                forms = [v for v, c in zip(FORMS, alloc) for _ in range(c)]
            else:
                mats = [v for v, c in zip(MATURITIES, alloc) for _ in range(c)]
        rng.shuffle(tiers); rng.shuffle(hours); rng.shuffle(forms); rng.shuffle(mats)
        for i in range(n):
            entries.append(dict(slug=ind["slug"], group=g, tier=tiers[i], hours=hours[i],
                                form=forms[i], maturity=mats[i]))
    # 全局校正：行业级最大余数合计与全局目标存在漂移，按行业权重约束逐条换值
    dims = {"tier": (TIERS, TIER_TARGET, TIER_W), "hours": (HOURS, HOURS_TARGET, HOURS_W),
            "form": (FORMS, FORM_TARGET, FORM_W), "maturity": (MATURITIES, MATURITY_TARGET, MAT_W)}
    for key, (values, target, weights) in dims.items():
        for v, t in zip(values, target):
            got = sum(1 for e in entries if e[key] == v)
            guard = 0
            while got != t and guard < 312:
                guard += 1
                if got > t:  # 该值过剩 → 找一条本值条目换成不足的值
                    other = next(u for u in values
                                 if sum(1 for e in entries if e[key] == u) <
                                 target[values.index(u)])
                    cand = next(e for e in entries
                                if e[key] == v and weights[e["group"]][values.index(other)] > 0)
                    cand[key] = other
                    got -= 1
                else:  # 该值不足 → 从过剩值借
                    other = next(u for u in values
                                 if sum(1 for e in entries if e[key] == u) >
                                 target[values.index(u)])
                    cand = next(e for e in entries
                                if e[key] == other and weights[e["group"]][values.index(v)] > 0)
                    cand[key] = v
                    got += 1
    # 全局精确命中（断言兜底）
    for key, target in (("tier", TIER_TARGET), ("hours", HOURS_TARGET),
                        ("form", FORM_TARGET), ("maturity", MATURITY_TARGET)):
        pool = {"tier": TIERS, "hours": HOURS, "form": FORMS, "maturity": MATURITIES}[key]
        for v, t in zip(pool, target):
            got = sum(1 for e in entries if e[key] == v)
            assert got == t, f"{key}={v}: got {got}, want {t}"
    return entries


def build_countries():
    """每国命中精确条数，随条目随机重叠（确定性种子）。"""
    rng = random.Random(20261114)
    flags = {}
    for c, t in COUNTRY_TARGET.items():
        lst = [True] * t + [False] * (312 - t)
        rng.shuffle(lst)
        flags[c] = lst
    return flags


def make_idea(ind, e, idx, country_flags, seq):
    """把一条调度实例化为完整 Idea（§3.2 全字段 + 6 国覆盖）。"""
    rng = random.Random(900000 + idx)
    p = ind["pricing"][idx % len(ind["pricing"])]
    cap_lo, cap_hi = TIER_RANGE[e["tier"]]
    capital = cap_lo + (idx * 97) % (cap_hi - cap_lo)
    capital = int(round(capital / 5.0)) * 5

    # 成本分项：占比 × capital，四舍五入，末项补齐使合计恰等于 min_capital（V-04 偏差 0%）
    costs, allocated = [], 0
    for j, (label, frac) in enumerate(ind["costs"]):
        if j == len(ind["costs"]) - 1:
            amount = capital - allocated
        else:
            amount = max(1, int(round(capital * frac)))
            amount = min(amount, capital - allocated - (len(ind["costs"]) - 1 - j))
            allocated += amount
        costs.append({"item": label, "amount": amount})
    allocated = sum(c["amount"] for c in costs)
    assert allocated == capital

    # 国家：精确命中各国条数
    countries = [c for c in ["US", "UK", "CA", "AU", "SG", "PH"] if country_flags[c][idx]] or ["US"]

    # first_customers：主条目用 US/UK 等主市场渠道池轮转
    main_pool = COUNTRY_DATA["US" if "US" in countries else countries[0]]["fc"]
    fc = [main_pool[(idx + k) % len(main_pool)] for k in range(4)]

    # wave
    wave = ind["wave"]
    if e["slug"] == "ai-agent-setup-local":
        wave = AGT_WAVES[idx % 3]
    else:
        cnt, ow = WAVE_OVERRIDE.get(e["slug"], (0, None))
        if ow and idx < cnt:
            wave = ow

    n_slot = [5, 10, 15, 20, 25, 30][idx % 6]
    steps = [s.format(n=n_slot, p=p) for s in ind["steps"]]
    title_base = ind["title"]
    suffix = AREA_SUFFIX[idx % len(AREA_SUFFIX)]
    title = title_base + suffix if len(title_base) + len(suffix) <= 48 else title_base

    # 6 国覆盖（币种 + 合规一句 + 本地化渠道名）
    overrides = {}
    for c in countries:
        cd = COUNTRY_DATA[c]
        fc_c = cd["fc"]
        overrides[c] = {"currency": cd["currency"], "compliance_note": cd["note"],
                        "first_customers": [fc_c[(idx + k) % len(fc_c)] for k in range(3)]}

    legal = []
    if "SG" in countries and idx % 40 == 7:
        legal = ["SG"]  # 少量政策示例条目

    first_seen = "2024-{:02d}".format(idx % 12 + 1) if idx % 3 else "2025-{:02d}".format(idx % 12 + 1)
    updated = "2026-{:02d}-01".format(idx % 11 + 1)

    return {
        "id": "bs-{}-{}-{:03d}".format(GROUP_CODE[e["group"]],
                                       SLUG_SHORT.get(e["slug"], e["slug"])[:20], seq),
        "title": title,
        "one_liner": ind["one_liner"],
        "min_capital": capital,
        "capital_tier": e["tier"],
        "hours_per_week": e["hours"],
        "countries": countries,
        "online_or_offline": e["form"],
        "legal_blocks": legal,
        "skills_needed": list(ind["skills"]),
        "assets_needed": list(ind["assets"]),
        "risk_level": ind["risk"],
        "payback_days": ind["payback"][idx % len(ind["payback"])],
        "recurring": ind["recurring"],
        "channel_ids": list(ind["channels"]),
        "cost_breakdown": costs,
        "steps": steps,
        "pricing_hint": p,
        "first_customers": fc,
        "pitfalls": list(ind["pitfalls"]),
        "compliance_note": COUNTRY_DATA["US" if "US" in countries else countries[0]]["note"],
        "wave": wave,
        "trend_tags": list(ind["trend_tags"]),
        "first_seen": first_seen,
        "maturity": e["maturity"],
        "version": 1,
        "updated_at": updated,
        "status": "active",
        "overrides": overrides,
    }


def main():
    schedule = build_schedule()
    flags = build_countries()
    by_ind = {ind["slug"]: ind for ind in INDUSTRIES}

    ideas, per_file = [], {ind["slug"]: [] for ind in INDUSTRIES}
    seq = 0
    for idx, e in enumerate(schedule):
        seq += 1
        idea = make_idea(by_ind[e["slug"]], e, idx, flags, seq)
        ideas.append(idea)
        per_file[e["slug"]].append(idea)

    # 全量自检：标题/一句话长度、7 步、每步 ≤60 字符、无 emoji、id 唯一
    ids = [i["id"] for i in ideas]
    assert len(set(ids)) == 312, "V-01 duplicate ids"
    for it in ideas:
        assert len(it["title"]) <= 48, (it["id"], len(it["title"]))
        assert len(it["one_liner"]) <= 110, (it["id"], len(it["one_liner"]))
        assert len(it["steps"]) == 7 and all(len(s) <= 60 for s in it["steps"]), it["id"]
        assert len(it["first_customers"]) >= 3
        assert it["id"] == it["id"].lower()

    # 写 baseline_v1.json
    baseline = {"version": "v1", "generated_at": "2026-11-13",
                "schema": "BizSpark Idea §3.2 / V2.0", "count": len(ideas), "ideas": ideas}
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "baseline_v1.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(baseline, f, ensure_ascii=False, indent=1)

    # 写 26 行业分文件
    os.makedirs(IDEAS_DIR, exist_ok=True)
    for slug, items in per_file.items():
        with open(os.path.join(IDEAS_DIR, slug + ".json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"industry": slug, "count": len(items), "ideas": items},
                      f, ensure_ascii=False, indent=1)

    # 写 distribution.csv（目标 vs 实际）
    def count(key, values):
        return [sum(1 for i in ideas if i[key] == v) for v in values]

    rows = [["dimension", "category", "target", "target_pct", "actual", "actual_pct", "deviation_pp"]]
    slug_group = {ind["slug"]: ind["group"] for ind in INDUSTRIES}

    def emit(dim, pairs, actual_fn):
        total = sum(t for _, t in pairs)
        for cat, t in pairs:
            a = actual_fn(cat)
            rows.append([dim, cat, t, "{:.1f}".format(t / total * 100), a,
                         "{:.1f}".format(a / total * 100),
                         "{:+.1f}".format(a / total * 100 - t / total * 100)])

    group_actual = {}
    for slug, items in per_file.items():
        group_actual[slug_group[slug]] = group_actual.get(slug_group[slug], 0) + len(items)
    emit("group", [(g, c) for g, c in GROUP_COUNTS.items()], lambda g: group_actual.get(g, 0))
    emit("capital_tier", list(zip(TIERS, TIER_TARGET)),
         lambda v: sum(1 for i in ideas if i["capital_tier"] == v))
    emit("hours_per_week", list(zip(HOURS, HOURS_TARGET)),
         lambda v: sum(1 for i in ideas if i["hours_per_week"] == v))
    emit("online_or_offline", list(zip(FORMS, FORM_TARGET)),
         lambda v: sum(1 for i in ideas if i["online_or_offline"] == v))
    emit("maturity", list(zip(MATURITIES, MATURITY_TARGET)),
         lambda v: sum(1 for i in ideas if i["maturity"] == v))
    emit("countries", [(c, t) for c, t in COUNTRY_TARGET.items()],
         lambda c: sum(1 for i in ideas if c in i["countries"]))
    emit("wave", [("local-service/mobile-internet/digital-product", 219), ("ai-*", 37)],
         lambda v: (sum(1 for i in ideas if i["wave"] in ("local-service", "mobile-internet", "digital-product"))
                    if v.startswith("local") else sum(1 for i in ideas if i["wave"].startswith("ai-"))))
    with open(os.path.join(REPO, "content", "distribution.csv"), "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)

    # 汇总打印
    print(f"baseline: {len(ideas)} ideas -> {os.path.relpath(os.path.join(DATA_DIR,'baseline_v1.json'), REPO)}")
    ai = sum(1 for i in ideas if i["wave"].startswith("ai-"))
    sat = sum(1 for i in ideas if i["maturity"] == "saturated")
    print(f"ai-* waves: {ai}/312 = {ai/312*100:.1f}% (<=12%) | saturated: {sat}/312 = {sat/312*100:.1f}% (<=15%)")
    for c, t in COUNTRY_TARGET.items():
        got = sum(1 for i in ideas if c in i["countries"])
        print(f"  {c}: {got} ({got/312*100:.0f}%) target {t/312*100:.0f}%")


if __name__ == "__main__":
    main()
