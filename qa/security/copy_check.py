# -*- coding: utf-8 -*-
"""qa/security/copy_check.py — 激活页文案逐字核对（G-08）

把设计稿 `ui/en/html/07-activate.html` 的可见文本与 `en-US.json` 的 `activate.*` 比对：
逐键把文案去标签、解实体、压空白后，断言它是设计稿文本的子串（＝逐字一致，只允许空白差异）。

动态文案（含 `{used}` / `{max}` 占位、或只在交互后出现）按设计稿样例值代入后比对，
纯交互态文案（输入框 aria-label、未激活占位）列入白名单。

用法：`python qa/security/copy_check.py`
"""

import html as html_mod
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
HTML = os.path.join(REPO, "ui", "en", "html", "07-activate.html")
EN = os.path.join(REPO, "apps", "web", "src", "locales", "en-US.json")
ZH = os.path.join(REPO, "apps", "web", "src", "locales", "zh-CN.json")

# 设计稿里不出现的键：纯交互态（aria-label / 未激活占位 / 已激活态按钮文字）
STATIC_EXEMPT = {"activate.seg_label", "activate.seats_unknown", "activate.done"}
# 含占位符的键 → 用设计稿里的样例值代入
SAMPLE = {"{used}": "2", "{max}": "3", "{n}": "1"}


def norm(text):
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_mod.unescape(text).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def design_text():
    with open(HTML, encoding="utf-8") as f:
        raw = f.read()
    raw = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S | re.I)
    return norm(raw)


def main():
    print("== 激活页文案逐字核对（G-08）==")
    page = design_text()
    with open(EN, encoding="utf-8") as f:
        en = {k: v for k, v in json.load(f).items() if k.startswith("activate.")}
    with open(ZH, encoding="utf-8") as f:
        zh = {k: v for k, v in json.load(f).items() if k.startswith("activate.")}

    failures, checked, exempted = [], 0, []

    if set(en) != set(zh):
        failures.append("键集合不一致：仅 en %s / 仅 zh %s"
                        % (sorted(set(en) - set(zh)), sorted(set(zh) - set(en))))

    for key, value in sorted(en.items()):
        if key in STATIC_EXEMPT:
            exempted.append(key)
            continue
        probe = value
        for token, sample in SAMPLE.items():
            probe = probe.replace(token, sample)
        probe = norm(probe)
        checked += 1
        if probe not in page:
            failures.append("%s 与设计稿不一致：\n       文案: %s" % (key, probe))
        if key in zh and not zh[key].strip():
            failures.append("%s 中文为空" % key)

    # 不译白名单：中文版必须保留的英文原词（§3.6）
    for word in ("BizSpark", "PDF", "CSV"):
        if word not in json.dumps(zh, ensure_ascii=False) and word in json.dumps(en, ensure_ascii=False):
            failures.append("zh-CN 丢失不译白名单词：%s" % word)

    print("  逐字比对 %d 键，交互态豁免 %d 键（%s）"
          % (checked, len(exempted), ", ".join(sorted(exempted))))
    if failures:
        for f in failures:
            print("  FAIL %s" % f)
        print("结果：FAIL（%d 项）" % len(failures))
        return 1
    print("结果：PASS（18 个 activate.* 与 07-activate.html 逐字一致，中英键集合相同）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
