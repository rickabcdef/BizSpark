# -*- coding: utf-8 -*-
"""export_bench — E-09 导出性能基准（F14.1：导出 ≤2s）

用法：python qa/perf/export_bench.py [次数]
对真实 baseline 库抽样导出 PDF（A4 + Letter）与 CSV，统计耗时分布。
红线：单次导出 ≤2000ms（T-27）；打印 PASS/FAIL 退出码供 H 汇总。
"""

import json
import os
import shutil
import sys
import tempfile
import time

_CORE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     "apps", "core")
sys.path.insert(0, _CORE)

from engine import get_idea                       # noqa: E402
from render.pdf import export_plan                # noqa: E402
from render.csv import export_csv                 # noqa: E402

BUDGET_MS = 2000  # T-27 / F14.1


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    with open(os.path.join(_CORE, "data", "baseline_v1.json"), encoding="utf-8") as f:
        lib = json.load(f)
    ideas = lib if isinstance(lib, list) else lib["ideas"]
    tmpdir = tempfile.mkdtemp(prefix="bizspark_bench_")
    samples = []
    try:
        for i in range(rounds):
            idea = ideas[i * 13 % len(ideas)]
            paper = "A4" if i % 2 == 0 else "Letter"
            t0 = time.perf_counter()
            data, err = export_plan({"id": idea["id"], "path": os.path.join(tmpdir, "plan.pdf"),
                                     "paper": paper})
            pdf_ms = (time.perf_counter() - t0) * 1000
            t1 = time.perf_counter()
            export_csv({"id": idea["id"], "path": os.path.join(tmpdir, "plan.pdf")})
            csv_ms = (time.perf_counter() - t1) * 1000
            assert err is None, "export failed: %s" % err
            assert data["pages"] == 1, "pages must be 1, got %s" % data["pages"]
            samples.append(pdf_ms)
            print("round %2d  %-12s  %-6s  pdf %7.1f ms  csv %6.1f ms  pages %d  bytes %d"
                  % (i + 1, idea["id"], paper, pdf_ms, csv_ms, data["pages"], data["bytes"]))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    worst = max(samples)
    avg = sum(samples) / len(samples)
    ok = worst <= BUDGET_MS
    print("-" * 64)
    print("pdf avg %.1f ms | worst %.1f ms | budget %d ms | %s"
          % (avg, worst, BUDGET_MS, "PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
