# -*- coding: utf-8 -*-
"""engine.detail — C-10 IdeaDetail 装配（§3.4，交 E 渲染 / B 详情页消费）

规则（§3.2/§3.4）：
- CountryOverride 按 id 挂变体：覆盖存在即用覆盖，缺失回退主条目（不复制整条）
- currency 仅影响成本展示符号，不改 min_capital 数值口径（内部统一 USD）
- 汇率来自 fx.json（D 维护的静态表），**不联网取汇率**
- 三个派生字段：cost_total（number）、cost_rows（已按 currency 格式化）、payback_hint（一句）
- 另附 B 详情页消费的兼容别名（costs/total_to_first_invoice/channels），契约字段不变
"""

import json
import os

_CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX_PATH = os.path.join(_CORE_DIR, "data", "fx.json")

# 静态汇率表兜底（fx.json 缺失时用；D 落库后以 fx.json 为准，不联网）
DEFAULT_FX = {"USD": 1.0, "CAD": 0.74, "GBP": 0.79, "AUD": 0.66, "SGD": 0.75, "PHP": 0.018}

OVERRIDE_FIELDS = ("currency", "first_customers", "compliance_note")

# D-02/D-03 修复（PM）：T-32 兜底——get_idea 页面数据与 E 渲染层同口径
# （兜底句/上限与 render/detail.py 保持一致，详情页与 PDF 文案统一）
MAX_TEXT = 220
MAX_LINE = 120
FALLBACK_PITFALL = "Double-check local rules and your numbers before you spend money."
FALLBACK_STEP = "Review what you have set up so far, then take the next small step."
FALLBACK_CHANNEL = "Ask people in your area directly."


def _s(text, fallback=""):
    if isinstance(text, str):
        cleaned = text.strip()
        if cleaned and cleaned.lower() not in ("undefined", "null", "none"):
            return cleaned
    return fallback


def _clip(text, limit):
    text = _s(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _as_list(value):
    return value if isinstance(value, list) else []


def _t32_sanitize(detail):
    """T-32 运行期兜底：恰好 7 steps / 3 pitfalls、超长截断、绝不出现空值。返回新 dict。"""
    d = dict(detail)
    d["title"] = _clip(d.get("title"), MAX_LINE)
    d["one_liner"] = _clip(d.get("one_liner"), MAX_TEXT)
    d["summary"] = d["one_liner"]  # 别名同步截断（D-03）
    steps = [_clip(s, MAX_TEXT) for s in _as_list(d.get("steps")) if _s(s)]
    while len(steps) < 7:
        steps.append(FALLBACK_STEP)
    d["steps"] = steps[:7]
    pitfalls = [_clip(p, MAX_TEXT) for p in _as_list(d.get("pitfalls")) if _s(p)]
    while len(pitfalls) < 3:
        pitfalls.append(FALLBACK_PITFALL)
    d["pitfalls"] = pitfalls[:3]
    channels = [_clip(c, MAX_LINE) for c in _as_list(d.get("first_customers")) if _s(c)]
    d["first_customers"] = channels or [FALLBACK_CHANNEL]
    d["channels"] = d["first_customers"]  # 别名同步兜底
    return d


def _load_fx():
    try:
        with open(FX_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data:
            return {k: float(v) for k, v in data.items() if isinstance(v, (int, float))}
    except (OSError, ValueError, TypeError):
        pass
    return dict(DEFAULT_FX)


def _fmt(amount, currency, fx):
    rate = fx.get(currency, 1.0)
    return "{} {:,.0f}".format(currency, amount * rate)


def assemble(idea, country=None):
    """把一条 Idea（§3.2）装配成 IdeaDetail（§3.4）。country 为空则不套覆盖。

    PM 2026-11-13：zh 包先做内容覆盖（标题/简介/步骤/坑点/渠道/成本项标签），
    金额数值与派生口径不变；缺项回退英文。
    """
    from . import zhpack  # 局部导入避免环
    idea = zhpack.overlay(idea)
    detail = {k: (list(v) if isinstance(v, list) else dict(v) if isinstance(v, dict) else v)
              for k, v in idea.items()}

    # 合并国家覆盖：覆盖存在即用，缺失回退主条目
    applied = False
    overrides = idea.get("overrides") if isinstance(idea.get("overrides"), dict) else None
    if country and overrides and country in overrides:
        ov = overrides[country]
        if isinstance(ov, dict):
            for k in OVERRIDE_FIELDS:
                if k in ov and ov[k] is not None:
                    detail[k] = ov[k]
            applied = True
    detail["_override_applied"] = applied

    # 派生字段 1：cost_total（USD 口径合计）
    costs = zhpack.apply_cost_labels(idea, detail.get("cost_breakdown") or [])
    detail["cost_breakdown"] = costs
    amounts = [c.get("amount") for c in costs
               if isinstance(c, dict) and isinstance(c.get("amount"), (int, float))]
    cost_total = float(sum(amounts)) if amounts else float(detail.get("min_capital") or 0)
    detail["cost_total"] = cost_total

    # 派生字段 2：cost_rows（按 currency 格式化；currency 仅影响展示符号）
    fx = _load_fx()
    currency = detail.get("currency") if isinstance(detail.get("currency"), str) else "USD"
    detail["currency"] = currency  # 无覆盖时显式落默认 USD，保证字段恒在
    detail["cost_rows"] = [{"item": (c.get("item") or "") if isinstance(c, dict) else "",
                            "amount": _fmt((c.get("amount") or 0) if isinstance(c, dict) else 0,
                                           currency, fx)}
                           for c in costs]

    # B 详情页消费别名：costs（KvRow 直接渲染）/ total_to_first_invoice（合计行）
    detail["costs"] = detail["cost_rows"]
    detail["total_to_first_invoice"] = _fmt(cost_total, currency, fx)

    # 派生字段 3：payback_hint（pricing_hint + payback_days 拼一句；zh 包走中文句式）
    hint = detail.get("pricing_hint") if isinstance(detail.get("pricing_hint"), str) else ""
    days = detail.get("payback_days")
    if zhpack.is_zh():
        detail["payback_hint"] = (zhpack.PAYBACK_HINT_ZH.format(hint=hint, days=int(days))
                                  if isinstance(days, (int, float)) else hint or zhpack.PAYBACK_HINT_ZH_NODAYS)
    else:
        days_part = "most founders cover costs within {} days".format(int(days)) if isinstance(days, (int, float)) \
            else "costs are typically covered early"
        detail["payback_hint"] = "{} — {}".format(hint, days_part) if hint else days_part.capitalize() + "."

    # B 兼容别名：channels（Detail.vue 渠道卡消费），契约字段仍是 first_customers
    detail["channels"] = detail.get("first_customers") or []
    detail["summary"] = detail.get("one_liner")
    return _t32_sanitize(detail)
