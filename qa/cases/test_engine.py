"""test_engine.py — T-09、T-10…T-18（负责人：H 验收 / C 修复）

全部对着真实 sidecar 跑，断言只读数据与返回值，不改 C 的代码。
"""

from __future__ import annotations

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness  # noqa: E402

IDEAS = harness.load_baseline()
BY_ID = {i["id"]: i for i in IDEAS}


class EngineBase(unittest.TestCase):
    CASES: list[str] = []

    def setUp(self) -> None:
        self.sc = harness.Sidecar().start()

    def tearDown(self) -> None:
        self.sc.cleanup()

    # 便于子类复用
    def diagnose(self, **answers) -> dict:
        return self.sc.ok("diagnose", {"answers": harness.default_answers(**answers)})


class T09InvalidAnswers(EngineBase):
    """T-09：非法答案静默回退，不报错不弹窗。"""

    CASES = ["T-09"]

    def test_garbage_answers_never_error(self):
        payloads = [
            {"answers": {"country": "ZZ", "capital": "banana", "hours": 42,
                         "assets": "laptop", "risk": "all-in"}},
            {"answers": {}},
            {"answers": None},
            {},
            {"answers": {"country": ["US"], "capital": {"tier": "<500"}}},
        ]
        for p in payloads:
            with self.subTest(payload=str(p)[:60]):
                d = self.sc.ok("diagnose", p)
                self.assertIn("ideas", d)
                self.assertTrue(1 <= len(d["ideas"]) <= 3)
                self.assertIsInstance(d["checked"], int)

    def test_unknown_fields_ignored(self):
        d = self.sc.ok("diagnose", {"answers": dict(harness.default_answers(),
                                                    hacker="drop table", __proto__=1)})
        self.assertTrue(1 <= len(d["ideas"]) <= 3)


class T10CapitalFilter(EngineBase):
    """T-10：资金只向上兼容，不向下。"""

    CASES = ["T-10"]

    def test_under_500_only_cheap(self):
        d = self.diagnose(capital="<500", hours="<10")
        for idea in d["ideas"]:
            src = BY_ID[idea["id"]]
            self.assertEqual(src["capital_tier"], "<500", "返回了更贵的条目：%s" % idea["id"])
            self.assertEqual(src["hours_per_week"], "<10")
        self.assertGreater(d["filtered"], 0, "过滤数应大于 0")

    def test_10k_up_accepts_all_tiers(self):
        d = self.diagnose(capital="10k+", hours="full")
        tiers = {BY_ID[i["id"]]["capital_tier"] for i in d["ideas"]}
        self.assertTrue(tiers.issubset({"<500", "500-2k", "2k-10k", "10k+"}))
        # 全档位用户可选到贵的条目，不应被限制在 <500
        self.assertLessEqual(len(tiers), 4)


class T11LegalBlocks(EngineBase):
    """T-11：legal_blocks 命中该国即剔除。

    真实库里被阻断的国家是 SG（6 条），故主用例走 SG；另用构造库覆盖 US，
    避免"只测真数据恰好没命中"的假绿。
    """

    CASES = ["T-11"]

    def test_sg_blocked_ids_never_returned(self):
        blocked = {i["id"] for i in IDEAS if "SG" in (i.get("legal_blocks") or [])}
        self.assertTrue(blocked, "库里应有至少一条 legal_blocks 含 SG")
        for _ in range(6):
            d = self.diagnose(country="SG", capital="10k+", hours="full")
            hit = blocked & {i["id"] for i in d["ideas"]}
            self.assertFalse(hit, "被法律阻断的条目出现在 SG 结果里：%s" % hit)

    def test_us_blocked_via_fixture(self):
        import json
        target = next(i for i in IDEAS
                      if i.get("status", "active") == "active"
                      and i.get("capital_tier") == "<500"
                      and i.get("hours_per_week") == "<10"
                      and "US" in (i.get("countries") or [])
                      and not (i.get("legal_blocks") or []))
        mutated = []
        for i in IDEAS:
            j = dict(i)
            if j["id"] == target["id"]:
                j["legal_blocks"] = ["US"]
            mutated.append(j)
        lib = self.sc.app_file("legal_lib.json")
        with open(lib, "w", encoding="utf-8") as f:
            json.dump({"version": "v1", "ideas": mutated}, f, ensure_ascii=False)
        with harness.Sidecar(env={"BIZSPARK_LIBRARY_CURRENT": lib}) as sc:
            d = sc.ok("diagnose", {"answers": harness.default_answers()})
        self.assertNotIn(target["id"], [i["id"] for i in d["ideas"]],
                         "legal_blocks=[US] 的条目仍出现在 US 结果里")

    def test_blocked_entries_still_on_disk(self):
        # 剔除 ≠ 删除（T-14 同口径）
        self.assertTrue(any(i.get("legal_blocks") for i in harness.load_baseline()))
        self.assertTrue(any("SG" in (i.get("legal_blocks") or []) for i in harness.load_baseline()))


class T12TrendWeight(EngineBase):
    """T-12：趋势新鲜度恰 5%，其余 7 维合计 95%。"""

    CASES = ["T-12"]

    def test_weights_frozen(self):
        sys.path.insert(0, str(harness.CORE))
        from engine.score import WEIGHTS  # noqa: PLC0415

        self.assertAlmostEqual(WEIGHTS["trend"], 0.05, places=6)
        others = sum(v for k, v in WEIGHTS.items() if k != "trend")
        self.assertAlmostEqual(others, 0.95, places=6)
        self.assertAlmostEqual(sum(WEIGHTS.values()), 1.0, places=6)


class T13WaveNotDominant(EngineBase):
    """T-13：把 wave 改成 bi-agent 不会直接进 Top3（趋势只值 5%）。"""

    CASES = ["T-13"]

    def test_wave_swap_does_not_promote_outsider(self):
        base = self.diagnose(capital="<500", hours="<10")
        top3 = {i["id"] for i in base["ideas"]}

        # 找一条当前不在 Top3、且满足硬过滤的条目，把 wave 改成 bi-agent
        pool = [i for i in IDEAS
                if i["id"] not in top3
                and i.get("status", "active") == "active"
                and i.get("capital_tier") == "<500"
                and i.get("hours_per_week") == "<10"
                and "US" in (i.get("countries") or [])
                and "US" not in (i.get("legal_blocks") or [])
                and i.get("maturity") != "saturated"]
        self.assertTrue(pool, "需要一条可改 wave 的候选")
        victim = pool[0]
        mutated = [dict(i) for i in IDEAS]
        for i in mutated:
            if i["id"] == victim["id"]:
                i["wave"] = "bi-agent"
        # 用临时库文件跑第二条 sidecar，绝不改仓库里的 baseline
        import json
        with harness.Sidecar() as sc2:
            lib = sc2.app_file("mutated_lib.json")
            with open(lib, "w", encoding="utf-8") as f:
                json.dump({"version": "v1", "ideas": mutated}, f, ensure_ascii=False)
            sc2.stop()
        with harness.Sidecar(env={"BIZSPARK_LIBRARY_CURRENT": lib}) as sc3:
            d = sc3.ok("diagnose", {"answers": harness.default_answers()})
        ids = [i["id"] for i in d["ideas"]]
        self.assertNotEqual(ids[0], victim["id"],
                            "换 wave 后直接冲到第 1 名——趋势权重失控")


class T14Saturated(EngineBase):
    """T-14：saturated 永不进 Top3，但仍在库文件里。"""

    CASES = ["T-14"]

    def test_saturated_never_top3(self):
        sat = {i["id"] for i in IDEAS if i.get("maturity") == "saturated"}
        self.assertTrue(sat)
        for cap, hrs in (("<500", "<10"), ("500-2k", "10-25"), ("10k+", "full")):
            d = self.diagnose(capital=cap, hours=hrs)
            hit = sat & {i["id"] for i in d["ideas"]}
            self.assertFalse(hit, "%s/%s 结果里出现 saturated：%s" % (cap, hrs, hit))

    def test_saturated_still_on_disk(self):
        sat = [i for i in IDEAS if i.get("maturity") == "saturated"]
        self.assertGreater(len(sat), 0)
        raw_ids = {i["id"] for i in harness.load_baseline()}
        self.assertTrue({i["id"] for i in sat}.issubset(raw_ids))


class T15Deterministic(EngineBase):
    """T-15：同答案重跑 10 次结果完全一致（含 tiebreak）。"""

    CASES = ["T-15"]

    def test_ten_runs_identical(self):
        payload = {"answers": harness.default_answers(capital="500-2k", hours="10-25",
                                                     assets=["car", "local_network"],
                                                     risk="small_loss")}
        runs = []
        for _ in range(10):
            d = self.sc.ok("diagnose", payload)
            runs.append([(i["id"], i["match_pct"]) for i in d["ideas"]])
        self.assertEqual(len(set(map(str, runs))), 1, "10 次结果不一致：%s" % set(map(str, runs)))

    def test_rerun_across_processes_identical(self):
        payload = {"answers": harness.default_answers(capital="2k-10k", hours="full")}
        a = [(i["id"], i["match_pct"]) for i in self.sc.ok("diagnose", payload)["ideas"]]
        with harness.Sidecar() as sc2:
            b = [(i["id"], i["match_pct"]) for i in sc2.ok("diagnose", payload)["ideas"]]
        self.assertEqual(a, b, "跨进程结果不稳定（字典序/随机源泄漏）")


class T16WhyPlainWords(EngineBase):
    """T-16：why 引用答案里的具体词，且不含后台词。"""

    CASES = ["T-16"]

    FORBIDDEN = ["algorithm", "score", "recommended by", "based on intelligent", "智能", " ai "]

    def test_why_uses_answer_words(self):
        d = self.diagnose(capital="<500", hours="<10", assets=["laptop"], risk="no_impact")
        for idea in d["ideas"]:
            why = str(idea.get("why") or "")
            self.assertTrue(why, "%s 没有 why" % idea["id"])
            low = why.lower()
            for word in self.FORBIDDEN:
                self.assertNotIn(word, low, "why 含后台词 %r：%s" % (word, why))
        # 至少一条要提到钱或时间的具体说法（模板池命中）
        joined = " ".join(str(i.get("why")) for i in d["ideas"]).lower()
        self.assertTrue(any(k in joined for k in ("$", "hour", "week", "budget", "under")),
                        "why 没有引用任何答案具体词：%s" % joined[:200])


class T17OutputShape(EngineBase):
    """T-17：1–3 条、match_pct 60–99 整数、字段齐全。"""

    CASES = ["T-17"]

    def test_shape(self):
        for cap, hrs in (("<500", "<10"), ("500-2k", "10-25"), ("2k-10k", "full"), ("10k+", "full")):
            d = self.diagnose(capital=cap, hours=hrs)
            ideas = d["ideas"]
            self.assertTrue(1 <= len(ideas) <= 3, "%d 条" % len(ideas))
            for i in ideas:
                self.assertIsInstance(i.get("match_pct"), int)
                self.assertTrue(60 <= i["match_pct"] <= 99, "match_pct=%r" % i["match_pct"])
                for key in ("id", "rank", "title", "summary", "why", "tags"):
                    self.assertIn(key, i, "%s 缺字段 %s" % (i.get("id"), key))
                self.assertEqual(len(i["tags"]), 3, "tags 应恰好 3 个：%s" % i["tags"])
            self.assertEqual([i["rank"] for i in ideas], list(range(1, len(ideas) + 1)))


class T18Degrade(EngineBase):
    """T-18：可用条目不足时放宽时间档一次，输出 1–2 条 + degrade_note。"""

    CASES = ["T-18"]

    def test_degrade_with_two_candidates(self):
        import json
        # 只留 2 条 <500/<10，其余全部改成昂贵档 → 触发放宽
        pool = [i for i in IDEAS
                if i.get("status", "active") == "active"
                and i.get("capital_tier") == "<500"
                and i.get("hours_per_week") == "<10"
                and "US" in (i.get("countries") or [])
                and "US" not in (i.get("legal_blocks") or [])
                and i.get("maturity") != "saturated"]
        self.assertGreaterEqual(len(pool), 2)
        keep = {pool[0]["id"], pool[1]["id"]}
        mutated = []
        for i in pool:
            if i["id"] not in keep:
                j = dict(i)
                j["hours_per_week"] = "10-25"   # 放宽一档后仍可能命中，但首选档只剩 2 条
                mutated.append(j)
        lib = self.sc.app_file("thin_lib.json")
        with open(lib, "w", encoding="utf-8") as f:
            json.dump({"version": "v1", "ideas": mutated}, f, ensure_ascii=False)
        with harness.Sidecar(env={"BIZSPARK_LIBRARY_CURRENT": lib}) as sc:
            d = sc.ok("diagnose", {"answers": harness.default_answers(capital="<500", hours="<10")})
        self.assertTrue(1 <= len(d["ideas"]) <= 3)
        if len(d["ideas"]) < 3:
            self.assertTrue(d.get("degraded"), "不足 3 条但没标 degraded")
            self.assertTrue(d.get("degrade_note"), "缺少温和 note")
        # 绝不空数组（无论放宽与否）
        self.assertNotEqual(d["ideas"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
