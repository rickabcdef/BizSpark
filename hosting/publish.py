# -*- coding: utf-8 -*-
"""hosting.publish — D-08：月度发布一键工具（负责人：D，F09 / §5.5 / 附录 B）

流程（§5.5 SOP 第 4 步）：生成 → 校验 → 更新 manifest → 上传
  python hosting/publish.py --release 2026-12-01
  python hosting/publish.py --release 2026-12-01 --upload-cmd "aws s3 cp {file} s3://bucket/"

上传为可插拔：提供 --upload-cmd（或环境变量 BIZSPARK_UPLOAD_CMD）则执行，否则仅落盘到
hosting/out/（由人工/CI 同步到静态托管）。绝不携带任何用户标识；manifest 是客户端
唯一常驻出网目标的索引（§3.7）。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "apps", "core"))

from library.validate import run_all  # noqa: E402


def main(argv):
    ap = argparse.ArgumentParser(description="BizSpark monthly publish (D)")
    ap.add_argument("--release", required=True, help="release date YYYY-MM-DD")
    ap.add_argument("--upload-cmd", default=None, help="upload command with {file} placeholder")
    ap.add_argument("--dry-run", action="store_true", help="validate only, write nothing")
    args = ap.parse_args(argv)

    month = args.release[:7]

    # 1) 校验 V-01…V-12（失败阻断构建）
    errors, warnings = run_all(ROOT)
    for w in warnings:
        print("WARN", w)
    for e in errors:
        print("ERROR", e)
    if errors:
        print(f"publish aborted: {len(errors)} validation errors")
        return 1

    # 2) delta 文件必须已生成（delta_tool）
    delta_path = os.path.join(ROOT, "hosting", f"delta_{month}.json")
    if not os.path.isfile(delta_path):
        print(f"publish aborted: missing {delta_path} — run library.delta_tool first")
        return 1
    delta = json.load(open(delta_path, encoding="utf-8"))
    if delta.get("release") != args.release:
        print(f"publish aborted: delta release {delta.get('release')} != {args.release}")
        return 1

    size_kb = max(1, round(os.path.getsize(delta_path) / 1024))
    files = [f"delta_{month}.json"]

    manifest = {"latest": month, "files": files, "size_kb": size_kb,
                "min_client": "1.0.0", "published_at": args.release}
    print(f"[publish] manifest: latest={month} files={files} size_kb={size_kb}")

    if args.dry_run:
        print("[publish] dry-run: manifest not written")
        return 0

    # 3) 更新 manifest（原子写）
    m_path = os.path.join(ROOT, "hosting", "manifest.json")
    tmp = m_path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    os.replace(tmp, m_path)
    print(f"[publish] manifest updated -> hosting/manifest.json")

    # 4) 上传（可插拔；缺省落盘 hosting/out/）
    out_dir = os.path.join(ROOT, "hosting", "out")
    os.makedirs(out_dir, exist_ok=True)
    staged = [delta_path, m_path]
    for p in staged:
        shutil.copy2(p, os.path.join(out_dir, os.path.basename(p)))
    print(f"[publish] staged -> hosting/out/ ({', '.join(os.path.basename(p) for p in staged)})")

    cmd = args.upload_cmd or os.environ.get("BIZSPARK_UPLOAD_CMD")
    if cmd:
        for p in staged:
            real = cmd.format(file=p)
            print(f"[publish] upload: {real}")
            rc = subprocess.call(real, shell=True)
            if rc != 0:
                print(f"[publish] upload failed (exit {rc}) — manifest updated but not live")
                return 1
    else:
        print("[publish] no upload cmd configured (BIZSPARK_UPLOAD_CMD) — files staged locally")
    print(f"[publish] OK {args.release}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
