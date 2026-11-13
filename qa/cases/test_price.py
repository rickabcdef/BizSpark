"""test_price.py — T-59 ①：全项目零商品售价硬编码（负责人：H / A 修脚本）

判定边界（需求文档 §4 P-14、§9 T-59 原话）：
  - 商品售价 = 软件本身的卖价，只能由 config/pricing.json → inject-pricing 渲染
  - **商机内容金额不计**（baseline 的 cost_breakdown / pricing_hint、问卷选项的
    资金档标签、UI 稿里的示例数据都属于内容数据）

所以本用例做两遍扫描：
  1) 严格版（与 scripts/check-no-price.sh 同规则）= 现状，命中内容数据也要报出来；
  2) 文档边界版（排除内容数据文件）= 真正的判定。
两个数字都写进报告，避免"改脚本放水"式的假绿。
"""

from __future__ import annotations

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness  # noqa: E402

PATTERN = re.compile(r"(\$[1-9][0-9,]*(\.[0-9]{1,2})?|USD ?[0-9][0-9,]*"
                     r"|[0-9][0-9,]*(\.[0-9]{1,2})? ?USD)")

SCAN_DIRS = ("apps", "config", "scripts", "qa", "content", "hosting")
EXTS = (".html", ".css", ".js", ".ts", ".vue", ".json", ".py", ".rs", ".md", ".sh", ".toml")
SKIP_DIRS = ("node_modules", "target", "dist", "__pycache__", ".git", "screenshots")

# 内容数据：商机库、问卷资金档标签、UI 稿示例、测试夹具/用例登记表
CONTENT_DATA = (
    "apps/core/data/",            # baseline / fallback / fx（商机内容）
    "apps/core/tests/",           # C 的夹具与单测（内容金额）
    "apps/core/engine/quiz.py",   # 问卷资金档标签（CAPITAL_LABELS，内容数据）
    "apps/web/src/locales/",      # 问卷资金档与 mock 卡片文案（内容数据，非商品售价）
    "content/",                   # D 的内容生产源
    "ui/",                        # UI 交付源稿
    "qa/cases/cases.json",        # 用例登记表（引述 UI 文案）
    "qa/cases/registry.py",       # 同上
    "qa/content-review.md",       # 抽检报告（引述内容）
    "qa/reports/",                # 报告（含内容金额样本）
    "docs/",                      # 需求文档（含示例金额）
    "hosting/delta_",             # delta 里的新增商机内容
)


def _iter_files():
    for d in SCAN_DIRS:
        base = harness.REPO / d
        if not base.is_dir():
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for name in files:
                if name.endswith(EXTS):
                    yield os.path.join(root, name)
    for name in os.listdir(harness.REPO):
        if name.endswith(".md"):
            yield str(harness.REPO / name)


def scan(exclude_content: bool) -> list[str]:
    hits = []
    for path in _iter_files():
        rel = os.path.relpath(path, harness.REPO).replace("\\", "/")
        if exclude_content and any(rel.startswith(p) for p in CONTENT_DATA):
            continue
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if PATTERN.search(line):
                hits.append("%s:%d %s" % (rel, n, line.strip()[:70]))
    return hits


class T59NoHardcodedPrice(unittest.TestCase):
    """T-59 ①：交付物零商品售价硬编码（内容数据不计）。"""

    CASES = ["T-59"]

    def test_strict_scan_matches_gate_script(self):
        """与 check-no-price.sh 同口径的结果——只用于记录现状，不作为判定。"""
        hits = scan(exclude_content=False)
        print("\n[T-59] 严格扫描命中 %d 处（含内容数据）" % len(hits))
        for h in hits[:10]:
            print("   ", h)

    def test_no_price_outside_content_data(self):
        hits = scan(exclude_content=True)
        self.assertFalse(hits, "内容数据之外出现商品售价硬编码（%d 处）：\n%s"
                         % (len(hits), "\n".join(hits[:10])))

    def test_pricing_config_is_single_source(self):
        cfg = harness.read_json(harness.REPO / "config" / "pricing.json")
        self.assertIn(cfg.get("display_mode"), ("hidden", "visible"))
        self.assertEqual(cfg.get("currency"), "USD")
        self.assertIn(cfg.get("model"), ("one-time", "monthly", "yearly", "seat"))
        if cfg.get("display_mode") == "hidden":
            self.assertIsNone(cfg.get("amount"), "hidden 态 amount 必须为 null")

    def test_inject_script_covers_six_targets(self):
        text = (harness.REPO / "scripts" / "inject-pricing.sh").read_text(encoding="utf-8", errors="replace")
        for t in ("store-win-en", "store-mac-en", "reseller-win-en", "reseller-mac-en",
                  "selfcheck-cn-win", "selfcheck-cn-mac"):
            self.assertIn(t, text, "注入脚本缺目标 %s" % t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
