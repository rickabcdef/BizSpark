#!/usr/bin/env python3
"""run_all.py — H-02 一键全量回归（负责人：H）

用法：
  python qa/e2e/run_all.py                 # 标准全量（单测 + UI + 性能 + 离线演练）
  python qa/e2e/run_all.py --with-visual   # 追加视觉回归截图（9+9 屏，较慢）
  python qa/e2e/run_all.py --fast          # 跳过性能与离线演练（只跑单测 + UI）

阶段：
  engine / detail_export / state / license / content / packaging / contract / price
    → qa/cases/*.py（真 sidecar IPC）
  ui        → qa/cases/test_ui.py（Playwright + 系统 Edge + 真前端 dist）
  perf      → qa/perf/perf_suite.py（F14.1 六项红线）
  drill     → qa/offline/drill.py（H-04 离线演练矩阵）
  visual    → qa/visual/screenshots.mjs（--with-visual）

产出：qa/reports/run-all-summary.json + 控制台总表。
退出码：0 = 无 FAIL；1 = 有 FAIL；2 = 环境问题。
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

QA = Path(__file__).resolve().parents[1]
REPO = QA.parent
REPORT = QA / "reports" / "run-all-summary.json"

UNIT_MODULES = [
    "engine",
    "detail_export",
    "state",
    "license",
    "content",
    "packaging",
    "contract",
    "price",
]


def run(name: str, argv: list[str], cwd: Path, timeout: int = 1800) -> dict:
    t0 = time.time()
    proc = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                          timeout=timeout, shell=False)
    dt = round(time.time() - t0, 1)
    tail = "\n".join(((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()[-8:])
    ok = proc.returncode == 0
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:<14} {dt:>6.1f}s"
          + ("" if ok else "\n" + "\n".join("        " + l for l in tail.splitlines())))
    return {"stage": name, "argv": argv, "cwd": str(cwd),
            "returncode": proc.returncode, "elapsed_s": dt,
            "status": "PASS" if ok else "FAIL", "tail": tail}


def main() -> int:
    fast = "--fast" in sys.argv
    with_visual = "--with-visual" in sys.argv
    t0 = time.time()
    print("== BizSpark 一键全量回归 ==")

    stages: list[dict] = []
    for mod in UNIT_MODULES:
        stages.append(run(mod, [sys.executable, "-m", "unittest", f"qa.cases.test_{mod}",
                                "-v"], REPO, timeout=1800))
    stages.append(run("ui", [sys.executable, "-m", "unittest", "qa.cases.test_ui",
                             "-v"], REPO, timeout=1500))
    if not fast:
        stages.append(run("perf", [sys.executable, "qa/perf/perf_suite.py"], REPO,
                          timeout=900))
        stages.append(run("drill", [sys.executable, "qa/offline/drill.py"], REPO,
                          timeout=900))
    if with_visual:
        node = "node"
        stages.append(run("visual", [node, "visual/screenshots.mjs"], QA, timeout=900))

    summary = {
        "task": "H-02 一键全量回归",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_s": round(time.time() - t0, 1),
        "stages": stages,
        "failed": [s["stage"] for s in stages if s["status"] == "FAIL"],
        "status": "PASS" if all(s["status"] == "PASS" for s in stages) else "FAIL",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"总评：{summary['status']}   阶段 {len(stages)} 个   "
          f"失败 {len(summary['failed']) or '无'}   用时 {summary['elapsed_s']}s")
    print(f"报告：{REPORT}")
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
