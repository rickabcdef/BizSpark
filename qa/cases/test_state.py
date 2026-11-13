"""test_state.py — T-29、T-30-5、T-30-6、T-35、T-36、T-38、T-40（负责人：H）

F 的状态层与降级路径。全部走真实 IPC；损坏/回滚类用例用临时 appdata，
绝不碰仓库里的 baseline（只读副本语义本身也要验）。
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness  # noqa: E402

IDEAS = harness.load_baseline()
DELTA = harness.read_json(harness.REPO / "hosting" / "delta_2026-12.json")


class StateBase(unittest.TestCase):
    def setUp(self) -> None:
        self.sc = harness.Sidecar().start()

    def tearDown(self) -> None:
        self.sc.cleanup()

    def lib_snapshot(self) -> tuple[str, bytes]:
        p = os.path.join(self.sc.app_data, "library", "current.json")
        if not os.path.isfile(p):
            return p, b""
        with open(p, "rb") as f:
            return p, f.read()


class T35CorruptState(StateBase):
    """T-35：state.json 损坏 → 静默重建空存档，其他目录不动。"""

    CASES = ["T-35"]

    def test_corrupt_state_recovers(self):
        self.sc.ok("diagnose", {"answers": harness.default_answers()})
        self.sc.ok("apply_delta", DELTA)          # 建工作库（state 与库互不影响是本用例要验的）
        self.sc.ok("save_idea", {"id": IDEAS[0]["id"]})
        before_lib = self.lib_snapshot()[1]
        self.assertTrue(before_lib)

        bad = self.sc.app_file("state.json")
        with open(bad, "w", encoding="utf-8") as f:
            f.write('{"saved": [ this is not json')
        self.sc.stop()

        sc2 = harness.Sidecar(app_data=self.sc.app_data).start()
        try:
            st = sc2.ok("get_state")
            self.assertEqual(st.get("saved"), [])
            self.assertEqual(st.get("saved_count"), 0)
            self.assertTrue(st.get("library_ideas", 0) >= 300, "库也被清了")
            kept = [n for n in os.listdir(self.sc.app_data) if n.startswith("state.json.corrupt")]
            self.assertTrue(kept, "坏文件没有留档（应改名 .corrupt-<ts>，不删）")
            after = self.lib_snapshot()[1]
            self.assertEqual(before_lib, after, "重建存档时动了工作库")
        finally:
            sc2.stop()

    def test_truncated_state_recovers(self):
        with open(self.sc.app_file("state.json"), "w", encoding="utf-8") as f:
            f.write("")
        self.sc.stop()
        with harness.Sidecar(app_data=self.sc.app_data) as sc2:
            st = sc2.ok("get_state")
            self.assertEqual(st.get("saved"), [])


class T36SavedDedupe(StateBase):
    """T-36：存档去重、按 saved_at 倒序。"""

    CASES = ["T-36"]

    def test_dedupe(self):
        ids = [IDEAS[0]["id"], IDEAS[1]["id"], IDEAS[2]["id"]]
        for i in ids:
            self.sc.ok("save_idea", {"id": i})
        dup = self.sc.ok("save_idea", {"id": ids[0]})     # 重复存第一条
        items = self.sc.ok("list_saved")["items"]
        self.assertEqual(len(items), 3, "重复存导致条数变成 %d" % len(items))
        self.assertEqual({i["id"] for i in items}, set(ids))
        self.assertEqual(len({i["id"] for i in items}), len(items), "出现了重复 id")
        self.assertTrue(dup.get("duplicate"), "重复存没有标记 duplicate")

    def test_order_by_saved_at_desc(self):
        # saved_at 是日期精度（同一天存 3 条无法验倒序），显式种入三天再验
        for i in (IDEAS[0]["id"], IDEAS[1]["id"], IDEAS[2]["id"]):
            self.sc.ok("save_idea", {"id": i})
        self.sc.stop()
        st_path = self.sc.app_file("state.json")
        st = json.loads(open(st_path, encoding="utf-8").read())
        for idx, entry in enumerate(st["saved"]):
            entry["saved_at"] = "2026-11-%02d" % (idx + 1)   # 越靠前越旧
        st["saved"] = list(reversed(st["saved"]))            # 故意打乱落盘顺序
        with open(st_path, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False)
        with harness.Sidecar(app_data=self.sc.app_data) as sc2:
            got = [i["saved_at"] for i in sc2.ok("list_saved")["items"]]
        self.assertEqual(got, sorted(got, reverse=True), "list_saved 未按 saved_at 倒序：%s" % got)

    def test_clear_empties(self):
        self.sc.ok("save_idea", {"id": IDEAS[0]["id"]})
        self.sc.ok("clear_saved")
        self.assertEqual(self.sc.ok("list_saved")["items"], [])


class T38LibraryFallback(unittest.TestCase):
    """T-38：current.json 坏 → baseline 只读副本 → 再坏用 fallback_ideas.json。

    第三层要真的走 fallback，必须让"内置只读副本"也坏掉；开发库里
    apps/core/data/baseline_v1.json 就是第三层，所以复制一份 core 树来破坏它，
    绝不动仓库里的文件。
    """

    CASES = ["T-38"]

    def setUp(self) -> None:
        self.tmp = harness.tempfile.mkdtemp(prefix="bz_chain_")
        self.broken = os.path.join(self.tmp, "broken.json")
        with open(self.broken, "w", encoding="utf-8") as f:
            f.write("{ broken : [")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_first_layer_broken_falls_to_baseline(self):
        with harness.Sidecar(env={"BIZSPARK_LIBRARY_CURRENT": self.broken}) as sc:
            d = sc.ok("diagnose", {"answers": harness.default_answers()})
            self.assertGreaterEqual(d["checked"], 300,
                                    "工作库坏了却没回退到 baseline 副本：checked=%r" % d.get("checked"))
            self.assertTrue(1 <= len(d["ideas"]) <= 3)

    def test_all_layers_broken_falls_to_fallback_ideas(self):
        core = os.path.join(self.tmp, "core")
        shutil.copytree(harness.CORE, core, ignore=shutil.ignore_patterns("__pycache__"))
        with open(os.path.join(core, "data", "baseline_v1.json"), "w", encoding="utf-8") as f:
            f.write("[ not json")
        script = os.path.join(core, "main.py")
        with harness.Sidecar(script=script,
                             env={"BIZSPARK_LIBRARY_CURRENT": self.broken,
                                  "BIZSPARK_BASELINE_PATH": self.broken}) as sc:
            d = sc.ok("diagnose", {"answers": harness.default_answers()})
            self.assertTrue(1 <= len(d["ideas"]) <= 3, "整库坏了却出了空结果")
            self.assertLessEqual(d["checked"], 10,
                                 "没有落到 fallback_ideas.json（checked=%r）" % d.get("checked"))
            self.assertFalse(sc.ok("ping").get("pong") is None)

    def test_baseline_file_never_mutated(self):
        import hashlib
        base = harness.DATA / "baseline_v1.json"
        before = hashlib.sha256(base.read_bytes()).hexdigest()
        with harness.Sidecar() as sc:
            sc.ok("diagnose", {"answers": harness.default_answers()})
            sc.ok("apply_delta", DELTA)
            sc.ok("get_state")
        after = hashlib.sha256(base.read_bytes()).hexdigest()
        self.assertEqual(before, after, "内置 baseline 被改写了（必须只读）")


class T40DeltaRollback(StateBase):
    """T-40：合并失败 → 整体回滚，版本号不变，retire 条目磁盘仍在。"""

    CASES = ["T-40"]

    def _version(self) -> str:
        return self.sc.ok("get_state").get("library_version")

    def test_invalid_delta_rolls_back(self):
        self.sc.ok("diagnose", {"answers": harness.default_answers()})  # 建工作库
        ver_before = self._version()
        _, lib_before = self.lib_snapshot()
        n_before = self.sc.ok("get_state").get("library_ideas")

        bad = dict(DELTA)
        bad["add"] = [{"id": "dup-id-test", "title": "x"}]           # 字段缺失，过不了 V-01/V-11
        bad["revise"] = [{"id": "no-such-id", "maturity": "growing"}] # 不存在的 id
        err = self.sc.err("apply_delta", bad)
        self.assertIn(err.get("code"), ("E_DELTA_INVALID", "E_BAD_REQUEST"), "错误码：%r" % err)

        _, lib_after = self.lib_snapshot()
        self.assertEqual(lib_before, lib_after, "失败后工作库被改动（应字节级回滚）")
        self.assertEqual(self._version(), ver_before, "失败后版本号变了")
        self.assertEqual(self.sc.ok("get_state").get("library_ideas"), n_before)

    def test_good_delta_applies_and_is_idempotent(self):
        self.sc.ok("diagnose", {"answers": harness.default_answers()})
        n0 = self.sc.ok("get_state").get("library_ideas")
        d1 = self.sc.ok("apply_delta", DELTA)
        n1 = self.sc.ok("get_state").get("library_ideas")
        self.assertGreaterEqual(n1, n0, "合并后条目数反而减少")
        d2 = self.sc.ok("apply_delta", DELTA)
        n2 = self.sc.ok("get_state").get("library_ideas")
        self.assertEqual(n1, n2, "重复应用同一 delta 不幂等：%s → %s" % (n1, n2))
        self.assertTrue(d1 or d2)

    def test_retire_keeps_entry_on_disk(self):
        self.sc.ok("diagnose", {"answers": harness.default_answers()})
        retired = (DELTA.get("retire") or [None])[0]
        if not retired:
            self.skipTest("delta 里没有 retire 项")
        self.sc.ok("apply_delta", DELTA)
        _, raw = self.lib_snapshot()
        ids = {i.get("id") for i in json.loads(raw.decode("utf-8")).get("ideas", [])}
        self.assertIn(retired, ids, "retire 把条目从磁盘删了（应只置 status）")

    def test_backups_kept_at_most_three(self):
        self.sc.ok("diagnose", {"answers": harness.default_answers()})
        self.sc.ok("apply_delta", DELTA)
        for i in range(4):
            d = {"target_baseline": "v1", "release": "2027-%02d-01" % (i + 1),
                 "revise": [{"id": IDEAS[0]["id"], "maturity": "growing"}]}
            self.sc.ok("apply_delta", d)
        rb = os.path.join(self.sc.app_data, "library", "rollback")
        files = sorted(os.listdir(rb)) if os.path.isdir(rb) else []
        self.assertLessEqual(len(files), 3, "回滚目录留了 %d 份（要求只留最近 3 份）" % len(files))


class T30DeltaAbnormal(StateBase):
    """T-30-5 / T-30-6：超大与非法 delta 静默跳过；断网后按序补合并。"""

    CASES = ["T-30-5", "T-30-6"]

    def _revise_only_delta(self, release, idea_id=None, **fields):
        """只含 revise 的合法 delta（新增 add 会与既有 id 冲突，不适合反复叠加）。"""
        target = idea_id or IDEAS[0]["id"]
        d = {"target_baseline": "v1", "release": release,
             "revise": [dict({"id": target}, **fields)]}
        return d

    def test_oversized_delta_silent(self):
        """T-30-5：delta 超 200KB 应静默跳过且不落盘。"""
        self.sc.ok("diagnose", {"answers": harness.default_answers()})
        self.sc.ok("apply_delta", DELTA)                     # 建工作库
        _, before = self.lib_snapshot()
        # 造 1200 条**字段合法**的新条目（复制真库），总大小 >200KB：
        # 只靠"字段非法被拒"不算过 T-30-5，必须验证体积闸门本身
        adds = []
        for i in range(1200):
            src = dict(IDEAS[i % len(IDEAS)])
            src["id"] = "huge-%04d" % i
            adds.append(src)
        huge = dict(DELTA)
        huge["release"] = "2027-03-01"
        huge["add"] = adds
        self.assertGreater(len(json.dumps(huge)), 200 * 1024)
        r = self.sc.call("apply_delta", huge)
        self.assertTrue(self.sc.alive(), "超大 delta 让 sidecar 崩了")
        _, after = self.lib_snapshot()
        if r.get("ok"):
            self.assertEqual(before, after,
                             ">200KB 的 delta 被接受了并写进库（库里现在 %d 条）"
                             % len(json.loads(after.decode("utf-8"))["ideas"]))
        else:
            self.assertEqual(before, after, "拒绝时也改了库")

    def test_illegal_fields_not_written(self):
        """T-40/V-11：revise 只能改白名单字段。"""
        self.sc.ok("diagnose", {"answers": harness.default_answers()})
        self.sc.ok("apply_delta", DELTA)
        _, before = self.lib_snapshot()
        bad = {"target_baseline": "v1", "release": "2027-02-01",
               "revise": [{"id": IDEAS[0]["id"], "title": "hacked title",
                           "capital_tier": "10k+", "secret_extra": "drop"}]}
        r = self.sc.call("apply_delta", bad)
        _, after = self.lib_snapshot()
        if not r.get("ok"):
            self.assertEqual(before, after, "校验失败却改了库")
            return
        data = json.loads(after.decode("utf-8"))
        idea = next(i for i in data["ideas"] if i["id"] == IDEAS[0]["id"])
        self.assertNotIn("secret_extra", idea, "白名单外的字段被写进库了")
        self.assertNotEqual(idea.get("title"), "hacked title", "白名单外字段覆盖了 title")

    def test_sequential_merges_in_release_order(self):
        self.sc.ok("diagnose", {"answers": harness.default_answers()})
        self.sc.ok("apply_delta", DELTA)
        v0 = self.sc.ok("get_state").get("library_version")
        n0 = self.sc.ok("get_state").get("library_ideas")
        # 模拟"断网一个月回来"：两个 release 的 revise-only delta 依次补
        for rel in ("2027-01-01", "2027-02-01"):
            self.sc.ok("apply_delta", self._revise_only_delta(rel, maturity="growing"))
        st = self.sc.ok("get_state")
        self.assertGreaterEqual(st.get("library_ideas"), n0)
        self.assertNotEqual(st.get("library_version"), v0, "合并后版本号没变")
        self.assertTrue(st.get("timeline"), "没有本地时间线记录")
        # 旧包不得回退版本（幂等保护）
        self.sc.ok("apply_delta", self._revise_only_delta("2026-12-01", maturity="emerging"))
        self.assertEqual(self.sc.ok("get_state").get("library_version"), st.get("library_version"),
                         "更旧的 delta 把版本号改回去了")


class T29OfflinePersistence(unittest.TestCase):
    """T-29：飞行模式跑完整链路 + 重启后存档仍在（socket 全禁）。"""

    CASES = ["T-29"]

    def test_offline_full_loop_and_restart(self):
        app = harness.tempfile.mkdtemp(prefix="bz_off_")
        guard = os.path.join(app, "guard")
        os.makedirs(guard, exist_ok=True)
        with open(os.path.join(guard, "sitecustomize.py"), "w", encoding="utf-8") as f:
            f.write("import socket\n"
                    "def _deny(*a, **k):\n"
                    "    raise RuntimeError('offline (T-29)')\n"
                    "socket.socket = _deny\n"
                    "socket.create_connection = _deny\n"
                    "socket.getaddrinfo = _deny\n")
        env = {"PYTHONPATH": guard}
        pdf = os.path.join(app, "plan.pdf")
        try:
            with harness.Sidecar(app_data=app, env=env) as sc:
                sc.ok("save_answers", {"answers": harness.default_answers()})
                d = sc.ok("diagnose", {"answers": harness.default_answers()})
                self.assertTrue(1 <= len(d["ideas"]) <= 3)
                first = d["ideas"][0]["id"]
                sc.ok("save_idea", {"id": first})
                e = sc.ok("export_plan", {"id": first, "path": pdf})
                self.assertEqual(e.get("pages"), 1)
                sc.ok("export_csv", {"id": first, "path": pdf.replace(".pdf", ".csv")})
            self.assertTrue(os.path.isfile(pdf))
            # 重启（仍无网）：存档还在、诊断还能跑
            with harness.Sidecar(app_data=app, env=env) as sc2:
                self.assertEqual([i["id"] for i in sc2.ok("list_saved")["items"]], [first])
                d2 = sc2.ok("diagnose", {"answers": harness.default_answers()})
                self.assertEqual(d2["ideas"][0]["id"], first, "重启后诊断结果变了")
        finally:
            shutil.rmtree(app, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
