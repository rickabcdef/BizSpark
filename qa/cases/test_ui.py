"""test_ui.py — 把 qa/e2e/ui_checks.mjs 的结果接进 Python 用例体系（负责人：H）

Node 侧跑真前端 + 真 sidecar，这里只负责"一次跑完、逐条映射成 unittest 用例"，
好让 qa/e2e/run_all.py 用同一套口径汇总所有 T 用例。
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness  # noqa: E402

REPORT = harness.REPO / "qa" / "reports" / "ui-checks.json"
_UI = {"loaded": False, "by_id": {}, "error": None}


def _run_ui() -> dict:
    """跑一次 node（约 1 分钟），结果缓存给所有子用例。"""
    if _UI["loaded"]:
        return _UI["by_id"]
    _UI["loaded"] = True
    web_dist = harness.REPO / "apps" / "web" / "dist" / "index.html"
    if not web_dist.exists():
        _UI["error"] = "前端未构建（cd apps/web && npm run build）"
        return _UI["by_id"]
    if os.path.exists(REPORT):
        os.remove(REPORT)
    rc, out = harness.sh(["node", str(harness.REPO / "qa" / "e2e" / "ui_checks.mjs")],
                         cwd=harness.REPO / "qa", timeout=900)
    if not os.path.exists(REPORT):
        _UI["error"] = "UI 用例没有产出报告：%s" % out[-800:]
        return _UI["by_id"]
    data = harness.read_json(REPORT)
    _UI["by_id"] = {r["id"]: r for r in data["results"]}
    print("\n" + out.strip().splitlines()[-1])
    return _UI["by_id"]


class UiBase(unittest.TestCase):
    def check(self, case_id: str) -> None:
        by_id = _run_ui()
        if _UI["error"]:
            self.fail(_UI["error"])
        r = by_id.get(case_id)
        self.assertIsNotNone(r, "UI 用例没有跑 %s" % case_id)
        self.assertTrue(r["ok"], "%s 未通过：%s" % (case_id, r["detail"]))


class T01(UiBase):
    CASES = ["T-01"]

    def test_first_screen(self):
        self.check("T-01")


class T03(UiBase):
    CASES = ["T-03"]

    def test_degraded_quiet(self):
        self.check("T-03")


class T04(UiBase):
    CASES = ["T-04"]

    def test_into_q1(self):
        self.check("T-04")


class T05(UiBase):
    CASES = ["T-05"]

    def test_auto_advance(self):
        self.check("T-05")


class T06(UiBase):
    CASES = ["T-06"]

    def test_double_click(self):
        self.check("T-06")


class T07(UiBase):
    CASES = ["T-07"]

    def test_multi_select(self):
        self.check("T-07")


class T08(UiBase):
    CASES = ["T-08"]

    def test_back_preselected(self):
        self.check("T-08")


class T19(UiBase):
    CASES = ["T-19"]

    def test_results_layout(self):
        self.check("T-19")


class T20(UiBase):
    CASES = ["T-20"]

    def test_recap_matches_answers(self):
        self.check("T-20")


class T21(UiBase):
    CASES = ["T-21"]

    def test_four_cards_order(self):
        self.check("T-21")


class T22(UiBase):
    CASES = ["T-22"]

    def test_sticky(self):
        self.check("T-22")


class T24(UiBase):
    CASES = ["T-24"]

    def test_no_backend_words(self):
        self.check("T-24")


class T37(UiBase):
    CASES = ["T-37"]

    def test_compare_three_fields(self):
        self.check("T-37")


class T46(UiBase):
    CASES = ["T-46"]

    def test_six_rows(self):
        self.check("T-46")


class T47(UiBase):
    CASES = ["T-47"]

    def test_dark_mode(self):
        self.check("T-47")


class T59Ui(UiBase):
    CASES = ["T-59"]

    def test_price_slots_render(self):
        self.check("T-59")


if __name__ == "__main__":
    unittest.main(verbosity=2)
