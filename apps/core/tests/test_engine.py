# -*- coding: utf-8 -*-
"""engine 单测（C-11）—— 覆盖 T-09…T-18、T-28/T-29、T-31、T-38 与 §3.4 装配。

运行：cd apps/core && python -m unittest discover tests -v
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import diagnose, load_library, FALLBACK_CHAIN
from engine.quiz import validate_answers, CAPITAL_TIERS, HOURS_TIERS, RISK_ENUM, ASSET_ENUM
from engine.filter import hard_filter, relax_hours
from engine.score import WEIGHTS, SEEN_FACTOR, match_pct
from engine.why import build_why, build_tags, _contains_forbidden
from engine.detail import assemble
from tests.fixture import make_library

ANSWERS = {"country": "US", "capital": "500-2k", "hours": "<10",
           "assets": ["laptop"], "risk": "small_loss"}
LIB = make_library(312)


class T09AnswerValidation(unittest.TestCase):
    """C-02 / T-09：§3.1 答案校验，非法静默回退。"""

    def test_valid_answers_pass_through(self):
        norm, fell = validate_answers(dict(ANSWERS))
        self.assertEqual(norm, ANSWERS)
        self.assertEqual(fell, [])

    def test_invalid_enum_silently_falls_back(self):
        norm, fell = validate_answers({"country": "FR", "capital": "999", "hours": "28h", "risk": "yolo"})
        self.assertIn(norm["country"], ["US"])
        self.assertIn(norm["capital"], CAPITAL_TIERS)
        self.assertIn(norm["hours"], HOURS_TIERS)
        self.assertIn(norm["risk"], RISK_ENUM)
        self.assertTrue(fell)

    def test_assets_non_array_becomes_empty(self):
        norm, fell = validate_answers({**ANSWERS, "assets": "laptop"})
        self.assertEqual(norm["assets"], [])
        self.assertIn("assets", fell)

    def test_assets_invalid_elements_dropped(self):
        norm, _ = validate_answers({**ANSWERS, "assets": ["laptop", "jetpack", ""]})
        self.assertEqual(norm["assets"], ["laptop"])

    def test_unknown_fields_ignored(self):
        norm, _ = validate_answers({**ANSWERS, "hacker_field": "x", "extra": 1})
        self.assertNotIn("hacker_field", norm)

    def test_b_wrapper_format_accepted(self):
        norm, _ = validate_answers({"answers": ANSWERS})
        self.assertEqual(norm, ANSWERS)

    def test_null_payload_no_crash(self):
        norm, _ = validate_answers(None)
        self.assertEqual(norm["capital"], "<500")


class T10T11HardFilter(unittest.TestCase):
    """C-03 / T-10 / T-11：硬过滤向上兼容、国家/legal_blocks/status、saturated 标记不剔。"""

    def test_capital_upward_compatible_not_downward(self):
        kept, _ = hard_filter(LIB, {**ANSWERS, "capital": "500-2k"})
        tiers = {i.get("capital_tier") for i, _s in kept}
        self.assertEqual(tiers, {"<500", "500-2k"})  # 向上兼容，不向下
        kept2, _ = hard_filter(LIB, {**ANSWERS, "capital": "10k+"})
        self.assertEqual({i.get("capital_tier") for i, _s in kept2}, set(CAPITAL_TIERS))

    def test_hours_upward(self):
        kept, _ = hard_filter(LIB, {**ANSWERS, "hours": "<10"})
        self.assertEqual({i.get("hours_per_week") for i, _s in kept}, {"<10"})
        kept2, _ = hard_filter(LIB, {**ANSWERS, "hours": "full"})
        self.assertEqual({i.get("hours_per_week") for i, _s in kept2}, set(HOURS_TIERS))

    def test_country_and_legal_blocks(self):
        kept, _ = hard_filter(LIB, {**ANSWERS, "country": "SG"})
        for idea, _s in kept:
            self.assertIn("SG", idea["countries"])
            self.assertNotIn("SG", idea.get("legal_blocks") or [])

    def test_retired_excluded_saturated_kept_marked(self):
        kept, sat_count = hard_filter(LIB, ANSWERS)
        self.assertTrue(all(i.get("status", "active") == "active" for i, _s in kept))
        marked = [1 for i, s in kept if s]
        self.assertEqual(len(marked), sat_count)
        self.assertTrue(sat_count > 0)  # 夹具含 saturated


class T12T13T14Scoring(unittest.TestCase):
    """C-04 / T-12 / T-13 / T-14：8 维权重、趋势锁死 5%。"""

    def test_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(WEIGHTS.values()), 1.0)

    def test_trend_weight_locked_at_5pct(self):
        self.assertEqual(WEIGHTS["trend"], 0.05)  # 锁死，禁止调高

    def test_score_bounds_and_determinism(self):
        from engine.score import score_idea
        for idea in LIB[:50]:
            s = score_idea(idea, ANSWERS)
            self.assertGreaterEqual(s, 0.0)
            self.assertLessEqual(s, 1.0)
        self.assertEqual(score_idea(LIB[0], ANSWERS), score_idea(LIB[0], ANSWERS))

    def test_match_pct_range_60_99(self):
        for s in [0.0, 0.17, 0.5, 0.83, 1.0]:
            self.assertTrue(60 <= match_pct(s) <= 99)


class T15SeenAndRepeatable(unittest.TestCase):
    """C-05 / T-15：已看降权 ×0.85；同答案重跑 10 次完全一致。"""

    def _run(self, saved_ids=None):
        res, err = diagnose({**ANSWERS, "saved_ids": saved_ids or []}, library=list(LIB))
        self.assertIsNone(err)
        return res

    def test_seen_downweighted(self):
        fresh = self._run()
        seen_run = self._run([fresh["ideas"][0]["id"]])
        # 看过的条目降权后排名变化或总分变化（match_pct 只降不升）
        by_id_fresh = {c["id"]: c for c in fresh["ideas"]}
        for card in seen_run["ideas"]:
            if card["id"] in by_id_fresh:
                self.assertLessEqual(card["match_pct"], by_id_fresh[card["id"]]["match_pct"])

    def test_repeatable_ten_runs(self):
        first = self._run()
        for _ in range(9):
            again = self._run()
            self.assertEqual(json.dumps(first["ideas"], sort_keys=True),
                             json.dumps(again["ideas"], sort_keys=True))
            self.assertEqual(first["checked"], again["checked"])
            self.assertEqual(first["filtered"], again["filtered"])

    def test_seen_factor_value(self):
        self.assertAlmostEqual(SEEN_FACTOR, 0.85)


class T16T17Top3Why(unittest.TestCase):
    """C-06 / T-16 / T-17：Top3 克制输出、match_pct、why 引用答案词、禁词、tags 恰好 3。"""

    def setUp(self):
        self.res, err = diagnose(dict(ANSWERS), library=list(LIB))
        self.assertIsNone(err)

    def test_top3_and_rank(self):
        self.assertEqual(len(self.res["ideas"]), 3)
        self.assertEqual([c["rank"] for c in self.res["ideas"]], [1, 2, 3])

    def test_saturated_never_in_top3_when_enough(self):
        non_sat_available = sum(1 for i, s in hard_filter(LIB, ANSWERS)[0] if not s)
        if non_sat_available >= 3:
            ids = {c["id"] for c in self.res["ideas"]}
            sat_ids = {i["id"] for i, s in hard_filter(LIB, ANSWERS)[0] if s}
            self.assertFalse(ids & sat_ids)

    def test_why_references_answer_words(self):
        for card in self.res["ideas"]:
            text = card["why"].lower()
            # 至少引用一个答案具体词（资金档/时间/资产/国家）
            hit = any(w in text for w in ["budget", "$500", "hours", "laptop", "united states", "money", "schedule", "local", "kitchen table", "area"])
            self.assertTrue(hit, card["why"])

    def test_why_no_forbidden_words(self):
        for card in self.res["ideas"]:
            self.assertFalse(_contains_forbidden(card["why"]), card["why"])

    def test_tags_exactly_three(self):
        for card in self.res["ideas"]:
            self.assertEqual(len(card["tags"]), 3)
            self.assertTrue(all(isinstance(t, str) and t for t in card["tags"]))

    def test_match_pct_on_card(self):
        for card in self.res["ideas"]:
            self.assertTrue(60 <= card["match_pct"] <= 99)


class T18T31Degradation(unittest.TestCase):
    """C-07 / T-18 / T-31：放宽时间档一次、1–2 条 + 温和 note、绝不返回空数组。"""

    def test_relax_once_only(self):
        self.assertEqual(relax_hours({**ANSWERS, "hours": "<10"})["hours"], "10-25")
        self.assertEqual(relax_hours({**ANSWERS, "hours": "10-25"})["hours"], "full")
        self.assertIsNone(relax_hours({**ANSWERS, "hours": "full"}))  # full 不再放宽

    def test_never_empty_even_impossible_answers(self):
        # 极端组合：最低资金 + 最低时间 + 无人脉资产 + PH（legal 收紧）
        res, err = diagnose({"country": "PH", "capital": "<500", "hours": "<10",
                             "assets": [], "risk": "no_impact"}, library=list(LIB))
        self.assertIsNone(err)
        self.assertTrue(res["ideas"])  # 绝不空数组
        self.assertLessEqual(len(res["ideas"]), 3)

    def test_degrade_flag_and_note(self):
        res, _ = diagnose({"country": "US", "capital": "<500", "hours": "<10",
                           "assets": ["car", "kitchen", "design", "coding", "spare_room", "local_network"],
                           "risk": "no_impact"}, library=list(LIB))
        if len(res["ideas"]) < 3:
            self.assertTrue(res["degraded"])
            self.assertTrue(isinstance(res["degrade_note"], str) and res["degrade_note"])
        else:
            self.assertFalse(res["degraded"])

    def test_no_match_error_never_raised_as_failure(self):
        # 即使极端输入也返回 ok（错误表 E_ENGINE_NO_MATCH 不应出现在正常路径）
        res, err = diagnose({"country": "CA", "capital": "<500", "hours": "<10",
                             "assets": [], "risk": "no_impact"}, library=list(LIB))
        self.assertIsNone(err)
        self.assertTrue(res["ideas"])


class T28T29StatsAndPrivacy(unittest.TestCase):
    """C-08 / T-28 / T-29：统计 checked/filtered；零出网；不写用户数据到日志。"""

    def test_stats_consistent(self):
        res, _ = diagnose(dict(ANSWERS), library=list(LIB))
        self.assertEqual(res["checked"], 312)
        self.assertEqual(res["filtered"], res["checked"] - len(res["ideas"]))
        self.assertLessEqual(res["filtered"], 312)

    def test_result_carries_no_user_answer_echo_in_stats(self):
        res, _ = diagnose(dict(ANSWERS), library=list(LIB))
        for key in ("country", "capital", "answers", "risk"):
            self.assertNotIn(key, res["ideas"][0])


class T38FallbackChain(unittest.TestCase):
    """C-09 / T-38：current.json → baseline 只读副本 → fallback_ideas.json。"""

    def _write(self, path, obj):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f)

    def test_chain_picks_first_healthy(self):
        with tempfile.TemporaryDirectory() as d:
            p1, p2, p3 = [os.path.join(d, n) for n in ("a.json", "b.json", "c.json")]
            self._write(p1, {"ideas": LIB[:10]})
            self._write(p2, {"ideas": LIB[10:20]})
            self._write(p3, {"ideas": LIB[20:23]})
            ideas, source = load_library([p1, p2, p3])
            self.assertEqual(source, "a.json")
            self.assertEqual(len(ideas), 10)

    def test_corrupt_current_falls_to_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            p1, p2 = os.path.join(d, "current.json"), os.path.join(d, "baseline.json")
            with open(p1, "w", encoding="utf-8") as f:
                f.write("{corrupt!!!")
            self._write(p2, {"ideas": LIB[30:40]})
            ideas, source = load_library([p1, p2])
            self.assertEqual(source, "baseline.json")

    def test_all_bad_items_in_file_means_corrupt(self):
        with tempfile.TemporaryDirectory() as d:
            p1, p2 = os.path.join(d, "current.json"), os.path.join(d, "baseline.json")
            self._write(p1, {"ideas": [{"id": None}, {"bad": 1}]})
            self._write(p2, {"ideas": LIB[40:43]})
            ideas, source = load_library([p1, p2])
            self.assertEqual(source, "baseline.json")

    def test_builtin_fallback_file_exists_and_valid(self):
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        fb = os.path.join(data_dir, "fallback_ideas.json")
        with open(fb, encoding="utf-8") as f:
            ideas = json.load(f)["ideas"]
        self.assertEqual(len(ideas), 3)
        good, source = load_library([fb])
        self.assertEqual(len(good), 3)


class C10DetailAssembly(unittest.TestCase):
    """C-10：get_idea 装配 —— 国家覆盖合并 + 3 个派生字段。"""

    def test_derived_fields(self):
        d = assemble(LIB[0])
        self.assertIsInstance(d["cost_total"], float)
        self.assertTrue(d["cost_rows"])
        self.assertTrue(all("item" in r and isinstance(r["amount"], str) for r in d["cost_rows"]))
        self.assertTrue(isinstance(d["payback_hint"], str) and d["payback_hint"])

    def test_country_override_merge(self):
        idea = dict(LIB[0])
        idea["overrides"] = {"SG": {"currency": "SGD",
                                    "first_customers": ["Facebook neighbourhood groups", "WhatsApp business lists"],
                                    "compliance_note": "SG: check ACRA registration before invoicing."}}
        d = assemble(idea, "SG")
        self.assertEqual(d["currency"], "SGD")
        self.assertEqual(d["first_customers"], idea["overrides"]["SG"]["first_customers"])
        self.assertTrue(d["_override_applied"])
        # min_capital 数值口径不变（USD 内部计算）
        self.assertEqual(d["min_capital"], LIB[0]["min_capital"])
        # 缺失国家回退主条目
        d2 = assemble(idea, "CA")
        self.assertFalse(d2["_override_applied"])
        self.assertNotEqual(d2.get("currency"), "SGD")

    def test_b_compat_aliases(self):
        d = assemble(LIB[0])
        self.assertEqual(d["channels"], d["first_customers"])
        self.assertEqual(d["costs"], d["cost_rows"])
        self.assertEqual(d["summary"], d["one_liner"])
        self.assertTrue(isinstance(d["total_to_first_invoice"], str))


class C01MainLoop(unittest.TestCase):
    """C-01：§2.4 全 cmd 可路由 + ready。"""

    def _main(self):
        import importlib
        spec = importlib.util.spec_from_file_location(
            "bizspark_main", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_all_ipc_cmds_routable(self):
        mod = self._main()
        for cmd in ["get_state", "save_answers", "diagnose", "get_idea", "export_plan", "export_csv",
                    "save_idea", "list_saved", "clear_saved", "compare_ideas", "get_settings",
                    "set_settings", "check_library", "apply_delta", "activate", "license_status",
                    "release_seat", "log_crash"]:
            self.assertIn(cmd, mod.CMD_HANDLERS, cmd)

    def test_ready_line(self):
        mod = self._main()
        line = json.loads(mod._ready_line())
        self.assertTrue(line["ok"])
        self.assertEqual(line["data"]["event"], "ready")

    def test_bad_line_and_unknown_cmd(self):
        mod = self._main()
        r = mod.handle("not json")
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"]["code"], "E_BAD_REQUEST")
        r = mod.handle(json.dumps({"req_id": "1", "cmd": "nope", "payload": {}}))
        self.assertEqual(r["error"]["code"], "E_UNKNOWN_CMD")

    def test_diagnose_via_handle(self):
        # dev 环境 baseline 为空占位 → main 管线按回退链落到 fallback_ideas.json（3 条），
        # 这正是 C-09/T-38 的预期行为；注入临时 312 条库验证全量口径。
        import engine
        mod = self._main()
        with tempfile.TemporaryDirectory() as d:
            lib_path = os.path.join(d, "current.json")
            with open(lib_path, "w", encoding="utf-8") as f:
                json.dump({"ideas": LIB}, f)
            engine.FALLBACK_CHAIN.insert(0, lib_path)  # 运行时注入工作库（F 维护 current.json 后同此路径）
            try:
                r = mod.handle(json.dumps({"req_id": "r-1", "cmd": "diagnose",
                                           "payload": {"answers": ANSWERS}}))
            finally:
                engine.FALLBACK_CHAIN.remove(lib_path)
        self.assertTrue(r["ok"])
        self.assertEqual(len(r["data"]["ideas"]), 3)
        self.assertEqual(r["data"]["checked"], 312)


if __name__ == "__main__":
    unittest.main()
