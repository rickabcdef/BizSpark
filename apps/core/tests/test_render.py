# -*- coding: utf-8 -*-
"""test_render — E 任务卡单元测试（E-01…E-07、E-09；新增文件，不改 C 的 test_engine.py）

验收用例映射：
- E-01 §3.4 三个派生字段
- E-02 4 卡顺序写死、不加第五张卡、定价/合规不进 cards（T-21）
- E-03 单页 A4/Letter 自适应、9 块顺序（T-25/T-26）
- E-04 无水印/无 URL（pdftotext 校验降级为 PDF 流关键字校验）
- E-05 返回 {filename, bytes, pages:1, path}（T-27/T-33）
- E-06 脏字段兜底、无 undefined（T-32）
- E-07 CSV 三列（列正确）
- E-09 导出 ≤2s（F14.1）
"""

import io
import json
import os
import sys
import time
import unittest
import zlib

_CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # apps/core
sys.path.insert(0, _CORE)

from render import detail as rd            # noqa: E402
from render.pdf import export_plan         # noqa: E402
from render.csv import export_csv, CSV_HEADERS, csv_rows  # noqa: E402


def _first_idea_id():
    path = os.path.join(_CORE, "data", "baseline_v1.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    ideas = data if isinstance(data, list) else data.get("ideas")
    return ideas[0]["id"]


def _detail():
    from engine import get_idea
    detail, err = get_idea({"id": _first_idea_id()})
    assert err is None, err
    return detail


def _pdf_text(raw):
    """无 pdftotext 环境下的降级校验：解出 PDF 内容流拼出可见文本。

    reportlab 默认 ASCII85Decode + FlateDecode；也兼容裸 zlib / 未压缩流。
    """
    import re
    import base64
    chunks = []
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", raw, re.S):
        body = m.group(1).rstrip(b"\r\n")
        data = None
        try:
            data = zlib.decompress(base64.a85decode(body, adobe=True))  # A85+Flate
        except Exception:
            try:
                data = zlib.decompress(body)                            # 裸 Flate
            except Exception:
                data = body                                             # 未压缩
        chunks.append(data.decode("latin-1", "ignore"))
    return "\n".join(chunks)


class TestDetailAssembly(unittest.TestCase):
    """E-01 / E-06"""

    def setUp(self):
        self.detail = _detail()

    def test_e01_derived_fields(self):
        for key in ("cost_total", "cost_rows", "payback_hint"):
            self.assertIn(key, self.detail, "§3.4 派生字段缺失: %s" % key)
        self.assertIsInstance(self.detail["cost_total"], float)
        self.assertTrue(all("item" in r and "amount" in r for r in self.detail["cost_rows"]))

    def test_e06_dirty_pitfalls_fallback(self):
        dirty = dict(self.detail)
        dirty["pitfalls"] = dirty["pitfalls"][:1]  # 脏数据：缺第 3 条（T-32 主用例）
        cards = rd.build_cards(dirty)
        pit = next(c for c in cards if c["key"] == "pitfalls")
        self.assertEqual(len(pit["items"]), 3)
        self.assertIn(rd.FALLBACK_PITFALL, pit["items"])

    def test_e06_no_undefined(self):
        dirty = {"title": None, "one_liner": "undefined", "steps": [None, ""],
                 "pitfalls": [], "first_customers": None, "cost_rows": [],
                 "cost_breakdown": [], "compliance_note": 123, "payback_hint": None}
        blob = json.dumps(rd.build_pdf_view(dirty), ensure_ascii=False)
        for bad in ("undefined", "None", "null"):
            self.assertNotIn(bad, blob, "渲染视图出现 %s" % bad)
        self.assertEqual(len(rd.build_pdf_view(dirty)["steps"]), 7)
        self.assertEqual(len(rd.build_pdf_view(dirty)["pitfalls"]), 3)

    def test_e06_long_text_clipped(self):
        dirty = dict(self.detail)
        dirty["one_liner"] = "x" * 5000
        self.assertLessEqual(len(rd.sanitize(dirty)["one_liner"]), rd.MAX_TEXT + 1)
        self.assertTrue(rd.sanitize(dirty)["one_liner"].endswith("…"))


class TestCards(unittest.TestCase):
    """E-02（T-21：4 卡顺序照 DOM，无第五张卡）"""

    def setUp(self):
        self.cards = rd.build_cards(_detail())

    def test_four_cards_fixed_order(self):
        self.assertEqual([c["key"] for c in self.cards], list(rd.CARD_ORDER))

    def test_no_pricing_or_compliance_card(self):
        blob = json.dumps(self.cards)
        self.assertNotIn("pricing_hint", blob)
        self.assertNotIn("compliance_note", blob)

    def test_costs_card_has_orange_total_row(self):
        costs = self.cards[0]
        self.assertEqual(costs["total_label"], "Total to first invoice")
        self.assertTrue(costs["total_value"])


class TestPdfExport(unittest.TestCase):
    """E-03 / E-04 / E-05 / E-08 / E-09"""

    def setUp(self):
        self.detail = _detail()
        self.out = os.path.join(os.environ.get("TEMP", "/tmp"),
                                "bizspark_e_test_%d.pdf" % os.getpid())

    def tearDown(self):
        if os.path.exists(self.out):
            os.remove(self.out)

    def _export(self, payload):
        data, err = export_plan(payload)
        self.assertIsNone(err, err)
        return data

    def test_e05_return_shape_and_pages_one(self):
        started = time.perf_counter()
        data = self._export({"id": self.detail["id"], "path": self.out})
        elapsed = time.perf_counter() - started
        self.assertEqual(data["pages"], 1)                      # T-27
        self.assertEqual(data["filename"], os.path.basename(self.out))
        self.assertEqual(data["bytes"], os.path.getsize(self.out))
        self.assertTrue(os.path.exists(data["path"]))
        self.assertLess(elapsed, 2.0, "E-09 导出红线 ≤2s")       # F14.1
        self.assertLess(data["elapsed_ms"], 2000)

    def test_e03_letter_also_single_page(self):
        data = self._export({"id": self.detail["id"], "path": self.out, "paper": "Letter"})
        self.assertEqual(data["pages"], 1)

    def test_e04_no_url_watermark_and_fixed_footer(self):
        self._export({"id": self.detail["id"], "path": self.out})
        with open(self.out, "rb") as f:
            raw = f.read()
        self.assertTrue(raw.startswith(b"%PDF"))
        text = _pdf_text(raw)
        self.assertNotIn("http://", text)                       # T-26 无在线链接
        self.assertNotIn("https://", text)
        for kw in ("Total to first invoice", "First 7 steps", "Pricing"):
            self.assertIn(kw, text, "PDF 缺内容块: %s" % kw)
        self.assertIn("one-time purchase", text)                # 固定页脚
        self.assertIn("One-page plan", text)                    # 页眉

    def test_e08_cancelled_and_unwritable(self):
        data, err = export_plan({"id": self.detail["id"], "path": ""})
        self.assertIsNone(data)
        self.assertEqual(err["code"], "E_EXPORT_CANCELLED")     # T-34 取消 → 前端静默
        self.assertTrue(err["recoverable"])
        # 目录不可写 → 只换文件夹提示（Windows 下用不存在的盘符模拟）
        data, err = export_plan({"id": self.detail["id"],
                                 "path": "Q:\\no\\such\\dir\\plan.pdf"})
        self.assertIsNone(data)
        self.assertEqual(err["code"], "E_PDF_WRITE")
        self.assertIn("Choose another folder", err["message"])

    def test_e09_long_content_single_page(self):
        """E-03 自适应：超长内容也必须压进 1 页。"""
        dirty = dict(self.detail)
        dirty["one_liner"] = "long " * 300
        dirty["steps"] = ["step number %d with plenty of words " % i * 5 for i in range(7)]
        view = rd.build_pdf_view(dirty)
        view["_path"] = self.out
        from render.pdf import render_pdf
        tmp, pages, _ = render_pdf(view, paper="A4")
        self.assertEqual(pages, 1)
        os.remove(tmp)


class TestCsvExport(unittest.TestCase):
    """E-07"""

    def setUp(self):
        self.detail = _detail()
        self.out = os.path.join(os.environ.get("TEMP", "/tmp"),
                                "bizspark_e_csv_%d" % os.getpid())

    def tearDown(self):
        pdf_like = self.out + ".pdf"
        for p in (os.path.join(self.out, "sample-costs.csv"), pdf_like):
            if os.path.exists(p):
                os.remove(p)

    def test_csv_three_columns(self):
        import csv as _csv
        os.makedirs(self.out, exist_ok=True)
        data, err = export_csv({"id": self.detail["id"],
                                "path": os.path.join(self.out, "plan.pdf")})
        self.assertIsNone(err, err)
        self.assertTrue(data["file_name"].endswith("-costs.csv"))
        with open(data["path"], encoding="utf-8-sig") as f:
            rows = list(_csv.reader(f))
        self.assertEqual(rows[0], CSV_HEADERS)                  # 列正确：item, amount, currency
        for r in rows[1:]:
            self.assertEqual(len(r), 3)
            float(r[1])  # amount 是数值
        self.assertTrue(rows[1][2])

    def test_csv_rows_shape(self):
        rows = csv_rows(self.detail)
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(set(r.keys()), set(CSV_HEADERS))

    def test_csv_cancelled(self):
        data, err = export_csv({"id": self.detail["id"], "path": ""})
        self.assertEqual(err["code"], "E_EXPORT_CANCELLED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
