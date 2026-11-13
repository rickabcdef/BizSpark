"""test_license.py — T-41、T-43、T-44、T-45（负责人：H 验收 / G 修复）

用 G 签发的演示码跑真实激活链路（不 mock 签名）。演示码文件缺失则 skip，
绝不假通过。T-42/T-55（Store 包裁授权）在 test_packaging.py。
"""

from __future__ import annotations

import json
import os
import stat
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness  # noqa: E402

CODES = harness.demo_codes()
POOL = harness.read_json(harness.CORE / "license" / "pool.json")


def h(tag: str) -> str:
    """"另一台电脑"的指纹（64 位十六进制，与 G 的 _valid_hash 同形）。"""
    import hashlib
    return hashlib.sha256(("qa-device-" + tag).encode()).hexdigest()


class LicenseBase(unittest.TestCase):
    def setUp(self) -> None:
        if not CODES:
            self.skipTest("没有演示码（%APPDATA%/BizSpark-issuer/codes-2026-11-dev.txt 缺失）")
        self.sc = harness.Sidecar().start()

    def tearDown(self) -> None:
        getattr(self, "sc", None) and self.sc.cleanup()

    def lic_path(self) -> str:
        return os.path.join(self.sc.app_data, "license.dat")


class T41FirstActivation(LicenseBase):
    """T-41：正确码 → 激活成功、license.dat 权限 600、席位 1/3。"""

    CASES = ["T-41"]

    def test_activate_once(self):
        st0 = self.sc.ok("license_status")
        self.assertIn(st0.get("state"), ("none", "unseated", None, ""), "初始状态异常：%r" % st0)

        bad = self.sc.err("activate", {"code": "BZSP-9999-8888-7777"})
        self.assertEqual(bad.get("code"), "E_LICENSE_BAD_CODE")
        self.assertTrue(bad.get("recoverable"))
        self.assertFalse(os.path.exists(self.lic_path()), "错码也写了凭证")

        d = self.sc.ok("activate", {"code": CODES[0].lower()})   # 小写粘贴也要认
        self.assertTrue(d.get("activated"), "正确码没激活：%r" % d)
        self.assertEqual(d.get("seats_used"), 1)
        self.assertEqual(d.get("seats_max"), POOL.get("seats_max", 3))

        self.assertTrue(os.path.isfile(self.lic_path()))
        rec = harness.read_json(self.lic_path())
        # §3.5 必填字段（G 另有 pool_id/serial/local_tag 扩展，不影响契约）
        for key in ("v", "code_hash", "device_hash", "seats", "seats_max", "signed_at", "sig"):
            self.assertIn(key, rec, "license.dat 缺字段 %s：%s" % (key, sorted(rec)))
        self.assertEqual(len(rec["seats"]), 1)
        self.assertTrue(rec["device_hash"].startswith("sha256:"), "设备指纹格式不符")
        self.assertTrue(rec["sig"].startswith("ed25519:"))

        if os.name == "posix":
            mode = stat.S_IMODE(os.stat(self.lic_path()).st_mode)
            self.assertEqual(mode & 0o077, 0, "license.dat 权限过宽：%o" % mode)
        else:
            rc, out = harness.sh(["icacls", self.lic_path()])
            self.assertEqual(rc, 0)
            self.assertNotIn("Everyone", out, "license.dat 对 Everyone 可见")

        self.assertEqual(self.sc.ok("get_state").get("license_state"), "activated")


class T43Idempotent(LicenseBase):
    """T-43：同设备重复激活幂等，不占第 2 个位。"""

    CASES = ["T-43"]

    def test_same_device_twice(self):
        self.sc.ok("activate", {"code": CODES[0]})
        before = harness.read_json(self.lic_path())
        d = self.sc.ok("activate", {"code": CODES[0]})
        after = harness.read_json(self.lic_path())
        self.assertEqual(d.get("seats_used"), 1, "重复激活占了第 2 个位：%r" % d)
        self.assertTrue(d.get("idempotent"))
        self.assertEqual(len(before["seats"]), len(after["seats"]))
        self.assertEqual(self.sc.ok("license_status").get("seats_used"), 1)


class T44SeatLimit(LicenseBase):
    """T-44：占满 3 台后第 4 台温和引导，不出现"授权失败"字样。"""

    CASES = ["T-44"]

    def test_fourth_device_gentle(self):
        self.sc.ok("activate", {"code": CODES[0]})
        for tag in ("b", "c"):
            r = self.sc.call("activate", {"code": CODES[0], "device_hash": h(tag)})
            self.assertTrue(r.get("ok"), "第 %s 台激活失败：%r" % (tag, r.get("error")))
        self.assertEqual(self.sc.ok("license_status").get("seats_used"), 3)

        err = self.sc.err("activate", {"code": CODES[0], "device_hash": h("d")})
        self.assertEqual(err.get("code"), "E_LICENSE_SEAT_FULL")
        self.assertTrue(err.get("recoverable"), "满席位必须可恢复（用户可释放）")
        msg = str(err.get("message") or "")
        self.assertIn("Release a seat", msg, "文案应引导 Release a seat：%r" % msg)
        for bad in ("fail", "denied", "invalid", "error", "授权失败"):
            self.assertNotIn(bad, msg.lower(), "文案出现 %r（应温和）" % bad)
        self.assertEqual(self.sc.ok("license_status").get("seats_used"), 3, "第 4 台挤掉了别人")


class T45OfflineAfterActivation(LicenseBase):
    """T-45：激活后拔网（socket 全禁）重启，全功能可用、零出网。"""

    CASES = ["T-45"]

    def test_offline_after_activation(self):
        self.sc.ok("activate", {"code": CODES[0]})
        self.sc.stop()

        guard = os.path.join(self.sc.app_data, "guard")
        os.makedirs(guard, exist_ok=True)
        with open(os.path.join(guard, "sitecustomize.py"), "w", encoding="utf-8") as f:
            f.write("import socket\n"
                    "def _deny(*a, **k):\n"
                    "    raise RuntimeError('offline (T-45)')\n"
                    "socket.socket = _deny\n"
                    "socket.create_connection = _deny\n"
                    "socket.getaddrinfo = _deny\n")
        pdf = os.path.join(self.sc.app_data, "off.pdf")
        with harness.Sidecar(app_data=self.sc.app_data, env={"PYTHONPATH": guard}) as sc:
            self.assertEqual(sc.ok("license_status").get("state"), "activated", "断网后授权丢了")
            sc.ok("diagnose", {"answers": harness.default_answers()})
            sc.ok("export_plan", {"id": harness.load_baseline()[0]["id"], "path": pdf})
            sc.ok("get_settings")
        self.assertTrue(os.path.isfile(pdf))

    def test_no_heartbeat_commands(self):
        """零心跳：命令表里不该出现 ping 之外的周期性上报类命令。"""
        self.sc.ok("activate", {"code": CODES[0]})
        for cmd in ("heartbeat", "check_license", "verify_license", "report"):
            err = self.sc.err(cmd)
            self.assertEqual(err.get("code"), "E_UNKNOWN_CMD", "%s 不该存在" % cmd)


class T41Tamper(LicenseBase):
    """G-04 附加：手改 license.dat → 判 invalid 且不锁死（同码可重新激活）。"""

    CASES = ["T-41"]

    def test_tampered_license_detected(self):
        self.sc.ok("activate", {"code": CODES[1]})
        rec = harness.read_json(self.lic_path())
        rec["seats"] = rec["seats"] * 3            # 伪造 3 个席位
        with open(self.lic_path(), "w", encoding="utf-8") as f:
            json.dump(rec, f)
        self.sc.stop()
        with harness.Sidecar(app_data=self.sc.app_data) as sc:
            self.assertIn(sc.ok("license_status").get("state"), ("invalid", "unseated"),
                          "伪造的凭证被判为有效")
            d = sc.ok("activate", {"code": CODES[1]})
            self.assertTrue(d.get("activated"), "凭证损坏后同码不能重新激活（把用户锁死了）")


if __name__ == "__main__":
    unittest.main(verbosity=2)
