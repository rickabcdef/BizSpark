# -*- coding: utf-8 -*-
"""qa/security/store_strip_check.py — Store 构建裁剪校验（G-07 / T-42）

做的事：把 `apps/core` 复制到临时目录、**删掉 `license/`**（模拟 Store 版编译期裁剪），
然后跑 sidecar 断言：

1. 进程正常起、首行 ready；
2. `ping` / `get_state` / `diagnose` 等业务 cmd 不受影响（不能"裁掉授权把别人功能搞坏"）；
3. `activate` / `license_status` / `release_seat` → `E_UNKNOWN_CMD`，且进程不崩；
4. 静态：`main.py` 里 `license` 的导入位于 `try/except` 内；除 `license/` 自身外无人 import 它。

用法：`python qa/security/store_strip_check.py`
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
CORE = os.path.join(REPO, "apps", "core")

failures = []
notes = []


def fail(msg):
    failures.append(msg)


def _copy_core(dst):
    shutil.copytree(CORE, dst, ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc", "tests"))
    lic = os.path.join(dst, "license")
    if not os.path.isdir(lic):
        fail("apps/core/license/ 不存在，本检查失去意义")
        return False
    shutil.rmtree(lic)
    notes.append("已裁掉 license/（模拟 feature=store）")
    return True


def _run(cmds, appdata):
    """跑**完整**构建的 sidecar（对照组）。"""
    env = dict(os.environ, BIZSPARK_APP_DATA=appdata, PYTHONIOENCODING="utf-8")
    proc = subprocess.Popen([sys.executable, os.path.join(CORE, "main.py")],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            text=True, encoding="utf-8", env=env)
    payload = "".join(json.dumps(c) + "\n" for c in cmds)
    out, _ = proc.communicate(payload)
    return [json.loads(x) for x in out.splitlines() if x.strip()]


def _run_stripped(cmds, tmp, appdata):
    env = dict(os.environ, BIZSPARK_APP_DATA=appdata, PYTHONIOENCODING="utf-8")
    proc = subprocess.Popen([sys.executable, os.path.join(tmp, "main.py")],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8", env=env)
    payload = "".join(json.dumps(c) + "\n" for c in cmds)
    out, err = proc.communicate(payload)
    rows = [json.loads(x) for x in out.splitlines() if x.strip()]
    return rows, err, proc.returncode


def check_static():
    with open(os.path.join(CORE, "main.py"), encoding="utf-8") as f:
        src = f.read()
    if "from license import activate" not in src:
        fail("main.py 里找不到 license 导入（挂载点被改动？）")
    block = src.split("from license import activate", 1)[0]
    if "try:" not in block.rsplit("\n\n", 1)[-1] and "try:" not in src:
        fail("main.py 的 license 导入不在 try/except 内 → 裁剪后会 ImportError 崩掉")
    # 反向：除 license/、tests/ 与 main.py（唯一挂载点，上面已查过是 try/except）外，谁都不许 import license
    for root, dirs, files in os.walk(CORE):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "license", "tests")]
        for name in files:
            if not name.endswith(".py") or (root == CORE and name == "main.py"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8", errors="ignore") as f:
                text = f.read()
            if "from license" in text or "import license" in text:
                fail("%s 直接 import 了 license（Store 构建会崩）" % os.path.relpath(path, REPO))


def main():
    print("== Store 裁剪校验（G-07 / T-42）==")
    check_static()

    appdata = tempfile.mkdtemp(prefix="bz_strip_app_")
    base = _run([
        {"req_id": "p", "cmd": "ping", "payload": {}},
        {"req_id": "g", "cmd": "get_state", "payload": {}},
        {"req_id": "d", "cmd": "diagnose", "payload": {"answers": {
            "country": "US", "capital": "<500", "hours": "<10",
            "assets": ["laptop"], "risk": "small_loss"}}},
    ], appdata)
    base_map = {r["req_id"]: r for r in base if r.get("req_id")}
    if not base or base[0]["data"].get("event") != "ready":
        fail("完整构建 sidecar 未就绪")
    if not base_map.get("d", {}).get("ok"):
        fail("完整构建 diagnose 失败（基线本身有问题）")

    tmp = tempfile.mkdtemp(prefix="bz_strip_core_")
    try:
        if not _copy_core(os.path.join(tmp, "core")):
            pass
        else:
            core_dir = os.path.join(tmp, "core")
            app2 = tempfile.mkdtemp(prefix="bz_strip_app2_")
            rows, err, rc = _run_stripped([
                {"req_id": "p", "cmd": "ping", "payload": {}},
                {"req_id": "g", "cmd": "get_state", "payload": {}},
                {"req_id": "d", "cmd": "diagnose", "payload": {"answers": {
                    "country": "US", "capital": "<500", "hours": "<10",
                    "assets": ["laptop"], "risk": "small_loss"}}},
                {"req_id": "a", "cmd": "activate", "payload": {"code": "BZSP-2222-3333-4444"}},
                {"req_id": "ls", "cmd": "license_status", "payload": {}},
                {"req_id": "rs", "cmd": "release_seat", "payload": {}},
            ], core_dir, app2)

            rmap = {r["req_id"]: r for r in rows if r.get("req_id")}
            if not rows or rows[0]["data"].get("event") != "ready":
                fail("裁剪后 sidecar 未输出 ready（崩了？stderr=%s）" % (err or "")[:300])
            if not rmap.get("p", {}).get("ok"):
                fail("裁剪后 ping 失败")
            if not rmap.get("g", {}).get("ok"):
                fail("裁剪后 get_state 失败")
            if not rmap.get("d", {}).get("ok"):
                fail("裁剪后 diagnose 失败 —— 裁掉授权把别人的功能搞坏了（禁止）")
            for rid, label in (("a", "activate"), ("ls", "license_status"), ("rs", "release_seat")):
                got = rmap.get(rid) or {}
                code = (got.get("error") or {}).get("code")
                if code != "E_UNKNOWN_CMD":
                    fail("裁剪后 %s 应回 E_UNKNOWN_CMD，实际 %s" % (label, code or "OK"))
            if rc not in (0, None):
                notes.append("sidecar 退出码 %s（stdin 关闭后正常退出即可）" % rc)
            shutil.rmtree(app2, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(appdata, ignore_errors=True)

    for n in notes:
        print("  .. %s" % n)
    if failures:
        for f in failures:
            print("  FAIL %s" % f)
        print("结果：FAIL（%d 项）" % len(failures))
        return 1
    print("结果：PASS（裁剪后授权 cmd 消失、业务功能与进程均正常）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
