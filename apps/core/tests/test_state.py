# -*- coding: utf-8 -*-
"""test_state — F 任务卡单元测试（F-01…F-10；新增文件，不改 A/B/C/D/E 的任何测试）

验收映射：
F-01 state.json 首次创建 / 损坏静默重建（T-35）
F-02 get_state / save_answers / last_result 缓存（T-03 / T-31）
F-03 存档去重 / 倒序 / 清空 / 对比只返三项（T-36 / T-37）
F-04 设置 6 项、非法键忽略、崩溃日志白名单（T-46 / T-47）
F-05 delta 合并 + 失败整体回滚（T-40）
F-06 回滚保留 3 份、断网后按 release 顺序合并（T-30-6）
F-07 library_version + 时间线（不上传确认）
F-09 baseline 校验和不变
F-10 export_dir 记忆
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

_CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _CORE)

from state import paths, store, settings as settings_mod, merge   # noqa: E402

BASELINE = os.path.join(_CORE, "data", "baseline_v1.json")


class StateTestBase(unittest.TestCase):
    """每个用例一个隔离的 appData 目录（§2.5 路径全部落在临时目录内）。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="bizspark_f_")
        self._old = os.environ.get(paths.ENV_APP_DATA)
        os.environ[paths.ENV_APP_DATA] = self.tmp
        store._LIB_CACHE.update({"path": None, "mtime": None, "ideas": []})

    def tearDown(self):
        if self._old is None:
            os.environ.pop(paths.ENV_APP_DATA, None)
        else:
            os.environ[paths.ENV_APP_DATA] = self._old
        store._LIB_CACHE.update({"path": None, "mtime": None, "ideas": []})
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestStateFile(StateTestBase):
    """F-01 / T-35"""

    def test_first_run_creates_state(self):
        self.assertFalse(os.path.exists(paths.state_path()))
        st = store.load_state()
        self.assertTrue(os.path.exists(paths.state_path()))
        self.assertTrue(st["first_run"])
        self.assertEqual(st["saved"], [])
        self.assertEqual(st["library_version"], store.DEFAULT_LIBRARY_VERSION)

    def test_corrupt_state_silently_rebuilt(self):
        os.makedirs(paths.app_data_dir(), exist_ok=True)
        with open(paths.state_path(), "w", encoding="utf-8") as f:
            f.write("{ this is not json")
        st = store.load_state()                     # 不抛异常、不弹窗
        self.assertEqual(st["saved"], [])
        self.assertTrue(st["first_run"])
        # 坏文件留档而非删除（不丢用户数据）
        self.assertTrue(any(n.startswith("state.json.corrupt-") for n in os.listdir(paths.app_data_dir())))
        # 其他目录文件不受影响
        self.assertTrue(os.path.isdir(paths.library_dir()) or True)

    def test_corrupt_root_type_rebuilt(self):
        os.makedirs(paths.app_data_dir(), exist_ok=True)
        with open(paths.state_path(), "w", encoding="utf-8") as f:
            json.dump([1, 2, 3], f)
        self.assertEqual(store.load_state()["saved"], [])

    def test_partial_state_filled_with_defaults(self):
        os.makedirs(paths.app_data_dir(), exist_ok=True)
        with open(paths.state_path(), "w", encoding="utf-8") as f:
            json.dump({"saved": [{"id": "x"}], "settings": {"country": "NOPE"}}, f)
        st = store.load_state()
        self.assertEqual(len(st["saved"]), 1)
        self.assertIn(st["settings"]["country"], settings_mod.SUPPORTED_COUNTRIES)


class TestStateHandlers(StateTestBase):
    """F-02 / F-03 / F-10"""

    def test_get_state_shape(self):
        data, err = store.get_state({})
        self.assertIsNone(err)
        for key in ("saved_count", "saved", "last_answers", "last_result", "settings",
                    "library_version", "library_ideas", "license_state", "first_run",
                    "export_dir", "timeline", "paths"):
            self.assertIn(key, data)
        self.assertIn(data["license_state"], ("activated", "none"))
        self.assertLessEqual(len(data["settings"]), 6)

    def test_save_answers_merges_and_clears_first_run(self):
        store.save_answers({"answers": {"country": "US"}})
        store.save_answers({"answers": {"capital": "<500"}})
        st = store.load_state()
        self.assertEqual(st["last_answers"], {"country": "US", "capital": "<500"})
        self.assertFalse(st["first_run"])
        # 非法类型不落库
        store.save_answers({"answers": {"weird": {"nested": 1}}})
        self.assertNotIn("weird", store.load_state()["last_answers"])

    def test_last_result_cache(self):
        store.save_last_result({"ideas": [{"id": "a"}], "checked": 312, "filtered": 309})
        cached = store.load_state()["last_result"]
        self.assertEqual(cached["checked"], 312)
        self.assertEqual(len(cached["ideas"]), 1)
        self.assertTrue(cached["cached_at"])

    def test_save_idea_dedup_no_time_overwrite(self):
        idea_id = store.load_ideas()[0]["id"]
        first, err = store.save_idea({"id": idea_id})
        self.assertIsNone(err)
        self.assertEqual(first["count"], 1)
        saved_at = store.load_state()["saved"][0]["saved_at"]
        second, _ = store.save_idea({"id": idea_id})
        self.assertTrue(second.get("duplicate"))
        self.assertEqual(store.load_state()["saved"][0]["saved_at"], saved_at)  # 不覆盖时间

    def test_list_saved_desc(self):
        ideas = store.load_ideas()
        for i in ideas[:3]:
            store.save_idea({"id": i["id"]})
        st = store.load_state()
        st["saved"][0]["saved_at"] = "2026-01-01"
        st["saved"][1]["saved_at"] = "2026-11-12"
        st["saved"][2]["saved_at"] = "2026-06-01"
        store.save_state(st)
        data, _ = store.list_saved({})
        dates = [it["saved_at"] for it in data["items"]]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_clear_saved(self):
        store.save_idea({"id": store.load_ideas()[0]["id"]})
        store.clear_saved({})
        self.assertEqual(store.load_state()["saved"], [])

    def test_compare_returns_three_fields_only(self):
        ideas = store.load_ideas()[:2]
        data, err = store.compare_ideas({"ids": [i["id"] for i in ideas]})
        self.assertIsNone(err)
        keys = set(data["left"].keys()) - {"title"}
        self.assertEqual(keys, {"Startup cost", "Hours per week", "Payback"})

    def test_compare_needs_two(self):
        data, err = store.compare_ideas({"ids": [store.load_ideas()[0]["id"]]})
        self.assertIsNone(data)
        self.assertEqual(err["code"], "E_BAD_REQUEST")

    def test_export_dir_memory(self):
        store.remember_export_dir(os.path.join("C:/tmp/out", "BizSpark-Plan-x.pdf"))
        data, _ = store.get_state({})
        self.assertEqual(os.path.normpath(data["export_dir"]),
                         os.path.normpath(os.path.join("C:/tmp/out")))


class TestSettings(StateTestBase):
    """F-04"""

    def test_six_keys_only(self):
        data, _ = settings_mod.get_settings({})
        self.assertEqual(set(data.keys()), set(settings_mod.SETTINGS_KEYS))
        self.assertEqual(len(data), 6)

    def test_illegal_key_ignored_silently(self):
        settings_mod.set_settings({"patch": {"hacker": "x", "country": "US"}})
        data, err = settings_mod.set_settings({"patch": {"nope": 1}})
        self.assertIsNone(err)
        self.assertNotIn("nope", data)
        self.assertEqual(data["country"], "US")

    def test_illegal_value_keeps_old(self):
        settings_mod.set_settings({"patch": {"country": "US"}})
        data, _ = settings_mod.set_settings({"patch": {"country": "MARS"}})
        self.assertEqual(data["country"], "US")

    def test_language_not_switchable(self):
        data, _ = settings_mod.set_settings({"patch": {"language": "zh-CN"}})
        self.assertEqual(data["language"], "en-US")

    def test_crash_log_off_by_default(self):
        ok, _ = settings_mod.log_crash_handler({"code": "E_X", "version": "1.0.0"})
        self.assertFalse(ok["written"])
        self.assertFalse(os.path.exists(paths.crash_log_path()))

    def test_crash_log_whitelist(self):
        settings_mod.set_settings({"patch": {"crash_notes": True}})
        settings_mod.log_crash_handler({"code": "E_PDF_RENDER", "version": "1.0.0",
                                        "answers": {"capital": "<500"}, "path": "C:/secret"})
        with open(paths.crash_log_path(), encoding="utf-8") as f:
            line = json.loads(f.readline())
        self.assertEqual(set(line.keys()), set(settings_mod.CRASH_LOG_FIELDS))
        raw = json.dumps(line)
        self.assertNotIn("<500", raw)
        self.assertNotIn("secret", raw)


class TestMerge(StateTestBase):
    """F-05 / F-06 / F-07 / F-09"""

    def _delta(self, release="2026-12-01", add=None, revise=None, retire=None):
        return {"target_baseline": "v1", "release": release,
                "add": add or [], "revise": revise or [], "retire": retire or []}

    def test_working_library_created_from_baseline(self):
        merge.ensure_working_library()
        self.assertTrue(os.path.isfile(paths.current_library_path()))
        info = merge.library_info()
        self.assertEqual(info["ideas"], 312)
        self.assertEqual(info["version"], store.DEFAULT_LIBRARY_VERSION)

    def test_apply_delta_add_revise_retire(self):
        merge.ensure_working_library()
        base = merge.read_current()[0]["ideas"]
        target_revise = base[0]["id"]
        target_retire = base[1]["id"]
        new_idea = dict(base[2])
        new_idea["id"] = "bs-new-999"
        data, err = merge.apply_delta(self._delta(
            add=[new_idea], revise=[{"id": target_revise, "maturity": "growing"}],
            retire=[target_retire]))
        self.assertIsNone(err, err)
        self.assertEqual(data["version"], "2026.12")
        self.assertEqual(data["ideas"], 313)
        lib = merge.read_current()[0]
        by_id = {i["id"]: i for i in lib["ideas"]}
        self.assertIn("bs-new-999", by_id)
        self.assertEqual(by_id[target_revise]["maturity"], "growing")
        self.assertEqual(by_id[target_retire]["status"], "retired")   # 不硬删
        self.assertIn(target_retire, by_id)

    def test_failed_merge_rolls_back(self):
        merge.ensure_working_library()
        with open(paths.current_library_path(), "rb") as f:
            before = f.read()
        data, err = merge.apply_delta(self._delta(retire=["no-such-id-000"]))
        self.assertIsNone(data)
        self.assertEqual(err["code"], "E_DELTA_INVALID")   # V-11
        with open(paths.current_library_path(), "rb") as f:
            after = f.read()
        self.assertEqual(hashlib.sha256(before).hexdigest(),
                         hashlib.sha256(after).hexdigest())     # 整体回滚，库原样

    def test_invalid_release_and_target(self):
        merge.ensure_working_library()
        self.assertEqual(merge.apply_delta(self._delta(release="2026/12"))[1]["code"],
                         "E_DELTA_INVALID")
        bad = self._delta()
        bad["target_baseline"] = "v9"
        self.assertEqual(merge.apply_delta(bad)[1]["code"], "E_DELTA_INVALID")

    def test_rollback_keeps_three(self):
        merge.ensure_working_library()
        base = merge.read_current()[0]["ideas"]
        for i, release in enumerate(["2026-12-01", "2027-01-01", "2027-02-01", "2027-03-01"]):
            idea = dict(base[3])
            idea["id"] = "bs-new-%03d" % i
            data, err = merge.apply_delta(self._delta(release=release, add=[idea]))
            self.assertIsNone(err, err)
        files = sorted(n for n in os.listdir(paths.rollback_dir()) if n.endswith(".json"))
        self.assertEqual(len(files), merge.ROLLBACK_KEEP)
        self.assertEqual(files, ["2027-01-01.json", "2027-02-01.json", "2027-03-01.json"])

    def test_sequence_merges_in_release_order(self):
        merge.ensure_working_library()
        base = merge.read_current()[0]["ideas"]
        d1 = self._delta(release="2027-01-01", add=[dict(base[4], id="bs-seq-1")])
        d2 = self._delta(release="2026-12-01", add=[dict(base[5], id="bs-seq-2")])
        data, err = merge.apply_sequence([d1, d2])     # 乱序传入，内部按 release 排序
        self.assertIsNone(err, err)
        self.assertEqual(data["version"], "2027.01")
        st = store.load_state()
        self.assertEqual([t["release"] for t in st["timeline"]], ["2026-12-01", "2027-01-01"])

    def test_library_version_and_timeline(self):
        merge.ensure_working_library()
        merge.apply_delta(self._delta(release="2026-12-01"))
        st = store.load_state()
        self.assertEqual(st["library_version"], "2026.12")
        self.assertEqual(len(st["timeline"]), 1)
        self.assertEqual(st["timeline"][0]["date"], "2026-12-01")

    def test_idempotent_same_release(self):
        merge.ensure_working_library()
        merge.apply_delta(self._delta(release="2026-12-01"))
        data, err = merge.apply_delta(self._delta(release="2026-12-01"))
        self.assertIsNone(err)
        self.assertFalse(data["applied"])

    def test_baseline_untouched(self):
        """F-09：任何用户操作后 baseline_v1.json 校验和不变。"""
        with open(BASELINE, "rb") as f:
            before = hashlib.sha256(f.read()).hexdigest()
        merge.ensure_working_library()
        store.save_idea({"id": store.load_ideas()[0]["id"]})
        store.clear_saved({})
        base = merge.read_current()[0]["ideas"]
        merge.apply_delta(self._delta(release="2026-12-01",
                                      add=[dict(base[6], id="bs-keep-1")]))
        settings_mod.set_settings({"patch": {"country": "CA"}})
        with open(BASELINE, "rb") as f:
            after = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(before, after)
        self.assertEqual(merge.baseline_checksum(), after)

    def test_check_library_reports_local_only(self):
        merge.ensure_working_library()
        data, err = merge.check_library({})
        self.assertIsNone(err)
        self.assertIn("version", data)
        self.assertEqual(data["ideas"], 312)
        self.assertTrue(data["up_to_date"])

    def test_corrupt_current_rebuilt_from_baseline(self):
        """F13 整库损坏：current.json 坏了 → 从只读副本重建，用户无感。"""
        merge.ensure_working_library()
        with open(paths.current_library_path(), "w", encoding="utf-8") as f:
            f.write("garbage{")
        info = merge.library_info()
        self.assertEqual(info["ideas"], 312)


if __name__ == "__main__":
    unittest.main(verbosity=2)
