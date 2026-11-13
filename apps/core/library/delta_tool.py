# -*- coding: utf-8 -*-
"""library.delta_tool — D-07：月度 delta 工具（负责人：D，F09 / §3.7 / §5.5，用例 T-40）

能力：
- add：完整 Idea（必须过 §3.2 校验）
- revise：只允许白名单字段（maturity/version/updated_at/first_customers/pricing_hint/
  cost_breakdown/status/compliance_note/pitfalls/channel_ids）
- retire：只给 id（不硬删，仅置 status=retired，磁盘条目保留）
- 校验：V-11（revise/retire 的 id 必须存在于当前库）+ 白名单检查 + add 全量校验

用法：
  python -m library.delta_tool --release 2026-12-01 --adds adds.json --revises r.json --retire id1,id2
  （在 apps/core 目录下运行；或作为模块 import create_delta/validate_delta）
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.validate import REVISE_WHITELIST, validate_idea  # noqa: E402


def _repo_root():
    p = os.path.dirname(os.path.abspath(__file__))
    while p != os.path.dirname(p):
        if os.path.isdir(os.path.join(p, "apps", "core")):
            return p
        p = os.path.dirname(p)
    return os.getcwd()


def load_baseline_ids(root=None):
    root = root or _repo_root()
    path = os.path.join(root, "apps", "core", "data", "baseline_v1.json")
    data = json.load(open(path, encoding="utf-8"))
    ids = {i["id"] for i in data.get("ideas", []) if isinstance(i, dict)}
    # 叠加此前 delta 的 add（链式合并）
    hosting = os.path.join(root, "hosting")
    if os.path.isdir(hosting):
        for fn in sorted(os.listdir(hosting)):
            if fn.startswith("delta_") and fn.endswith(".json"):
                d = json.load(open(os.path.join(hosting, fn), encoding="utf-8"))
                ids |= {a["id"] for a in d.get("add", []) if isinstance(a, dict) and "id" in a}
    return ids


def create_delta(release, adds, revises, retires, target_baseline="v1", root=None):
    """组装 delta 文件对象并校验（T-40 前置）。返回 (delta, errors)。"""
    errors = []
    known = load_baseline_ids(root)
    delta = {"target_baseline": target_baseline, "release": release,
             "add": [], "revise": [], "retire": []}
    for a in adds or []:
        if not isinstance(a, dict) or "id" not in a:
            errors.append("add item missing id")
            continue
        if a["id"] in known:
            errors.append(f"add id {a['id']} already exists in library (use revise)")
            continue
        err_w = ([], [])
        validate_idea(a, *err_w)
        errors.extend(err_w[0])
        delta["add"].append(a)
    for r in revises or []:
        if not isinstance(r, dict) or r.get("id") not in known:
            errors.append(f"[V-11] revise id {r.get('id')!r} not in current library")
            continue
        bad = set(r.keys()) - REVISE_WHITELIST - {"id"}
        if bad:
            errors.append(f"revise {r['id']} has non-whitelisted fields: {sorted(bad)}")
            continue
        if "version" in r and "updated_at" not in r:
            errors.append(f"revise {r['id']} must bump updated_at together with version")
            continue
        delta["revise"].append(r)
    for rid in retires or []:
        if rid not in known:
            errors.append(f"[V-11] retire id {rid!r} not in current library")
            continue
        delta["retire"].append(rid)
    if not (delta["add"] or delta["revise"] or delta["retire"]):
        errors.append("delta is empty")
    return delta, errors


def validate_delta(delta, errors):
    """对已存在的 delta 文件做合并方向校验（白名单 + V-11 由 validate.run_all 覆盖）。"""
    for r in delta.get("revise") or []:
        bad = set(r.keys()) - REVISE_WHITELIST - {"id"}
        if bad:
            errors.append(f"revise {r.get('id')} non-whitelisted fields: {sorted(bad)}")
    for key in ("add", "revise", "retire"):
        if not isinstance(delta.get(key), list):
            errors.append(f"delta.{key} must be a list")


def merge_delta(baseline_ideas, delta):
    """把 delta 合并进库（纯函数，T-40 用）：add 追加 / revise 白名单字段覆盖并 version+1 / retire 置 status。"""
    by_id = {i["id"]: dict(i) for i in baseline_ideas if isinstance(i, dict)}
    merged = list(by_id.values())
    for a in delta.get("add") or []:
        if a.get("id") in by_id:
            raise ValueError(f"add id {a['id']} already exists")
        merged.append(dict(a))
    for r in delta.get("revise") or []:
        item = by_id.get(r.get("id"))
        if item is None:
            raise ValueError(f"revise id {r.get('id')} not found")
        for k, v in r.items():
            if k != "id":
                item[k] = v
        if "version" not in r:  # payload 已带 version 则以其为准，避免双重递增
            item["version"] = item.get("version", 1) + 1
    for rid in delta.get("retire") or []:
        item = by_id.get(rid)
        if item is None:
            raise ValueError(f"retire id {rid} not found")
        item["status"] = "retired"
    return merged


def main(argv):
    ap = argparse.ArgumentParser(description="BizSpark monthly delta tool (D)")
    ap.add_argument("--release", required=True, help="release date YYYY-MM-DD")
    ap.add_argument("--adds", help="JSON file with array of full Ideas")
    ap.add_argument("--revises", help="JSON file with array of whitelist-field revises")
    ap.add_argument("--retire", help="comma-separated ids to retire")
    ap.add_argument("--out", help="output path hosting/delta_YYYY-MM.json (auto from release)")
    ap.add_argument("--root", default=None)
    args = ap.parse_args(argv)

    adds = json.load(open(args.adds, encoding="utf-8")) if args.adds else []
    revises = json.load(open(args.revises, encoding="utf-8")) if args.revises else []
    retires = args.retire.split(",") if args.retire else []
    delta, errors = create_delta(args.release, adds, revises, retires, root=args.root)
    if errors:
        for e in errors:
            print("ERROR", e)
        return 1
    out = args.out or os.path.join(
        _hosting_dir(args.root), "delta_{}.json".format(args.release[:7]))
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(delta, f, ensure_ascii=False, indent=1)
    print(f"delta written: {out} (add {len(delta['add'])}, revise {len(delta['revise'])}, retire {len(delta['retire'])})")
    return 0


def _hosting_dir(root=None):
    root = root or _repo_root()
    return os.path.join(root, "hosting")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
