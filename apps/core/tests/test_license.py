# -*- coding: utf-8 -*-
"""tests/test_license.py — 程序员 G 的单元测试（G-01 ~ G-05）

覆盖：Ed25519 正确性（RFC 8032 官方向量）、码规范化、机器指纹、激活幂等、
3 席位与第 4 台温和返回、凭证验签/篡改/损坏重建、状态回报、释放席位无后台。

测试自带临时密钥对（不读仓库里任何私钥），把公钥注入 `signature` 模块，
码池写到临时目录 —— 与被测的生产码池完全隔离。
"""

import json
import os
import secrets
import shutil
import sys
import tempfile
import unittest
from unittest import mock

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE = os.path.dirname(_HERE)
_REPO = os.path.dirname(os.path.dirname(_CORE))
sys.path.insert(0, _CORE)
sys.path.insert(0, os.path.join(_REPO, "tools"))

from license import activate as act          # noqa: E402
from license import device as dev_mod        # noqa: E402
from license import ed25519                  # noqa: E402
from license import signature as sig         # noqa: E402
import issue                                 # noqa: E402  tools/issue.py


class Ed25519VectorTest(unittest.TestCase):
    """G-02/G-04：签名实现必须与 RFC 8032 §7.1 逐字节一致，否则"签得出、验不过"。"""

    VECTORS = [
        ("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
         "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", "",
         "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
        ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
         "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", "72",
         "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
        ("c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
         "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025", "af82",
         "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac18ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a"),
    ]

    def test_rfc8032_vectors(self):
        for sk, pk, msg_hex, want_sig in self.VECTORS:
            msg = bytes.fromhex(msg_hex)
            self.assertEqual(ed25519.public_key(sk), pk)
            self.assertEqual(ed25519.sign(sk, msg), want_sig)
            self.assertTrue(ed25519.verify(want_sig, msg, pk))

    def test_rejects_tampering_and_garbage(self):
        sk, pk, msg_hex, sig_hex = self.VECTORS[0]
        self.assertFalse(ed25519.verify(sig_hex[:-2] + "00", bytes.fromhex(msg_hex), pk))
        self.assertFalse(ed25519.verify(sig_hex, b"x", pk))
        self.assertFalse(ed25519.verify("zz", b"", pk))
        self.assertFalse(ed25519.verify(sig_hex, b"", pk[:-2]))
        # 另一把钥匙的公钥不能验过
        self.assertFalse(ed25519.verify(sig_hex, b"", self.VECTORS[1][1]))


class _PoolFixture(unittest.TestCase):
    """每个测试类独立：临时 appData + 临时码池 + 临时密钥对。"""

    @classmethod
    def setUpClass(cls):
        cls.seed = secrets.token_hex(32)
        cls.pub = ed25519.public_key(cls.seed)
        cls.tmp = tempfile.mkdtemp(prefix="bizspark_lic_")

        cls.pool_path = os.path.join(cls.tmp, "pool.json")
        pool, codes = issue.build_pool(20, sig.DEFAULT_SEATS_MAX, cls.seed,
                                       "test-pool", demo=True)
        with open(cls.pool_path, "w", encoding="utf-8") as f:
            json.dump(pool, f)
        cls.codes = codes

        cls._env = mock.patch.dict(os.environ, {"BIZSPARK_APP_DATA": os.path.join(cls.tmp, "appdata")})
        cls._env.start()
        cls._prev_pub = sig.set_public_key(cls.pub)
        cls._prev_pool = act.POOL_PATH
        act.POOL_PATH = cls.pool_path
        act.load_pool(force=True)

    @classmethod
    def tearDownClass(cls):
        act.POOL_PATH = cls._prev_pool
        sig.set_public_key(cls._prev_pub)
        cls._env.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        # 每个用例清空凭证与指纹缓存，模拟"另一台新机器"
        path = act._license_path()
        if os.path.isfile(path):
            os.remove(path)
        for name in os.listdir(os.path.dirname(path)) if os.path.isdir(os.path.dirname(path)) else []:
            if name.startswith("license.dat.corrupt-"):
                os.remove(os.path.join(os.path.dirname(path), name))
        dev_mod.reset_cache()
        act.load_pool(force=True)
        self._clean_env()

    def tearDown(self):
        self._clean_env()

    def _clean_env(self):
        os.environ.pop(dev_mod.ENV_DEVICE_HASH, None)

    def _as_device(self, tag):
        """模拟另一台设备：注入一个确定性的 64 hex 指纹。"""
        h = (tag * 64)[:64]
        os.environ[dev_mod.ENV_DEVICE_HASH] = h
        return h


class CodeFormatTest(unittest.TestCase):
    """G-02：码格式与规范化（用户粘贴/小写/空格都必须能用）。"""

    def test_normalize_tolerates_user_input(self):
        body = "K7Q2M9XA7BCD"
        want = "BZSP-K7Q2-M9XA-7BCD"
        for raw in ("BZSP-K7Q2-M9XA-7BCD", "bzsp-k7q2-m9xa-7bcd",
                    " BZSP K7Q2 M9XA 7BCD ", "BZSPK7Q2M9XA7BCD",
                    "BZSP-K7Q2-M9XA-7BCD\n", '"BZSP-K7Q2-M9XA-7BCD"'):
            self.assertEqual(sig.normalize_code(raw), want, raw)

    def test_rejects_bad_codes(self):
        for raw in ("", None, 123, "BZSP-K7Q2-M9XA", "XXXX-K7Q2-M9XA-7BCD",
                    "BZSP-K7Q2-M9XA-7BCI",  # I 不在 32 字符表
                    "BZSP-K7Q2-M9XA-7BC0",  # 0 不在表内
                    "BZSP-K7Q2-M9XA-7BCDL"):
            self.assertIsNone(sig.normalize_code(raw), raw)
        self.assertFalse(sig.is_code_like("hello"))

    def test_hash_shape(self):
        code = "BZSP-K7Q2-M9XA-7BCD"
        self.assertEqual(len(sig.code_hash(code)), 16)
        self.assertEqual(sig.code_hash(code), sig.code_hash("bzspk7q2m9xa7bcd"))
        self.assertTrue(sig.full_code_hash(code).startswith("sha256:"))
        self.assertEqual(len(sig.full_code_hash(code)), 7 + 64)


class DeviceFingerprintTest(unittest.TestCase):
    """G-01：指纹稳定、只含允许分量、禁止 IP/MAC/用户名/路径。"""

    def setUp(self):
        self._env = mock.patch.dict(os.environ, {}, clear=False)
        self._env.start()
        os.environ.pop(dev_mod.ENV_DEVICE_HASH, None)
        dev_mod.reset_cache()

    def tearDown(self):
        self._env.stop()
        dev_mod.reset_cache()

    def test_stable_64_hex(self):
        a = dev_mod.compute_device_hash()
        b = dev_mod.compute_device_hash()
        self.assertEqual(a, b)
        self.assertEqual(len(a), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in a))

    def test_canonical_has_only_allowed_components(self):
        canon = dev_mod.canonical_string()
        parts = canon.split("|")
        self.assertEqual(parts[0], dev_mod.FP_VERSION)
        self.assertEqual(len(parts), 6)  # 版本 + os + 4 个硬件/系统分量
        user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
        if len(user) > 2:
            self.assertNotIn(user.lower(), canon.lower())
        self.assertNotIn("\\", canon)   # 不含文件路径
        self.assertNotIn("/users/", canon.lower())

    def test_overrides(self):
        h = "ab" * 32
        os.environ[dev_mod.ENV_DEVICE_HASH] = h
        self.assertEqual(dev_mod.device_hash(), h)
        # 上层显式传入优先于环境变量
        p = "cd" * 32
        self.assertEqual(dev_mod.device_hash({"device_hash": p}), p)
        # 非法值应被忽略，回落到自算
        self.assertEqual(dev_mod.device_hash({"device_hash": "not-a-hash"}),
                         dev_mod.device_hash())


class ActivationTest(_PoolFixture):
    """G-03 / G-04：激活、幂等、席位、凭证形态。"""

    def test_first_activation_writes_license(self):
        data, err = act.activate({"code": self.codes[0].lower()})
        self.assertIsNone(err, err)
        self.assertTrue(data["activated"])
        self.assertEqual(data["seats_used"], 1)
        self.assertEqual(data["seats_max"], 3)

        path = act._license_path()
        self.assertTrue(os.path.isfile(path))
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
        # §3.5 字段齐全
        for key in ("v", "code_hash", "device_hash", "seats", "seats_max",
                    "signed_at", "sig", "local_tag", "serial"):
            self.assertIn(key, rec)
        self.assertEqual(rec["v"], 1)
        self.assertTrue(rec["code_hash"].startswith("sha256:"))
        self.assertTrue(rec["sig"].startswith("ed25519:"))
        self.assertEqual(rec["seats_max"], 3)
        self.assertEqual(len(rec["seats"]), 1)
        self.assertRegex(rec["seats"][0]["activated_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        ok, why = act.verify_license(rec)
        self.assertTrue(ok, why)
        self.assertEqual(act.license_state(), "activated")

    @unittest.skipIf(sys.platform.startswith("win"), "Windows 无 POSIX 权限位（改用 icacls，见 _restrict_permissions）")
    def test_license_permissions_600(self):
        act.activate({"code": self.codes[0]})
        mode = os.stat(act._license_path()).st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_idempotent_same_device(self):
        first, _ = act.activate({"code": self.codes[0]})
        with open(act._license_path(), encoding="utf-8") as f:
            before = json.load(f)
        second, err = act.activate({"code": self.codes[0]})
        self.assertIsNone(err)
        self.assertTrue(second.get("idempotent"))
        self.assertEqual(second["seats_used"], 1)          # T-43：不占第 2 个位
        with open(act._license_path(), encoding="utf-8") as f:
            after = json.load(f)
        self.assertEqual(before["seats"], after["seats"])  # 席位与时间戳都不动

    def test_three_seats_then_soft_seat_full(self):
        self._as_device("a")
        d1, _ = act.activate({"code": self.codes[1]})
        self.assertEqual(d1["seats_used"], 1)
        self._as_device("b")
        d2, _ = act.activate({"code": self.codes[1]})
        self.assertEqual(d2["seats_used"], 2)
        self._as_device("c")
        d3, _ = act.activate({"code": self.codes[1]})
        self.assertEqual(d3["seats_used"], 3)

        self._as_device("d")                                # 第 4 台
        data, err = act.activate({"code": self.codes[1]})
        self.assertIsNone(data)
        self.assertEqual(err["code"], "E_LICENSE_SEAT_FULL")  # T-44
        self.assertTrue(err["recoverable"])
        msg = err["message"].lower()
        self.assertIn("release a seat", msg)                 # 必须引导释放席位
        for banned in ("fail", "error", "invalid", "授权失败", "denied"):
            self.assertNotIn(banned, msg)

        # 席位没有被偷偷改动
        rec, reason = act.read_license()
        self.assertEqual(reason, "ok")
        self.assertEqual(len(rec["seats"]), 3)

    def test_bad_codes_are_soft(self):
        cases = ["BZSP-AAAA-AAAA-AAAA", "nonsense", "", None, "BZSP-K7Q2-M9XA"]
        for code in cases:
            data, err = act.activate({"code": code} if code is not None else {})
            self.assertIsNone(data, code)
            self.assertEqual(err["code"], "E_LICENSE_BAD_CODE", code)
            msg = err["message"].lower()
            for banned in ("fail", "error", "授权失败"):
                self.assertNotIn(banned, msg)
        self.assertEqual(act.license_state(), "none")

    def test_status_before_and_after(self):
        before, err = act.license_status({})
        self.assertIsNone(err)
        self.assertFalse(before["activated"])
        self.assertEqual(before["state"], "none")
        self.assertIsNone(before["seats_used"])     # B 的 UI 用 null 显示"激活后显示席位"
        self.assertEqual(before["seats_max"], 3)

        act.activate({"code": self.codes[2]})
        after, _ = act.license_status({})
        self.assertTrue(after["activated"])
        self.assertEqual(after["seats_used"], 1)
        self.assertEqual(after["state"], "activated")

    def test_release_seat_is_manual(self):
        self._as_device("a")
        act.activate({"code": self.codes[3]})
        data, err = act.release_seat({})
        self.assertIsNone(err)
        self.assertFalse(data["released"])
        self.assertTrue(data["manual"])
        self.assertIn("@", data["support_email"])
        rec, _ = act.read_license()
        self.assertEqual(len(rec["seats"]), 1)   # 不自助删席位（G-05：无后台、无账号）

    def test_license_copied_to_another_device_is_unseated(self):
        self._as_device("a")
        act.activate({"code": self.codes[4]})
        self._as_device("b")                            # 换了台机器，文件被拷过来
        self.assertEqual(act.license_state(), "unseated")
        st, _ = act.license_status({})
        self.assertFalse(st["activated"])
        self.assertEqual(st["seats_used"], 1)
        # 真码可以继续激活（占第 2 个位），不会被锁死
        data, err = act.activate({"code": self.codes[4]})
        self.assertIsNone(err)
        self.assertEqual(data["seats_used"], 2)

    def test_tampered_seats_rejected_then_reactivation_allowed(self):
        code = self.codes[5]
        act.activate({"code": code})
        path = act._license_path()
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
        rec["seats"].append({"device_hash": "sha256:" + "ff" * 32,
                             "activated_at": "2026-01-01T00:00:00Z"})
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f)

        ok, why = act.verify_license(rec)
        self.assertFalse(ok)
        self.assertEqual(why, "local_tag")
        self.assertEqual(act.license_state(), "invalid")
        rec2, reason = act.read_license()
        self.assertIsNone(rec2)
        self.assertEqual(reason, "unreadable")

        # 允许重新输入同一码，损坏文件留档
        data, err = act.activate({"code": code})
        self.assertIsNone(err)
        self.assertEqual(data["seats_used"], 1)
        base = os.path.dirname(path)
        self.assertTrue(any(n.startswith("license.dat.corrupt-") for n in os.listdir(base)))

    def test_corrupt_json_rebuilds(self):
        self._as_device("a")
        act.activate({"code": self.codes[6]})
        with open(act._license_path(), "w", encoding="utf-8") as f:
            f.write("{not json")
        self.assertEqual(act.license_state(), "invalid")
        data, err = act.activate({"code": self.codes[6]})
        self.assertIsNone(err)
        self.assertTrue(data["activated"])

    def test_forged_signature_rejected(self):
        act.activate({"code": self.codes[7]})
        path = act._license_path()
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
        rec["sig"] = "ed25519:" + "00" * 64      # 换成自造签名
        self.assertFalse(act.verify_license(rec)[0])
        # 换个假 serial 也过不了背书
        rec2 = dict(rec, serial="AAAAA")
        self.assertFalse(act.verify_license(rec2)[0])

    def test_missing_pool_is_soft(self):
        prev = act.POOL_PATH
        act.POOL_PATH = os.path.join(self.tmp, "no-such-pool.json")
        try:
            act.load_pool(force=True)
            data, err = act.activate({"code": self.codes[0]})
            self.assertIsNone(data)
            self.assertEqual(err["code"], "E_LICENSE_BAD_CODE")
        finally:
            act.POOL_PATH = prev
            act.load_pool(force=True)

    def test_tampered_pool_rejected(self):
        with open(self.pool_path, encoding="utf-8") as f:
            pool = json.load(f)
        bad = json.loads(json.dumps(pool))
        bad["codes"][0]["s"] = "AAAAA"          # 改一条，池签名就失效
        self.assertFalse(sig.verify_pool_header(bad))
        bad2 = json.loads(json.dumps(pool))
        bad2["seats_max"] = 9                    # 想把自己的席位数放大
        self.assertFalse(sig.verify_pool_header(bad2))


class IpcIntegrationTest(_PoolFixture):
    """§2.4 契约：cmd 名、返回字段与 B 的 Activate.vue 对齐。"""

    def test_cmd_payload_contract(self):
        # B 的 activate(code) 只传 code；license_status() 无 payload
        self.assertTrue(callable(act.activate))
        data, err = act.activate({"code": self.codes[8]})
        self.assertIsNone(err)
        for key in ("activated", "seats_used", "seats_max"):
            self.assertIn(key, data)       # Activate.vue 直接读这三个
        st, _ = act.license_status(None)   # payload 缺失也不能崩
        self.assertTrue(st["activated"])

    def test_no_network(self):
        import socket
        real = socket.socket

        def boom(*a, **k):
            raise AssertionError("license 流程绝不能开 socket（T-45 零出网）")

        socket.socket = boom
        try:
            data, err = act.activate({"code": self.codes[0]})
            self.assertIsNone(err)
            self.assertTrue(data["activated"])
            act.license_status({})
            act.release_seat({})
        finally:
            socket.socket = real

    def test_source_has_no_network_or_secret(self):
        """静态兜底：授权模块不引入任何联网/签名私钥材料。"""
        base = os.path.dirname(act.__file__)
        for name in ("activate.py", "device.py", "signature.py", "ed25519.py"):
            with open(os.path.join(base, name), encoding="utf-8") as f:
                src = f.read().lower()
            for banned in ("import socket", "import urllib", "import requests",
                           "http://", "https://", "urlopen"):
                self.assertNotIn(banned, src, "%s 含 %s" % (name, banned))
            self.assertNotIn("private", src.replace("private_key", "").replace(
                "私钥", "").replace("never ship", ""), "%s 不该出现私钥材料" % name)

    def test_unknown_code_does_not_touch_state(self):
        act.activate({"code": self.codes[9]})
        with open(act._license_path(), "rb") as f:
            before = f.read()
        act.activate({"code": "BZSP-2222-3333-4444"})
        with open(act._license_path(), "rb") as f:
            after = f.read()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
