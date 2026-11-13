"""perf_suite.py — F14.1 六项性能指标（负责人：H）

1) 冷启动到可操作（sidecar ready + 首屏可用）
2) diagnose（312 条）≤300ms
3) 导出 PDF ≤2s
4) 常驻内存 ≤300MB（sidecar RSS）
5) 包体 ≤80MB（前端 dist + Python 源；真安装包由 pack.sh 量）
6) 出网请求 = 0（socket 全禁后跑完整链路）

用法：python qa/perf/perf_suite.py [轮数]
输出：qa/reports/perf.json + 控制台表格
"""

from __future__ import annotations

import ctypes
import json
import os
import statistics
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cases"))

import harness  # noqa: E402

IDEAS = harness.load_baseline()
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 12
LIMITS = {
    "cold_start_ms": 1500,
    "diagnose_ms": 300,
    "export_ms": 2000,
    "rss_mb": 300,
    "bundle_mb": 80,
    "egress": 0,
}


def rss_mb(pid: int) -> float:
    """进程常驻内存（Windows 用 psapi，POSIX 用 /proc）。"""
    if os.name == "nt":
        class PMC(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]

        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not h:
            return -1.0
        try:
            counters = PMC()
            counters.cb = ctypes.sizeof(PMC)
            if ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(counters), counters.cb):
                return counters.WorkingSetSize / (1024 * 1024)
            return -1.0
        finally:
            k32.CloseHandle(h)
    try:
        with open("/proc/%d/status" % pid) as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except OSError:
        pass
    return -1.0


def dir_size_mb(path) -> float:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total / (1024 * 1024)


def measure() -> dict:
    out: dict = {"rounds": ROUNDS, "metrics": {}}

    # 1) 冷启动：从 spawn 到首行 ready
    starts = []
    for _ in range(3):
        sc = harness.Sidecar()
        t0 = time.perf_counter()
        sc.start()
        starts.append((time.perf_counter() - t0) * 1000)
        sc.cleanup()
    out["metrics"]["cold_start_ms"] = round(min(starts), 1)

    sc = harness.Sidecar().start()
    try:
        answers = {"answers": harness.default_answers()}
        sc.ok("diagnose", answers)

        # 2) diagnose
        diag = []
        for i in range(ROUNDS):
            a = {"answers": harness.default_answers(
                capital=["<500", "500-2k", "2k-10k", "10k+"][i % 4],
                hours=["<10", "10-25", "full"][i % 3])}
            t0 = time.perf_counter()
            d = sc.ok("diagnose", a)
            diag.append((time.perf_counter() - t0) * 1000)
            assert d["checked"] >= 300

        # 3) 导出
        ex = []
        for i in range(min(ROUNDS, 8)):
            path = sc.app_file("perf_%d.pdf" % i)
            t0 = time.perf_counter()
            r = sc.ok("export_plan", {"id": IDEAS[i]["id"], "path": path})
            ex.append((time.perf_counter() - t0) * 1000)
            assert r["pages"] == 1 and os.path.isfile(path)

        # 4) 内存（跑完一轮之后的稳定值）
        sc.ok("diagnose", answers)
        mem = rss_mb(sc.proc.pid)

        out["metrics"]["diagnose_ms"] = {
            "p50": round(statistics.median(diag), 1),
            "p95": round(sorted(diag)[max(0, int(len(diag) * 0.95) - 1)], 1),
            "max": round(max(diag), 1),
        }
        out["metrics"]["export_ms"] = {
            "p50": round(statistics.median(ex), 1),
            "max": round(max(ex), 1),
        }
        out["metrics"]["rss_mb"] = round(mem, 1)
    finally:
        sc.cleanup()

    # 5) 包体（前端 dist + sidecar 源 + 数据；真安装包看 pack.sh）
    web = harness.REPO / "apps" / "web" / "dist"
    core = harness.CORE
    out["metrics"]["bundle_mb"] = {
        "web_dist": round(dir_size_mb(web), 1) if web.is_dir() else 0.0,
        "core_py_and_data": round(dir_size_mb(core), 1),
        "note": "真安装包（Tauri + PyInstaller）≤80MB 由 scripts/pack.sh 校验；此处为未压缩源体积",
    }

    # 6) 出网：socket 全禁后跑完整链路
    guard = tempfile.mkdtemp(prefix="bz_egress_")
    with open(os.path.join(guard, "sitecustomize.py"), "w", encoding="utf-8") as f:
        f.write("import socket\n"
                "def _deny(*a, **k):\n"
                "    raise RuntimeError('network disabled (F14.1)')\n"
                "socket.socket = _deny\n"
                "socket.create_connection = _deny\n"
                "socket.getaddrinfo = _deny\n")
    ok = False
    try:
        with harness.Sidecar(env={"PYTHONPATH": guard}) as sc2:
            sc2.ok("diagnose", {"answers": harness.default_answers()})
            sc2.ok("get_idea", {"id": IDEAS[0]["id"]})
            sc2.ok("save_idea", {"id": IDEAS[0]["id"]})
            sc2.ok("list_saved")
            sc2.ok("get_settings")
            sc2.ok("check_library")
            sc2.ok("license_status")
            sc2.ok("export_plan", {"id": IDEAS[0]["id"], "path": sc2.app_file("e.pdf")})
            ok = True
    finally:
        import shutil
        shutil.rmtree(guard, ignore_errors=True)
    out["metrics"]["egress"] = 0 if ok else -1

    # 判定
    verdict = {
        "cold_start_ms": out["metrics"]["cold_start_ms"] <= LIMITS["cold_start_ms"],
        "diagnose_ms": out["metrics"]["diagnose_ms"]["p95"] <= LIMITS["diagnose_ms"],
        "export_ms": out["metrics"]["export_ms"]["max"] <= LIMITS["export_ms"],
        "rss_mb": 0 <= out["metrics"]["rss_mb"] <= LIMITS["rss_mb"],
        "bundle_mb": out["metrics"]["bundle_mb"]["web_dist"] + out["metrics"]["bundle_mb"]["core_py_and_data"]
        <= LIMITS["bundle_mb"],
        "egress": out["metrics"]["egress"] == 0,
    }
    out["limits"] = LIMITS
    out["verdict"] = verdict
    out["pass"] = all(verdict.values())
    return out


def main() -> int:
    data = measure()
    report = harness.REPO / "qa" / "reports" / "perf.json"
    harness.write_json(report, data)

    m = data["metrics"]
    print("\n== F14.1 性能（%d 轮） ==" % data["rounds"])
    print("冷启动到 ready      %8.1f ms   红线 %d  %s"
          % (m["cold_start_ms"], LIMITS["cold_start_ms"], "PASS" if data["verdict"]["cold_start_ms"] else "FAIL"))
    print("diagnose 312 条     p50 %6.1f / p95 %6.1f ms   红线 %d  %s"
          % (m["diagnose_ms"]["p50"], m["diagnose_ms"]["p95"], LIMITS["diagnose_ms"],
             "PASS" if data["verdict"]["diagnose_ms"] else "FAIL"))
    print("导出 PDF            p50 %6.1f / max %6.1f ms   红线 %d  %s"
          % (m["export_ms"]["p50"], m["export_ms"]["max"], LIMITS["export_ms"],
             "PASS" if data["verdict"]["export_ms"] else "FAIL"))
    print("常驻内存            %8.1f MB   红线 %d  %s"
          % (m["rss_mb"], LIMITS["rss_mb"], "PASS" if data["verdict"]["rss_mb"] else "FAIL"))
    print("包体（dist+core）   %8.1f MB   红线 %d  %s"
          % (m["bundle_mb"]["web_dist"] + m["bundle_mb"]["core_py_and_data"], LIMITS["bundle_mb"],
             "PASS" if data["verdict"]["bundle_mb"] else "FAIL"))
    print("出网请求            %8d 处   红线 0   %s"
          % (m["egress"], "PASS" if data["verdict"]["egress"] else "FAIL"))
    print("报告：%s" % report)
    return 0 if data["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
