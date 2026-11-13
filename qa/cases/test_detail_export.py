"""test_detail_export.py — T-21、T-23、T-24、T-26、T-27、T-32、T-33、T-34（负责人：H）

后端可判的部分全在这里；屏幕观感（T-19/T-20/T-21 顺序/T-22/T-24 全文/T-46/T-47）
由 qa/e2e/ui_checks.mjs 在真前端上跑。
"""

from __future__ import annotations

import os
import shutil
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness  # noqa: E402

IDEAS = harness.load_baseline()
BY_ID = {i["id"]: i for i in IDEAS}

DETAIL_KEYS = ("costs", "total_to_first_invoice", "steps", "channels", "pitfalls")
BANNED_IN_DETAIL = ("wave", "maturity", "version", "score", "algorithm", "filtered", "match_pct")


class DetailBase(unittest.TestCase):
    def setUp(self) -> None:
        self.sc = harness.Sidecar().start()

    def tearDown(self) -> None:
        self.sc.cleanup()


class T21DetailBlocks(DetailBase):
    """T-21：4 个内容卡的数据齐备，且定价/合规不进详情页（只进 PDF 与数据对象）。"""

    CASES = ["T-21"]

    def test_four_blocks_present(self):
        for idea in IDEAS[:40]:
            with self.subTest(idea=idea["id"]):
                d = self.sc.ok("get_idea", {"id": idea["id"]})
                self.assertTrue(d.get("costs"), "缺 costs")
                self.assertTrue(d.get("steps"), "缺 steps")
                self.assertTrue(d.get("channels"), "缺 channels")
                self.assertTrue(d.get("pitfalls"), "缺 pitfalls")
                self.assertEqual(len(d["steps"]), 7, "steps 应恰好 7 条")

    def test_pricing_and_compliance_not_in_page_cards(self):
        d = self.sc.ok("get_idea", {"id": IDEAS[0]["id"]})
        # 页面卡片字段里不得夹带 pricing_hint / compliance_note（它们只进 PDF 与数据对象）
        for key in ("costs", "steps", "channels", "pitfalls"):
            blob = str(d.get(key))
            self.assertNotIn("pricing_hint", blob)


class T23SingaporeChannels(DetailBase):
    """T-23：SG 的 first_customers 必须是本地具体渠道。"""

    CASES = ["T-23"]

    def test_sg_channels_are_concrete(self):
        checked = 0
        for idea in IDEAS:
            if "SG" not in (idea.get("countries") or []) or "SG" in (idea.get("legal_blocks") or []):
                continue
            d = self.sc.ok("get_idea", {"id": idea["id"], "country": "SG"})
            chans = [str(c) for c in (d.get("channels") or [])]
            self.assertGreaterEqual(len(chans), 3, "%s 渠道不足 3 个：%s" % (idea["id"], chans))
            joined = " ".join(chans).lower()
            self.assertNotIn("social media", joined, "%s 用了 social media 空话" % idea["id"])
            self.assertTrue(any(k in joined for k in ("facebook", "whatsapp", "google maps",
                                                      "carousell", "telegram")),
                            "%s 的 SG 渠道没有本地形态：%s" % (idea["id"], chans))
            checked += 1
            if checked >= 12:
                break
        self.assertGreater(checked, 0, "没有任何支持 SG 的条目，无法验证")


class T24NoBackendWords(DetailBase):
    """T-24：详情对象给前端的可见字段里不出现后台词。"""

    CASES = ["T-24"]

    def test_no_jargon_in_visible_fields(self):
        for idea in IDEAS[:60]:
            d = self.sc.ok("get_idea", {"id": idea["id"]})
            visible = " ".join([
                str(d.get("title") or ""), str(d.get("summary") or ""),
                " ".join(c.get("item", "") + " " + str(c.get("amount", "")) for c in d.get("costs") or []),
                " ".join(str(s) for s in d.get("steps") or []),
                " ".join(str(s) for s in d.get("channels") or []),
                " ".join(str(s) for s in d.get("pitfalls") or []),
            ]).lower()
            for word in BANNED_IN_DETAIL:
                self.assertNotIn(word, visible, "%s 可见文案含 %r" % (idea["id"], word))


class T32DirtyFields(DetailBase):
    """T-32：缺第 3 条 pitfall / 超长文案 → 兜底句补齐，页面无 undefined、无溢出。

    分两层验：页面数据（get_idea，B 直接渲染）与 PDF 视图（render.build_pdf_view）。
    任何一层不过，T-32 即不过——两层都是"用户能看到的"。
    """

    CASES = ["T-32"]

    def _mutated_lib(self, mutator) -> str:
        import json
        mutated = []
        for i in IDEAS:
            j = dict(i)
            mutator(j)
            mutated.append(j)
        lib = self.sc.app_file("dirty_lib.json")
        with open(lib, "w", encoding="utf-8") as f:
            json.dump({"version": "v1", "ideas": mutated}, f, ensure_ascii=False)
        return lib

    def test_missing_third_pitfall_page(self):
        target = IDEAS[0]["id"]

        def mut(j):
            if j["id"] == target:
                j["pitfalls"] = list(j.get("pitfalls") or [])[:2]

        lib = self._mutated_lib(mut)
        with harness.Sidecar(env={"BIZSPARK_LIBRARY_CURRENT": lib}) as sc:
            d = sc.ok("get_idea", {"id": target})
        pitfalls = d.get("pitfalls") or []
        self.assertNotIn("undefined", str(d).lower())
        self.assertEqual(len(pitfalls), 3,
                         "页面数据只补到 %d 条 pitfall（T-32 要求兜底补齐 3 条）：%s"
                         % (len(pitfalls), pitfalls))

    def test_missing_third_pitfall_pdf(self):
        target = IDEAS[0]["id"]

        def mut(j):
            if j["id"] == target:
                j["pitfalls"] = list(j.get("pitfalls") or [])[:2]

        lib = self._mutated_lib(mut)
        path = self.sc.app_file("dirty.pdf")
        with harness.Sidecar(env={"BIZSPARK_LIBRARY_CURRENT": lib}) as sc:
            sc.ok("export_plan", {"id": target, "path": path})
        text = harness.pdf_text(path)
        self.assertGreater(len(text), 400)
        self.assertNotIn("undefined", text.lower())

    def test_overlong_text_not_overflowing_page(self):
        target = IDEAS[0]["id"]

        def mut(j):
            if j["id"] == target:
                j["one_liner"] = "Very long sentence that keeps going. " * 60
                j["steps"] = [("Step with a very long body that should be clipped " * 10) for _ in range(7)]

        lib = self._mutated_lib(mut)
        with harness.Sidecar(env={"BIZSPARK_LIBRARY_CURRENT": lib}) as sc:
            d = sc.ok("get_idea", {"id": target})
        self.assertNotIn("undefined", str(d).lower())
        self.assertLessEqual(len(str(d.get("summary") or "")), 260,
                             "页面摘要未截断（%d 字），会撑爆详情页" % len(str(d.get("summary") or "")))
        worst = max(len(str(s)) for s in d.get("steps") or [])
        self.assertLessEqual(worst, 260, "页面步骤未截断（最长 %d 字）" % worst)

    def test_overlong_text_clipped_in_pdf(self):
        target = IDEAS[0]["id"]

        def mut(j):
            if j["id"] == target:
                j["one_liner"] = "Very long sentence that keeps going. " * 60
                j["steps"] = [("Step with a very long body that should be clipped " * 10) for _ in range(7)]

        lib = self._mutated_lib(mut)
        path = self.sc.app_file("long.pdf")
        with harness.Sidecar(env={"BIZSPARK_LIBRARY_CURRENT": lib}) as sc:
            d = sc.ok("export_plan", {"id": target, "path": path})
        self.assertEqual(d.get("pages"), 1, "超长文案把 PDF 撑成多页")
        text = harness.pdf_text(path)
        self.assertLessEqual(len(text), 6000, "PDF 文本异常长，可能未截断")


class ExportBase(unittest.TestCase):
    def setUp(self) -> None:
        self.sc = harness.Sidecar().start()
        self.out = self.sc.app_file("out")
        os.makedirs(self.out, exist_ok=True)
        self.idea_id = IDEAS[0]["id"]

    def tearDown(self) -> None:
        self.sc.cleanup()


class T25DefaultName(ExportBase):
    """T-25（后端侧）：默认文件名可读、合法、不含金额。"""

    CASES = ["T-25"]

    def test_file_name_echoes_target(self):
        """后端只负责"写到哪就叫什么"；默认目录与默认名由 A 的系统对话框给（T-25 真机验）。"""
        path = os.path.join(self.out, "BizSpark-Plan-pet-care.pdf")
        d = self.sc.ok("export_plan", {"id": self.idea_id, "path": path})
        self.assertEqual(d.get("file_name"), "BizSpark-Plan-pet-care.pdf")
        self.assertTrue(d.get("path", "").endswith("BizSpark-Plan-pet-care.pdf"))
        self.assertGreater(d.get("bytes", 0), 1000)
        self.assertEqual(d.get("pages"), 1)


class T26PdfContent(ExportBase):
    """T-26：恰好 1 页；含 7 步与成本合计；无 URL/水印/二维码。"""

    CASES = ["T-26"]

    def test_pdf_single_page_and_content(self):
        for idea in IDEAS[:6]:
            with self.subTest(idea=idea["id"]):
                path = os.path.join(self.out, "p_%s.pdf" % idea["id"])
                d = self.sc.ok("export_plan", {"id": idea["id"], "path": path})
                self.assertEqual(d.get("pages"), 1, "返回 pages≠1：%r" % d.get("pages"))
                self.assertEqual(harness.pdf_pages(path), 1, "PDF 实际页数≠1")
                detail = self.sc.ok("get_idea", {"id": idea["id"]})
                text = harness.pdf_text(path)
                self.assertGreater(len(text), 400, "PDF 文本过少，可能是空页")
                # 7 步：取每步前 18 个字符比对（PDF 会换行）
                hits = 0
                for step in detail["steps"]:
                    head = str(step)[:18]
                    if head and head in text:
                        hits += 1
                self.assertGreaterEqual(hits, 5, "7 步里只匹配到 %d 步" % hits)
                # 成本合计
                total = str(detail.get("total_to_first_invoice") or "")
                self.assertTrue(total)
                self.assertIn(total.split(".")[0][:4], text, "PDF 缺成本合计 %r" % total)

    def test_no_url_watermark_qr(self):
        path = os.path.join(self.out, "clean.pdf")
        self.sc.ok("export_plan", {"id": self.idea_id, "path": path})
        self.assertFalse(harness.pdf_has_url(path), "PDF 含 URL/链接注解")
        raw = harness.pdf_raw(path).lower()
        self.assertNotIn(b"/annot", raw, "PDF 含注解（可能被塞二维码/链接）")
        self.assertNotIn(b"/subtype /image", raw, "PDF 含位图（水印/二维码）")
        self.assertNotIn(b"/xobject", raw, "PDF 含外部对象（可能夹带水印图）")
        self.assertNotIn("bizspark.app", harness.pdf_text(path).lower())

    def test_fonts_embedded_builtin(self):
        path = os.path.join(self.out, "font.pdf")
        self.sc.ok("export_plan", {"id": self.idea_id, "path": path})
        fonts = harness.pdf_fonts(path)
        self.assertTrue(fonts, "PDF 没有字体信息")
        self.assertTrue(all("Helvetica" in f or "Times" in f or "Courier" in f for f in fonts),
                        "字体不是内置标准字体：%s" % fonts)


class T27ExportSpeed(ExportBase):
    """T-27：导出 ≤2s，返回 pages:1。"""

    CASES = ["T-27"]

    def test_under_two_seconds(self):
        worst = 0.0
        for i, idea in enumerate(IDEAS[:8]):
            path = os.path.join(self.out, "speed_%d.pdf" % i)
            t0 = time.perf_counter()
            d = self.sc.ok("export_plan", {"id": idea["id"], "path": path})
            dt = time.perf_counter() - t0
            worst = max(worst, dt)
            self.assertEqual(d.get("pages"), 1)
            self.assertGreater(d.get("bytes", 0), 1000, "bytes 太小：%r" % d.get("bytes"))
        self.assertLess(worst, 2.0, "最慢一次 %.2fs，超过 2s 红线" % worst)


class T33OfflineExport(ExportBase):
    """T-33：导出全程不联网（socket 全部禁用后仍成功）。"""

    CASES = ["T-33"]

    def test_export_without_network(self):
        # 通过 sitecustomize 注入 socket 禁用，真实验证"零出网"而不是读代码猜
        guard = self.sc.app_file("noguard")
        os.makedirs(guard, exist_ok=True)
        with open(os.path.join(guard, "sitecustomize.py"), "w", encoding="utf-8") as f:
            f.write(
                "import socket\n"
                "class _Blocked(RuntimeError):\n"
                "    pass\n"
                "def _deny(*a, **k):\n"
                "    raise _Blocked('network disabled by QA (T-33/T-28)')\n"
                "socket.socket = _deny\n"
                "socket.create_connection = _deny\n"
                "socket.getaddrinfo = _deny\n"
            )
        env = {"PYTHONPATH": guard}
        path = os.path.join(self.out, "offline.pdf")
        with harness.Sidecar(env=env) as sc:
            d = sc.ok("export_plan", {"id": self.idea_id, "path": path})
            self.assertEqual(d.get("pages"), 1)
            # 整条主链路也不许出网
            sc.ok("diagnose", {"answers": harness.default_answers()})
            sc.ok("get_idea", {"id": self.idea_id})
            sc.ok("list_saved")
        self.assertTrue(os.path.isfile(path))
        self.assertGreater(os.path.getsize(path), 1000)


class T34ReadOnlyDir(ExportBase):
    """T-34：目录不可写 → 只提示换文件夹（recoverable），不崩、不丢步骤。

    注：错误码是否等于附录 D 的 E_FS_READONLY 属"契约漂移"，在
    test_contract.py 单独记，不混进本用例（用户可见行为才是 T-34 的判据）。
    """

    CASES = ["T-34"]

    def test_readonly_dir_error_semantics(self):
        ro = os.path.join(self.out, "ro")
        os.makedirs(ro, exist_ok=True)
        path = os.path.join(ro, "x.pdf")
        # 用目录占用目标文件名 → 必定不可写（跨平台稳定，不依赖 chmod 权限位）
        os.makedirs(path, exist_ok=True)
        err = self.sc.err("export_plan", {"id": self.idea_id, "path": path})
        self.assertTrue(err.get("recoverable"), "不可写应回可恢复错误：%r" % err)
        self.assertIn("another folder", str(err.get("message") or "").lower(),
                      "提示语应引导换文件夹，实际 %r" % err.get("message"))
        self.assertNotIn("traceback", str(err).lower())
        # 失败后引擎仍可用（不丢步骤）
        d = self.sc.ok("get_idea", {"id": self.idea_id})
        self.assertEqual(len(d["steps"]), 7)

    def test_cancel_returns_silent_error(self):
        err = self.sc.err("export_plan", {"id": self.idea_id, "path": ""})
        self.assertTrue(err.get("recoverable"), "取消应回可恢复错误（前端静默回详情）")
        self.assertNotIn("traceback", str(err).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
