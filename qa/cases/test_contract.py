"""test_contract.py — 契约漂移巡检（负责人：H）

不对应具体 T 编号，专门抓"功能都对、契约悄悄变了"的问题：
§2.4 命令表覆盖、附录 D 错误码表、V-10 键集合、价格槽、界面文案唯一来源。
这些不过不算某人的用例失败，但必须在报告里点名。
"""

from __future__ import annotations

import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness  # noqa: E402

DOC = harness.REPO / "docs" / "BizSpark_开发执行版需求文档V2.0.md"
WEB = harness.REPO / "apps" / "web"
CORE = harness.CORE

# §2.4 命令表（正名，不含早期脚手架别名）
CMDS = [
    ("get_state", {}), ("save_answers", {"answers": {}}), ("diagnose", {"answers": {}}),
    ("get_idea", {"id": "x"}), ("export_plan", {"id": "x", "path": ""}), ("export_csv", {"id": "x", "path": ""}),
    ("save_idea", {"id": "x"}), ("list_saved", {}), ("clear_saved", {}),
    ("compare_ideas", {"ids": []}), ("get_settings", {}), ("set_settings", {"patch": {}}),
    ("check_library", {}), ("apply_delta", {}), ("activate", {"code": ""}),
    ("license_status", {}), ("release_seat", {}), ("log_crash", {"code": "E_X", "version": "1.0.0"}),
]

# 附录 D 错误码表（用户可见的只允许这几个）
# D-09 契约修订（PM，2026-11-13）：运行期实际在用的 6 码正式收编进附录 D
APPENDIX_D = {
    "E_CORE_DOWN", "E_STATE_CORRUPT", "E_LIBRARY_FALLBACK", "E_ENGINE_NO_MATCH",
    "E_FS_READONLY", "E_PDF_RENDER", "E_LICENSE_SEAT_FULL", "E_LICENSE_BAD_CODE",
    "E_DELTA_INVALID", "E_MANIFEST_FAIL", "E_UNKNOWN_CMD",
    "E_INTERNAL", "E_IDEA_NOT_FOUND", "E_EXPORT_CANCELLED",
    "E_CSV_WRITE", "E_PDF_WRITE", "E_LIBRARY_WRITE",
}


class CmdCoverage(unittest.TestCase):
    """§2.4 的 18 条正名 cmd 都必须有 handler（不许再回 E_UNKNOWN_CMD）。"""

    CASES = []

    def test_all_cmds_registered(self):
        with harness.Sidecar() as sc:
            missing = []
            for cmd, payload in CMDS:
                r = sc.call(cmd, payload)
                code = (r.get("error") or {}).get("code")
                if code == "E_UNKNOWN_CMD":
                    missing.append(cmd)
            self.assertFalse(missing, "这些 cmd 没有 handler：%s" % missing)

    def test_unknown_cmd_is_recoverable(self):
        with harness.Sidecar() as sc:
            err = sc.err("definitely_not_a_cmd")
            self.assertEqual(err.get("code"), "E_UNKNOWN_CMD")
            self.assertTrue(err.get("recoverable"))

    def test_bad_json_line_does_not_crash(self):
        with harness.Sidecar() as sc:
            for bad in ('[1,2,3]', '"just a string"', 'null', '42'):
                r = sc.raw_line(bad)
                self.assertIsNotNone(r, "sidecar 对 %r 没有响应" % bad)
                self.assertFalse(r.get("ok"), "%r 竟然被当成合法请求" % bad)
            self.assertTrue(sc.alive(), "脏行让 sidecar 崩了")
            self.assertTrue(sc.ok("ping").get("pong"))


class ErrorCodeDrift(unittest.TestCase):
    """实现里出现的错误码必须都在附录 D 里，或多出来的要登记豁免。"""

    CASES = []

    # 已登记的扩展码（H 与负责人确认后加入）：code -> 说明
    REGISTERED_EXTRA = {
        "E_BAD_REQUEST": "请求体不合法（F 加的类型守卫，等价 400）",
        "E_NOT_IMPLEMENTED": "早期脚手架占位（已无 cmd 命中）",
    }

    def _codes(self) -> dict[str, list[str]]:
        found: dict[str, list[str]] = {}
        for root, dirs, files in os.walk(CORE):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "tests")]
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(root, name)
                for n, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
                    for m in re.finditer(r'"(E_[A-Z_]+)"', line):
                        found.setdefault(m.group(1), []).append(
                            "%s:%d" % (os.path.relpath(path, harness.REPO), n))
        return found

    def test_only_documented_codes(self):
        found = self._codes()
        unknown = {k: v for k, v in found.items()
                   if k not in APPENDIX_D and k not in self.REGISTERED_EXTRA}
        self.assertFalse(unknown, "出现附录 D 之外的错误码（契约漂移）：%s" % unknown)


class LocaleParity(unittest.TestCase):
    """V-10：中英键集合差集为 0；中文不译白名单；无语言切换键与控件。"""

    CASES = []

    def test_key_parity(self):
        en = harness.locales("en-US")
        zh = harness.locales("zh-CN")
        only_en = sorted(set(en) - set(zh))
        only_zh = sorted(set(zh) - set(en))
        self.assertEqual(only_en, [], "zh-CN 缺键：%s" % only_en[:10])
        self.assertEqual(only_zh, [], "zh-CN 多键：%s" % only_zh[:10])
        self.assertGreaterEqual(len(en), 200)

    def test_no_language_switch(self):
        for lang in ("en-US", "zh-CN"):
            d = harness.locales(lang)
            hits = [k for k in d if "locale.switch" in k or "language.switch" in k]
            self.assertFalse(hits, "%s 出现语言切换键：%s" % (lang, hits))
        for path in (WEB / "src").rglob("*.vue"):
            text = path.read_text(encoding="utf-8", errors="replace")
            self.assertNotRegex(text, r"<select[^>]*lang|language\s*switch",
                                "%s 出现语言切换控件" % path.name)

    def test_zh_keeps_brand_terms(self):
        """白名单词只在"英文原文出现过"的键上要求中文保留（不译），逐键比对。"""
        en = harness.locales("en-US")
        zh = harness.locales("zh-CN")
        keep = ("BizSpark", "Microsoft Store", "Mac App Store", "PDF", "CSV", "AI",
                "Google Maps", "Yelp", "Etsy", "Shopify", "Nextdoor")
        missing = []
        for k, v in en.items():
            for term in keep:
                if term in str(v) and term not in str(zh.get(k, "")):
                    missing.append("%s 的 %r 被译掉了：%r" % (k, term, zh.get(k)))
        self.assertFalse(missing, "白名单词被翻译：%s" % missing[:6])


class PriceSlots(unittest.TestCase):
    """T-59 结构前提：4 个价格槽都在，文案不含金额。"""

    CASES = []

    SLOTS = ("hero-trust", "hero-foot", "export-note", "activate-eyebrow")

    def test_four_slots_present(self):
        blob = ""
        for path in (WEB / "src").rglob("*.vue"):
            blob += path.read_text(encoding="utf-8", errors="replace")
        for slot in self.SLOTS:
            self.assertIn('data-price-slot="%s"' % slot, blob, "缺价格槽 %s" % slot)

    def test_hidden_copy_has_no_amount(self):
        en = harness.locales("en-US")
        price_keys = {k: v for k, v in en.items() if k.startswith("price.")}
        self.assertTrue(price_keys, "locales 里没有 price.* 键")
        for k, v in price_keys.items():
            if "{" in str(v):
                continue      # visible 模板用 {amount} 占位，允许
            self.assertNotRegex(str(v), r"\$\s?\d", "%s 写死了金额：%r" % (k, v))


class UiCopySource(unittest.TestCase):
    """§12.2：界面文案只在 locales；业务层不写字符串。"""

    CASES = []

    def test_no_hardcoded_copy_in_views(self):
        offenders = []
        for path in (WEB / "src" / "views").rglob("*.vue"):
            text = path.read_text(encoding="utf-8", errors="replace")
            body = re.sub(r"<style.*?</style>", "", text, flags=re.S)
            body = re.sub(r"<script.*?</script>", "", body, flags=re.S)
            for m in re.finditer(r">\s*([A-Z][A-Za-z ,.'’\-]{8,})\s*<", body):
                offenders.append("%s: %r" % (path.name, m.group(1)[:40]))
        self.assertFalse(offenders, "视图里写死了文案（应走 locales）：%s" % offenders[:6])


if __name__ == "__main__":
    unittest.main(verbosity=2)
