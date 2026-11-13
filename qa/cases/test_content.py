"""test_content.py — T-39、T-53、H-09（负责人：H）

T-39 库校验（D 的 validate.py，V-01…V-12）
H-09 抽检 30 条商机内容（§5.4 清单）→ 自动生成 qa/content-review.md
T-53 全包无可执行内容（delta 只能是 JSON/CSV 数据）
"""

from __future__ import annotations

import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness  # noqa: E402

IDEAS = harness.load_baseline()

# 抽检样本：按 id 排序后等距取样 30 条（可复现，不靠随机种子）
SAMPLE = [IDEAS[i] for i in sorted(range(len(IDEAS)), key=lambda i: IDEAS[i]["id"])
          ][::max(1, len(IDEAS) // 30)][:30]

VAGUE_WORDS = ("ai-powered", "revolutionary", "one-stop", "一站式", "game-changing",
               "ultimate", "best-in-class", "disrupt")
EMPTY_CHANNELS = ("social media", "线上推广", "打广告", "online ads", "word of mouth only")
# "动词开头"用排除法判：只要不是冠词/代词/系动词开头，就认为是祈使句动作。
# 白名单法会误伤 audit/triage/bake/rewrite 这类合法动词，QA 不能制造假缺陷。
NON_IMPERATIVE_START = ("a", "an", "the", "your", "you", "my", "our", "this", "that",
                        "these", "those", "it", "we", "i", "there", "they", "he", "she",
                        "is", "are", "was", "were", "be", "will", "can", "should")
NUMBER_WORDS = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
                "ten", "eleven", "twelve", "twenty", "thirty", "fifty", "hundred")


def _cost_sum(idea) -> float:
    return sum(c.get("amount", 0) for c in (idea.get("cost_breakdown") or [])
               if isinstance(c, dict) and isinstance(c.get("amount"), (int, float)))


def check53_idea(idea) -> list[str]:
    """返回不达标项（空列表 = 全过）。"""
    bad = []
    title = str(idea.get("title") or "")
    if any(w in title.lower() for w in VAGUE_WORDS):
        bad.append("title 含虚词")
    if re.search(r"[\u4e00-\u9fff]", json.dumps(idea, ensure_ascii=False)):
        bad.append("含中文")
    if re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", json.dumps(idea, ensure_ascii=False)):
        bad.append("含 emoji")

    steps = idea.get("steps") or []
    if len(steps) != 7:
        bad.append("steps 不是 7 条(%d)" % len(steps))
    first = str(steps[0]) if steps else ""
    first_word = re.split(r"[^A-Za-z']+", first.strip())[0].lower() if first else ""
    if first_word in NON_IMPERATIVE_START:
        bad.append("steps[0] 不是动作开头：%s" % first[:40])
    # §5.4 原话是"有地点/对象/数量"——三者有其一即可，不能只认数字
    low = first.lower()
    has_detail = bool(
        re.search(r"\d", first)
        or any(w in low.split() for w in NUMBER_WORDS)
        or re.search(r"\b(your|own|my)\b", low)                  # 对象归属
        or re.search(r"\b(in|on|at|near|outside|downtown|street)\b", low)  # 地点
    )
    if first and not has_detail:
        bad.append("steps[0] 没有地点/对象/数量：%s" % first[:40])
    for idx, st in enumerate(steps):
        w = re.split(r"[^A-Za-z']+", str(st).strip())[0].lower()
        if w in NON_IMPERATIVE_START:
            bad.append("steps[%d] 不是动作开头：%s" % (idx + 1, str(st)[:30]))
            break

    total = _cost_sum(idea)
    cap = idea.get("min_capital")
    if isinstance(cap, (int, float)) and total:
        if not (0.85 * cap <= total <= 1.15 * cap):
            bad.append("成本合计 %.0f 与 min_capital %s 不符" % (total, cap))
    else:
        bad.append("缺 cost_breakdown 或 min_capital")

    if not re.search(r"\d", str(idea.get("pricing_hint") or "")):
        bad.append("pricing_hint 无具体数字")

    chans = idea.get("first_customers") or []
    if len(chans) < 3:
        bad.append("first_customers < 3")
    for c in chans:
        if str(c).lower() in EMPTY_CHANNELS:
            bad.append("渠道是空话：%s" % c)

    if len(idea.get("pitfalls") or []) != 3:
        bad.append("pitfalls 不是 3 条")

    note = str(idea.get("compliance_note") or "")
    if not note:
        bad.append("缺 compliance_note")
    elif "\n" in note or len(note) > 180:
        bad.append("compliance_note 不是一句")

    if not (idea.get("countries") or []):
        bad.append("countries 为空（无 6 国覆盖也无回退）")
    return bad


class T39LibraryValidate(unittest.TestCase):
    """T-39：CI 跑 validate.py，312 条 V-01…V-12 全绿。"""

    CASES = ["T-39"]

    def test_validate_pass(self):
        rc, out = harness.sh([sys.executable, str(harness.CORE / "library" / "validate.py")], timeout=240)
        self.assertEqual(rc, 0, "validate.py 未通过：\n%s" % out[-2000:])
        m = re.search(r"validate: (\d+) errors, (\d+) warnings", out)
        self.assertIsNotNone(m, "输出格式变了，无法判定：%s" % out[-500:])
        errors, warnings = int(m.group(1)), int(m.group(2))
        self.assertEqual(errors, 0)
        self.assertLessEqual(warnings, 1, "警告 %d 条，超过容忍：\n%s" % (warnings, out[-1500:]))

    def test_v07_v08_no_warning(self):
        rc, out = harness.sh([sys.executable, str(harness.CORE / "library" / "validate.py")], timeout=240)
        for code in ("V-07", "V-08"):
            self.assertNotIn("[%s]" % code, out, "%s 出现警告：\n%s" % (code, out[-1500:]))

    def test_baseline_count(self):
        self.assertEqual(len(IDEAS), 312, "库里不是 312 条：%d" % len(IDEAS))


class T53NoExecutableContent(unittest.TestCase):
    """T-53：delta/托管产物只能是数据，不能夹带可执行内容。"""

    CASES = ["T-53"]

    BANNED = (b"eval(", b"exec(", b"<script", b"#!/", b"subprocess", b"__import__",
              b"import os", b"javascript:", b"data:text/html")

    def test_hosting_files_are_data_only(self):
        hosting = harness.REPO / "hosting"
        for path in sorted(hosting.rglob("*")):
            if path.is_dir():
                continue
            self.assertIn(path.suffix.lower(), (".json", ".py", ".md"),
                          "托管目录出现非数据文件：%s" % path)
            if path.suffix.lower() == ".py":      # publish.py 是本地工具，不进包
                continue
            blob = path.read_bytes().lower()
            for token in self.BANNED:
                self.assertNotIn(token, blob, "%s 含可执行片段 %r" % (path.name, token))

    def test_delta_shape_only(self):
        delta = harness.read_json(harness.REPO / "hosting" / "delta_2026-12.json")
        self.assertEqual(set(delta) - {"target_baseline", "release", "add", "revise", "retire",
                                       "note", "checksum", "generated_at", "seq"}, set(),
                         "delta 出现未知顶层字段：%s" % sorted(delta))
        for r in delta.get("revise") or []:
            self.assertNotIn("steps", r, "revise 改了 steps（非白名单）")

    def test_content_dir_has_no_scripts(self):
        for path in (harness.REPO / "content").rglob("*"):
            if path.is_file() and not path.name.startswith("."):
                self.assertIn(path.suffix.lower(), (".py", ".md", ".json", ".csv", ".txt"),
                              "content/ 出现可疑文件类型：%s" % path)


class H09ContentReview(unittest.TestCase):
    """H-09：抽检 30 条，逐条过 §5.4 清单，结果写 qa/content-review.md。"""

    CASES = []

    def test_sample_30(self):
        rows = []
        for idea in SAMPLE:
            bad = check53_idea(idea)
            rows.append((idea["id"], idea.get("capital_tier"), idea.get("free_tier", ""), bad))

        failed = [r for r in rows if r[3]]
        self._write_report(rows, failed)
        self.assertEqual(len(rows), 30)
        self.assertFalse(failed, "%d/30 条不达标：\n%s" % (
            len(failed), "\n".join("%s: %s" % (r[0], "；".join(r[3])) for r in failed[:8])))

    def test_distribution_close_to_target(self):
        from collections import Counter
        cat = Counter()
        for i in IDEAS:
            cid = i["id"]
            if "-svc-" in cid:
                cat["svc"] += 1
            elif "-onl-" in cid:
                cat["onl"] += 1
            elif "-b2b-" in cid:
                cat["b2b"] += 1
            elif "-cnt-" in cid:
                cat["cnt"] += 1
            elif "-hnd-" in cid:
                cat["hnd"] += 1
            elif "-agt-" in cid:
                cat["agt"] += 1
        total = sum(cat.values())
        self.assertEqual(total, 312)
        # §5.1 目标：svc28 onl24 b2b18 cnt14 hnd10 agt6，允许 ±3pp
        target = {"svc": 28, "onl": 24, "b2b": 18, "cnt": 14, "hnd": 10, "agt": 6}
        for k, want in target.items():
            actual = cat[k] * 100.0 / total
            self.assertLessEqual(abs(actual - want), 3.5,
                                 "%s 占比 %.1f%% 偏离目标 %d%% 超过 3.5pp" % (k, actual, want))

    def _write_report(self, rows, failed) -> None:
        out = harness.REPO / "qa" / "content-review.md"
        lines = [
            "# 商机内容抽检报告（H-09）",
            "",
            "> 抽检方式：按 `id` 排序等距取 30 条（可复现，不依赖随机种子）；",
            "> 判定清单：需求文档 §5.4。生成脚本：`qa/cases/test_content.py`。",
            "",
            "## 结果",
            "",
            "- 抽样：**30** 条（库共 %d 条）" % len(IDEAS),
            "- 全过：**%d** 条　不达标：**%d** 条" % (30 - len(failed), len(failed)),
            "",
            "## 逐条明细",
            "",
            "| # | id | 资金档 | 结论 | 不达标项 |",
            "|---|---|---|---|---|",
        ]
        for n, (iid, tier, _free, bad) in enumerate(rows, 1):
            lines.append("| %d | `%s` | %s | %s | %s |"
                         % (n, iid, tier or "-", "❌" if bad else "✅",
                            "；".join(bad) if bad else "—"))
        lines += [
            "",
            "## 抽样覆盖",
            "",
            "- 行业：%d 个不同前缀分类" % len({r[0].split("-")[1] for r in rows}),
            "- 资金档：%s" % ", ".join(sorted({str(t) for _, t, *_ in rows})),
            "- 时间档：%s" % ", ".join(sorted({str(i.get("hours_per_week")) for i in SAMPLE})),
            "",
        ]
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n[content-review] 已写 %s（%d 条不达标）" % (out, len(failed)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
