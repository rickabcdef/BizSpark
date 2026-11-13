# -*- coding: utf-8 -*-
"""library.validate — D-02：V-01…V-12 校验规则（负责人：D，§3.8，CI 必跑）

用法：
  python apps/core/library/validate.py                # 校验 baseline + 分行业文件 + delta + locales
  python apps/core/library/validate.py file1.json ... # 校验指定文件

退出码：存在"构建失败"级问题 → 1；只有警告 → 0。
"""
import json
import os
import re
import sys

ID_RE = re.compile(r"^[a-z]{2}-[a-z]{2,4}-[a-z0-9-]{1,20}-\d{3}$")
COUNTRIES = ["US", "CA", "UK", "AU", "SG", "PH"]
CAPITAL_TIERS = ["<500", "500-2k", "2k-10k", "10k+"]
HOURS_TIERS = ["<10", "10-25", "full"]
WAVES = ["mobile-internet", "ai-llm", "ai-agent", "bi-agent", "local-service", "digital-product"]
MATURITIES = ["emerging", "growing", "mature", "saturated"]
STATUSES = ["active", "retired"]
SKILLS = ["writing", "basic_english", "design", "coding", "sales", "driving", "cooking", "handyman", "none"]
ASSETS = ["car", "kitchen", "laptop", "design", "coding", "spare_room", "local_network", "none"]
RISKS = ["low", "medium", "high"]
CHANNELS = ["google-maps", "nextdoor", "thumbtack", "etsy", "shopify", "facebook",
            "whatsapp", "walk-in", "chamber", "referral", "local-groups"]
AI_WAVES = ("ai-llm", "ai-agent", "bi-agent")  # §5.1：三者合计 ≤12%（V-08）
# V-09 空话黑名单（first_customers 禁止出现）
FC_FORBIDDEN = ["social media", "online promotion", "广告", "social networks", "the internet"]
# F09/§3.7 delta revise 白名单字段
REVISE_WHITELIST = {"maturity", "version", "updated_at", "first_customers", "pricing_hint",
                    "cost_breakdown", "status", "compliance_note", "pitfalls", "channel_ids"}
# §5.1 分布目标（V-12 用；group 按行业组归并）
DIST_TARGET = {
    "group": {"svc": 0.28, "onl": 0.24, "b2b": 0.18, "cnt": 0.14, "hnd": 0.10, "agt": 0.06},
    "capital_tier": {"<500": 0.40, "500-2k": 0.32, "2k-10k": 0.20, "10k+": 0.08},
    "maturity": {"emerging": 0.15, "growing": 0.35, "mature": 0.35, "saturated": 0.15},
}
REQUIRED_FIELDS = {
    "id": str, "title": str, "one_liner": str, "min_capital": (int, float),
    "capital_tier": str, "hours_per_week": str, "countries": list, "online_or_offline": str,
    "legal_blocks": list, "skills_needed": list, "assets_needed": list, "risk_level": str,
    "payback_days": (int, float), "recurring": bool, "channel_ids": list,
    "cost_breakdown": list, "steps": list, "pricing_hint": str, "first_customers": list,
    "pitfalls": list, "compliance_note": str, "wave": str, "trend_tags": list,
    "first_seen": str, "maturity": str, "version": (int, float), "updated_at": str,
    "status": str,
}


def _repo_root():
    p = os.path.dirname(os.path.abspath(__file__))
    while p != os.path.dirname(p):
        if os.path.isdir(os.path.join(p, "apps", "core")):
            return p
        p = os.path.dirname(p)
    return os.getcwd()


def validate_idea(idea, errors, warnings, ctx=""):
    """单条 Idea 校验（V-02…V-05 + V-09 内容项）。"""
    tag = f"{ctx}:{idea.get('id', '?')}" if ctx else idea.get("id", "?")
    # V-02 必填字段与类型
    for f, t in REQUIRED_FIELDS.items():
        if f not in idea:
            errors.append(f"[V-02] {tag} missing field {f}")
        elif not isinstance(idea[f], t) or (t is not bool and isinstance(idea[f], bool) and t is not bool):
            errors.append(f"[V-02] {tag} field {f} wrong type, want {t}")
    # V-03 结构数量
    steps = idea.get("steps") or []
    if len(steps) != 7:
        errors.append(f"[V-03] {tag} steps must be exactly 7, got {len(steps)}")
    for s in steps:
        if not isinstance(s, str) or not s or len(s) > 60:
            errors.append(f"[V-03] {tag} step too long/empty (>60 chars)")
            break
    if len(idea.get("pitfalls") or []) != 3:
        errors.append(f"[V-03] {tag} pitfalls must be exactly 3")
    if len(idea.get("first_customers") or []) < 3:
        errors.append(f"[V-03] {tag} first_customers must be >=3")
    # V-04 成本合计偏差 ≤15%
    cap = idea.get("min_capital")
    costs = [c.get("amount") for c in (idea.get("cost_breakdown") or []) if isinstance(c, dict)]
    if isinstance(cap, (int, float)) and costs and all(isinstance(a, (int, float)) for a in costs):
        dev = abs(sum(costs) - cap) / max(cap, 1)
        if dev > 0.15:
            errors.append(f"[V-04] {tag} cost sum deviates {dev*100:.0f}% from min_capital")
    # V-05 枚举
    for f, enum in (("capital_tier", CAPITAL_TIERS), ("hours_per_week", HOURS_TIERS),
                    ("wave", WAVES), ("maturity", MATURITIES), ("status", STATUSES),
                    ("risk_level", RISKS), ("online_or_offline", ["online", "offline", "hybrid"])):
        if idea.get(f) not in enum:
            errors.append(f"[V-05] {tag} {f}={idea.get(f)!r} not in enum")
    for f, enum in (("skills_needed", SKILLS), ("assets_needed", ASSETS), ("channel_ids", CHANNELS)):
        for v in (idea.get(f) or []):
            if v not in enum:
                errors.append(f"[V-05] {tag} {f} item {v!r} not in enum")
    for c in (idea.get("countries") or []):
        if c not in COUNTRIES:
            errors.append(f"[V-05] {tag} countries item {c!r} not in enum")
    # V-06 覆盖可回退（警告级）：无任何 overrides 且多国 → 提示
    if len(idea.get("countries") or []) > 1 and not idea.get("overrides"):
        warnings.append(f"[V-06] {tag} multi-country entry has no CountryOverride (falls back to main)")
    # V-09 first_customers 空话拦截（构建失败级）
    for fc in (idea.get("first_customers") or []):
        low = str(fc).lower()
        for bad in FC_FORBIDDEN:
            if bad in low or bad in str(fc):
                errors.append(f"[V-09] {tag} first_customers contains empty phrase: {fc!r}")


def validate_library(ideas, errors, warnings, ctx="", share_checks=True):
    """库级校验（V-01 唯一性 + 逐条）。share_checks=False 时跳过 V-07/V-08（用于单行业分文件等子集）。"""
    ids = [i.get("id") for i in ideas if isinstance(i, dict)]
    if len(set(ids)) != len(ids):
        errors.append("[V-01] duplicate ids found")
    for i in ideas:
        if isinstance(i, dict):
            validate_idea(i, errors, warnings, ctx)
        else:
            errors.append(f"[V-02] {ctx} non-object entry in ideas")
    if not share_checks:
        return
    n = len(ideas) or 1
    sat = sum(1 for i in ideas if isinstance(i, dict) and i.get("maturity") == "saturated")
    if sat / n > 0.20:
        warnings.append(f"[V-07] saturated {sat}/{n} = {sat/n*100:.0f}% > 20%")
    ai = sum(1 for i in ideas if isinstance(i, dict) and i.get("wave") in AI_WAVES)
    if ai / n > 0.12:
        warnings.append(f"[V-08] ai-* waves {ai}/{n} = {ai/n*100:.0f}% > 12%")


def check_v10(locales_dir, errors):
    """V-10：zh-CN 与 en-US 键集合一致（构建失败级）。"""
    en_p = os.path.join(locales_dir, "en-US.json")
    zh_p = os.path.join(locales_dir, "zh-CN.json")
    try:
        en = set(json.load(open(en_p, encoding="utf-8")).keys())
        zh = set(json.load(open(zh_p, encoding="utf-8")).keys())
    except (OSError, ValueError) as e:
        errors.append(f"[V-10] locales unreadable: {e}")
        return
    if en != zh:
        errors.append(f"[V-10] locale key mismatch: en-only={sorted(en - zh)[:5]} zh-only={sorted(zh - en)[:5]}")


def check_v12(ideas, errors, warnings):
    """V-12：合并后分布与 §5.1/§5.2 对比（警告级，±2pp）。"""
    n = len(ideas) or 1
    for dim, targets in DIST_TARGET.items():
        for cat, t in targets.items():
            if dim == "group":
                a = sum(1 for i in ideas if i.get("id", "").split("-")[1] == cat) / n
            else:
                a = sum(1 for i in ideas if i.get(dim) == cat) / n
            if abs(a - t) > 0.02:
                warnings.append(f"[V-12] {dim}/{cat} actual {a*100:.1f}% vs target {t*100:.0f}%")


def load_ideas_file(path):
    obj = json.load(open(path, encoding="utf-8"))
    if isinstance(obj, list):
        return obj, None
    if isinstance(obj, dict) and isinstance(obj.get("ideas"), list):
        return obj["ideas"], obj
    return [], obj


def run_all(root=None):
    root = root or _repo_root()
    errors, warnings = [], []

    # baseline
    b_path = os.path.join(root, "apps", "core", "data", "baseline_v1.json")
    ideas, meta = load_ideas_file(b_path)
    validate_library(ideas, errors, warnings, ctx="baseline")
    baseline_ids = set(i.get("id") for i in ideas if isinstance(i, dict))
    merged = list(ideas)

    # 分行业文件与 baseline 一致性
    ideas_dir = os.path.join(root, "content", "ideas")
    if os.path.isdir(ideas_dir):
        file_ids = []
        for fn in sorted(os.listdir(ideas_dir)):
            if fn.endswith(".json"):
                fi, _ = load_ideas_file(os.path.join(ideas_dir, fn))
                validate_library(fi, errors, warnings, ctx=fn, share_checks=False)
                file_ids.extend(i.get("id") for i in fi if isinstance(i, dict))
        if set(file_ids) != baseline_ids:
            errors.append("[V-12] content/ideas files do not match baseline_v1.json")

    # delta 文件（V-11 + add 全量校验 + 合并后 V-07/V-08/V-12）
    hosting = os.path.join(root, "hosting")
    deltas = []
    if os.path.isdir(hosting):
        for fn in sorted(os.listdir(hosting)):
            if fn.startswith("delta_") and fn.endswith(".json"):
                try:
                    d = json.load(open(os.path.join(hosting, fn), encoding="utf-8"))
                except (OSError, ValueError) as e:
                    errors.append(f"[V-11] {fn} unreadable: {e}")
                    continue
                deltas.append((fn, d))
                for r in d.get("revise") or []:
                    if not isinstance(r, dict) or r.get("id") not in baseline_ids:
                        errors.append(f"[V-11] {fn} revise id {r.get('id')!r} not in baseline")
                    bad = set((r or {}).keys()) - REVISE_WHITELIST - {"id"}
                    if bad:
                        errors.append(f"[V-11] {fn} revise has non-whitelisted fields: {sorted(bad)}")
                for rid in d.get("retire") or []:
                    if rid not in baseline_ids:
                        errors.append(f"[V-11] {fn} retire id {rid!r} not in baseline")
                for a in d.get("add") or []:
                    if isinstance(a, dict):
                        validate_idea(a, errors, warnings, ctx=fn)
                        merged.append(a)

    if merged:
        validate_library([m for m in merged], errors, warnings, ctx="merged")  # 触发合并后 V-07/V-08
        check_v12(merged, errors, warnings)

    # V-10 locales
    locales = os.path.join(root, "apps", "web", "src", "locales")
    if os.path.isdir(locales):
        check_v10(locales, errors)

    return errors, warnings


def main(argv):
    root = _repo_root()
    if argv:
        errors, warnings = [], []
        for p in argv:
            ideas, _ = load_ideas_file(p if os.path.isabs(p) else os.path.join(root, p))
            validate_library(ideas, errors, warnings, ctx=os.path.basename(p))
    else:
        errors, warnings = run_all(root)
    for w in warnings:
        print("WARN", w)
    for e in errors:
        print("ERROR", e)
    print(f"validate: {len(errors)} errors, {len(warnings)} warnings -> "
          f"{'FAIL' if errors else 'PASS'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
