"""test_packaging.py — T-42、T-55、T-56、T-58（负责人：H）

只判"仓库里能判"的部分：Store 构建裁剪、六目标命名、提审材料齐备。
需要真包/真机的 T-49…T-52、T-54、T-57 见 qa/reports/release-checklist.md（逐条手工步骤）。
"""

from __future__ import annotations

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness  # noqa: E402

WEB = harness.REPO / "apps" / "web"
CORE = harness.CORE


def _strip_report() -> tuple[int, str]:
    """G 的裁剪校验：真删 license/ 再跑一遍业务 cmd。"""
    return harness.sh([sys.executable, str(harness.REPO / "qa" / "security" / "store_strip_check.py")],
                      timeout=300)


class T42StoreBackendStripped(unittest.TestCase):
    """T-42（后端侧）：裁掉 license/ 后授权 cmd 消失、业务 cmd 正常、进程不崩。"""

    CASES = ["T-42"]

    def test_backend_strippable(self):
        rc, out = _strip_report()
        self.assertEqual(rc, 0, "Store 裁剪校验未通过：\n%s" % out[-2000:])
        self.assertIn("PASS", out.upper())

    def test_license_module_isolated(self):
        """除 license/ 自身、测试与 main.py 的守卫导入外，任何模块都不许 import license。"""
        offenders = []
        for root, dirs, files in os.walk(CORE):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "license", "tests")]
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(root, name)
                for n, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
                    if re.match(r"^\s*(from|import)\s+license\b", line):
                        if line[:1] in (" ", "\t"):     # 缩进 = 写在 try/except 里，裁掉目录可降级
                            continue
                        offenders.append("%s:%d" % (os.path.relpath(path, harness.REPO), n))
        self.assertFalse(offenders, "这些文件裸 import 了 license，Store 版裁不干净：%s" % offenders)


class T42StoreFrontend(unittest.TestCase):
    """T-42（前端侧）：Store 构建产物不得包含 /activate 路由与视图。"""

    CASES = ["T-42"]

    def test_frontend_has_store_build_mode(self):
        pkg = harness.read_json(WEB / "package.json")
        scripts = pkg.get("scripts") or {}
        self.assertTrue(any("store" in k.lower() for k in scripts),
                        "package.json 没有 build:store 之类脚本，Store 包必然带 Activate 页：%s"
                        % sorted(scripts))
        router = (WEB / "src" / "router.ts").read_text(encoding="utf-8")
        self.assertRegex(router, r"(STORE|store)",
                         "router.ts 没有编译期裁剪标记（/activate 会进 Store 包）")


class T55StorePackages(unittest.TestCase):
    """T-55：Store 两个包检索 activate/license/updater 零命中（独立留痕）。"""

    CASES = ["T-55"]

    def test_stripped_build_rejects_license_cmds(self):
        """自己再裁一次（不依赖 G 的脚本输出格式）：三个授权 cmd 必须变成 E_UNKNOWN_CMD。"""
        import shutil
        import tempfile
        tmp = tempfile.mkdtemp(prefix="bz_strip_")
        try:
            core = os.path.join(tmp, "core")
            shutil.copytree(CORE, core, ignore=shutil.ignore_patterns("__pycache__", "license"))
            self.assertFalse(os.path.isdir(os.path.join(core, "license")))
            with harness.Sidecar(script=os.path.join(core, "main.py")) as sc:
                for cmd in ("activate", "license_status", "release_seat"):
                    err = sc.err(cmd, {"code": "BZSP-2222-3333-4444"})
                    self.assertEqual(err.get("code"), "E_UNKNOWN_CMD",
                                     "裁掉 license/ 后 %s 仍然存在：%r" % (cmd, err))
                # 业务功能不受影响
                d = sc.ok("diagnose", {"answers": harness.default_answers()})
                self.assertTrue(1 <= len(d["ideas"]) <= 3)
                st = sc.ok("get_state")
                self.assertIn("license_state", st)
                self.assertIn(st.get("license_state"), ("none", "unseated", None, ""))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_web_bundle_has_no_updater_path(self):
        hits = []
        for path in (WEB / "src").rglob("*"):
            if path.is_file() and path.suffix in (".ts", ".vue", ".js"):
                text = path.read_text(encoding="utf-8", errors="replace")
                if re.search(r"@tauri-apps/plugin-updater", text) or \
                        re.search(r"(invoke|call)\s*[(\"'][^\n]{0,40}(update|updater)", text, re.I):
                    hits.append(str(path.relative_to(WEB)))
        self.assertFalse(hits, "前端存在真实更新调用路径（Store 包必须零命中）：%s" % hits)


class T56ArtifactNaming(unittest.TestCase):
    """T-56：六构建目标命名可区分，包体红线与签名策略明确。"""

    CASES = ["T-56"]

    TARGETS = ("store-win-en", "store-mac-en", "reseller-win-en", "reseller-mac-en",
               "selfcheck-cn-win", "selfcheck-cn-mac")

    def test_six_targets_declared(self):
        text = (harness.REPO / "scripts" / "inject-pricing.sh").read_text(encoding="utf-8", errors="replace")
        missing = [t for t in self.TARGETS if t not in text]
        self.assertFalse(missing, "注入脚本缺构建目标：%s" % missing)

    def test_size_gate_and_signing_policy(self):
        pack = (harness.REPO / "scripts" / "pack.sh").read_text(encoding="utf-8", errors="replace")
        self.assertRegex(pack, r"80", "pack.sh 没有 80MB 包体红线")
        sign = (harness.REPO / "scripts" / "sign.sh").read_text(encoding="utf-8", errors="replace")
        self.assertRegex(sign, r"(未配置|skip|跳过)", "sign.sh 没有「无证书时跳过」的明确分支")
        cn = (harness.REPO / "scripts" / "build-cn.sh").read_text(encoding="utf-8", errors="replace")
        self.assertIn("selfcheck", cn, "build-cn.sh 未把自检包标识为 selfcheck 目标")


class T58StoreMaterials(unittest.TestCase):
    """T-58：提审材料齐备（图标变体 / 隐私政策 / 5 条商品页文案 / 支持邮箱 / 仅英文截图）。"""

    CASES = ["T-58"]

    def setUp(self) -> None:
        self.assets = harness.REPO / "qa" / "store-assets"

    def test_icon_variants(self):
        icons = sorted((self.assets / "icon").glob("*.png")) if (self.assets / "icon").is_dir() else []
        sizes = {harness.png_size(str(p)) for p in icons}
        for need in ((1024, 1024), (512, 512), (256, 256)):
            self.assertIn(need, sizes, "缺图标尺寸 %s，现有 %s" % (need, sorted(sizes)))

    def test_privacy_and_support(self):
        privacy = self.assets / "privacy-policy.md"
        self.assertTrue(privacy.is_file(), "缺隐私政策一页")
        text = privacy.read_text(encoding="utf-8").lower()
        for token in ("data", "local", "device"):
            self.assertIn(token, text)

        page = self.assets / "product-page.md"
        self.assertTrue(page.is_file(), "缺商品页文案")
        body = page.read_text(encoding="utf-8")
        for line in ("One-time purchase", "No subscription", "No auto-renewal",
                     "Works offline", "Your data stays on this device"):
            self.assertIn(line, body, "商品页缺必写句：%s" % line)
        self.assertRegex(body, r"[\w.+-]+@[\w-]+\.[\w.]+", "商品页没有支持邮箱")

    def test_screenshots_english_only(self):
        en_dir = self.assets / "screenshots" / "en"
        shots = sorted(en_dir.glob("*.png")) if en_dir.is_dir() else []
        self.assertGreaterEqual(len(shots), 9, "英文截图不足 9 张：%d" % len(shots))
        cn_dir = self.assets / "screenshots" / "cn"
        cn_shots = list(cn_dir.glob("*.png")) if cn_dir.is_dir() else []
        self.assertFalse(cn_shots, "商店素材里出现中文截图（F14.3 明令禁止）：%s" % cn_shots[:3])

    def test_no_price_in_store_assets(self):
        pattern = re.compile(r"(\$[1-9][0-9,]*(\.[0-9]{1,2})?|USD ?[0-9][0-9,]*"
                             r"|[0-9][0-9,]*(\.[0-9]{1,2})? ?USD)")
        hits = []
        for path in self.assets.rglob("*"):
            if path.is_file() and path.suffix.lower() in (".md", ".txt", ".json", ".html", ".csv"):
                for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if pattern.search(line):
                        hits.append("%s:%d %s" % (path.name, n, line.strip()[:60]))
        self.assertFalse(hits, "商店素材出现金额：%s" % hits[:5])


if __name__ == "__main__":
    unittest.main(verbosity=2)
