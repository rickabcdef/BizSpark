# -*- coding: utf-8 -*-
"""normalize_cluster_costs.py — 同业务簇成本归一（PM 2026-11-14，老板反馈 bug）

问题（老板 2026-11-14 截图反馈）：
  baseline_v1.json 把 26 门生意灌成了 312 个"地点变体"，且变体的成本是按
  min_capital 固定比例（约 40%/30%/30%）机械缩放的——结果"同一把刮水器"
  在同一座城市从 USD 28 到 3,478 都有（bs-svc-window-cleaning-069 = 3478，
  -071 = 28）。做生意趋利避害，同样的工具就该花同样的钱。

修复口径：
  1. 业务簇 = idea id 去掉尾部 -NNN（如 bs-svc-window-cleaning）
  2. 簇基准 = title 不带地点后缀（无 "("）的条目；多条则取 min_capital 最小者
  3. 簇内所有条目的同名成本项金额 = 基准金额（工具价全城一致）
  4. min_capital = 该条 cost_breakdown 金额之和（保持"合计=起步资金"自洽）
  5. capital_tier 按 min_capital 重算（<500 / 500-2k / 2k-10k / 10k+，
     边界与 engine/filter.py 的向上兼容档位一致）
  6. zh_v1.json 同步：对应条目 cost_items[].amount 更新为新源值
     （zhpack.apply_cost_labels 要求金额逐条相等才覆盖中文标签）

定价（pricing_hint）不动：按次/月结/整屋是商业模式差异，不是数据错误；
推荐层已做同簇去重（engine/__init__.py），同一屏不会再出现同生意多个变体。

用法：
  python tools/normalize_cluster_costs.py            # 试运行（dry-run，只打印）
  python tools/normalize_cluster_costs.py --write    # 实际写回两个数据文件

幂等：跑第二遍不会再有变化。
"""

import json
import os
import re
import sys
from collections import defaultdict

CORE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "apps", "core")
BASELINE = os.path.join(CORE, "data", "baseline_v1.json")
ZH = os.path.join(CORE, "data", "zh_v1.json")

WRITE = "--write" in sys.argv


def tier_of(min_capital: int) -> str:
    """与数据现状一致的档位边界（校验过 312 条 0 冲突）。"""
    if min_capital < 500:
        return "<500"
    if min_capital <= 2000:
        return "500-2k"
    if min_capital <= 10000:
        return "2k-10k"
    return "10k+"


def main() -> None:
    doc = json.load(open(BASELINE, encoding="utf-8"))
    ideas = doc["ideas"]

    clusters: dict[str, list] = defaultdict(list)
    for idea in ideas:
        clusters[re.sub(r"-\d+$", "", str(idea["id"]))].append(idea)

    changed = 0
    for key, members in sorted(clusters.items()):
        base_candidates = [m for m in members if "(" not in str(m.get("title", ""))]
        pool = base_candidates or members
        baseline = min(pool, key=lambda m: m["min_capital"])
        bench = {c["item"]: c["amount"] for c in baseline.get("cost_breakdown", [])}

        for m in members:
            before = (m["min_capital"], [(c["item"], c["amount"]) for c in m.get("cost_breakdown", [])])
            for c in m.get("cost_breakdown", []):
                if c["item"] in bench:
                    c["amount"] = bench[c["item"]]
            total = sum(int(c["amount"]) for c in m.get("cost_breakdown", []))
            m["min_capital"] = total
            m["capital_tier"] = tier_of(total)
            after = (m["min_capital"], [(c["item"], c["amount"]) for c in m.get("cost_breakdown", [])])
            if before != after:
                changed += 1
                if changed <= 3:
                    print(f"[样例] {m['id']}: min_capital {before[0]} → {after[0]}, "
                          f"tier {tier_of(before[0])} → {m['capital_tier']}")

    # zh_v1 同步金额（标签不动，金额必须与源逐条相等）
    zh = json.load(open(ZH, encoding="utf-8"))
    zh_changed = 0
    for idea in ideas:
        entry = zh.get(str(idea["id"]))
        if not isinstance(entry, dict):
            continue
        src_costs = idea.get("cost_breakdown", [])
        zh_items = entry.get("cost_items")
        if isinstance(zh_items, list) and len(zh_items) == len(src_costs):
            for s, z in zip(src_costs, zh_items):
                if isinstance(z, dict) and z.get("amount") != s.get("amount"):
                    z["amount"] = s.get("amount")
                    zh_changed += 1

    print(f"\n簇数 {len(clusters)} | 基线条目被修改 {changed}/{len(ideas)} | zh_v1 金额项同步 {zh_changed} 处")
    if not WRITE:
        print("\n(dry-run，未写回。加 --write 生效)")
        return

    json.dump(doc, open(BASELINE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(zh, open(ZH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"已写回:\n  {BASELINE}\n  {ZH}")


if __name__ == "__main__":
    main()
