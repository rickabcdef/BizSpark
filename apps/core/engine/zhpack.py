# -*- coding: utf-8 -*-
"""engine.zhpack — 中文包运行期文案与内容覆盖（PM 2026-11-13，老板需求：中文版全局中文）

§2.7 双构建在 en 之上叠加三层中文，全部**缺省回退英文、绝不崩**：
1. locale 判定：环境变量 BIZSPARK_LOCALE（A 壳 / 试玩桥接注入；缺省 en-US，H 的 QA 不受影响）
2. 引擎生成文案的中文镜像：why 模板池 / 答案标签 / 结果卡标签 / 回本提示 / 降级提示
3. 内容覆盖：data/zh_v1.json（id → 可见字段中文，312+3 条）；文件缺失、id 缺项、
   数量不一致一律回退英文原字段
"""

import json
import os

_DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + os.sep + ".." + os.sep + "data"
ZH_PACK_PATH = os.path.normpath(os.path.join(_DATA_DIR, "zh_v1.json"))

_overlay_cache = None


def current_locale():
    """当前语言（en-US / zh-CN）。env 在进程启动时注入，读取随时可调。"""
    v = (os.environ.get("BIZSPARK_LOCALE") or "en-US").strip()
    return "zh-CN" if v.lower().startswith("zh") else "en-US"


def is_zh():
    return current_locale() == "zh-CN"


# ---------------------------------------------------------------- 引擎文案中文镜像
CAPITAL_LABELS_ZH = {"<500": "500 美元以内", "500-2k": "500–2,000 美元",
                     "2k-10k": "2,000–10,000 美元", "10k+": "10,000 美元以上"}
HOURS_LABELS_ZH = {"<10": "每周不到 10 小时", "10-25": "每周 10–25 小时", "full": "全职投入"}
COUNTRY_NAMES_ZH = {"US": "美国", "CA": "加拿大", "UK": "英国",
                    "AU": "澳大利亚", "SG": "新加坡", "PH": "菲律宾"}
ASSET_NAMES_ZH = {"car": "一辆车", "kitchen": "自家厨房", "laptop": "一台笔记本",
                  "design": "设计手艺", "coding": "基础编程", "spare_room": "一间空房",
                  "local_network": "本地人脉"}

# 6 组中文 why 模板池（与 why.py 的 WHY_POOLS 一一对应；占位符一致；禁词规则同源）
WHY_POOLS_ZH = {
    "capital_time": [
        "资金不多、{hours}——{capital}就够开张。",
        "匹配{capital}和{hours}：不用动存款就能起步。",
        "预算轻、时间松——这一单两头都对得上。",
    ],
    "local_assets": [
        "你有{assets_list}，还有固定的本地圈子——这是本地利润最高的组合。",
        "{assets_list}加你的人脉，正是这门生意要用的全部本钱。",
        "这门生意按街区推进，{assets_list}就是全部装备。",
    ],
    "payback": [
        "大多数人几周内回本——按{hours}算，这里约 {payback_days} 天回本很现实。",
        "回本快：约 {payback_days} 天就能收回投入。",
    ],
    "online_laptop": [
        "线上就能做，{assets_list}加{hours}——本周就能在家开工。",
        "没有店面、没有库存：{assets_list}就够服务第一批付费客户。",
    ],
    "recurring": [
        "月月都有回头收入——客户一般会长期留下，和{hours}很搭。",
        "客户每月都会回来，你投入的时间持续产生回报。",
    ],
    "general": [
        "匹配你的{capital}、{hours}，以及你在{country}已有的资源（{assets_list}）。",
        "和你在{country}的预算与时间安排直接对得上。",
    ],
}
FORBIDDEN_SAFE_FALLBACK_ZH = "匹配{capital}和{hours}，用你在{country}已有的资源就能做。"

DEGRADE_NOTE_ZH = "下次可以把预算档位调高一档试试。"

PAYBACK_HINT_ZH = "{hint}，多数人约 {days} 天内回本。"
PAYBACK_HINT_ZH_NODAYS = "成本通常很快收回。"


def answer_labels():
    """why.py 用的答案标签组（中文 / 英文自动切换）。"""
    if is_zh():
        return (CAPITAL_LABELS_ZH, HOURS_LABELS_ZH, COUNTRY_NAMES_ZH, ASSET_NAMES_ZH,
                WHY_POOLS_ZH, FORBIDDEN_SAFE_FALLBACK_ZH)
    from .quiz import CAPITAL_LABELS, HOURS_LABELS, COUNTRY_NAMES, ASSET_NAMES  # noqa
    from .why import WHY_POOLS, FORBIDDEN_SAFE_FALLBACK  # noqa
    return (CAPITAL_LABELS, HOURS_LABELS, COUNTRY_NAMES, ASSET_NAMES, WHY_POOLS, FORBIDDEN_SAFE_FALLBACK)


# ---------------------------------------------------------------- 内容覆盖（zh_v1.json）
def _load_overlay():
    """懒加载中文内容包；任何异常都返回空表（回退英文，T-38 同款防御）。"""
    global _overlay_cache
    if _overlay_cache is None:
        table = {}
        try:
            with open(ZH_PACK_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                table = {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, dict)}
        except (OSError, ValueError):
            table = {}
        _overlay_cache = table
    return _overlay_cache


def overlay(idea):
    """把中文可见字段覆盖到 idea 副本上（不改入参、不改数值字段、缺项回退英文）。

    覆盖字段：title / one_liner / pricing_hint / compliance_note（标量）
             steps / pitfalls / first_customers（列表，长度必须与源一致才覆盖）
    成本项 item 标签由 overlay_cost_items 处理（需与 cost_breakdown 对齐）。
    """
    if not is_zh() or not isinstance(idea, dict):
        return idea
    entry = _load_overlay().get(str(idea.get("id")))
    if not isinstance(entry, dict):
        return idea
    out = dict(idea)
    for key in ("title", "one_liner", "pricing_hint", "compliance_note"):
        v = entry.get(key)
        if isinstance(v, str) and v.strip():
            out[key] = v
    for key in ("steps", "pitfalls", "first_customers"):
        v = entry.get(key)
        src = idea.get(key)
        if isinstance(v, list) and isinstance(src, list) and len(v) == len(src):
            out[key] = list(v)
    return out


def apply_cost_labels(idea, costs):
    """按 zh_v1.json 的 cost_items 顺序替换 item 标签（amount 一字不动；数量不齐回退）。"""
    if not is_zh() or not isinstance(idea, dict) or not isinstance(costs, list):
        return costs
    entry = _load_overlay().get(str(idea.get("id")))
    items = entry.get("cost_items") if isinstance(entry, dict) else None
    if not isinstance(items, list) or len(items) != len(costs):
        return costs
    out = []
    for src, zh_item in zip(costs, items):
        row = dict(src) if isinstance(src, dict) else src
        if isinstance(row, dict) and isinstance(zh_item, dict) \
                and isinstance(zh_item.get("item"), str):
            amt_src, amt_zh = src.get("amount") if isinstance(src, dict) else None, zh_item.get("amount")
            if amt_src == amt_zh:  # 金额必须逐条相等才覆盖标签
                row = dict(row)
                row["item"] = zh_item["item"]
        out.append(row)
    return out
