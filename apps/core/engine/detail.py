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
    """把一条 Idea（§3.2）装配成 IdeaDetail（§3.4）。country 为空则不套覆盖。"""
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
    costs = detail.get("cost_breakdown") or []
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

    # 派生字段 3：payback_hint（pricing_hint + payback_days 拼一句）
    hint = detail.get("pricing_hint") if isinstance(detail.get("pricing_hint"), str) else ""
    days = detail.get("payback_days")
    days_part = "most founders cover costs within {} days".format(int(days)) if isinstance(days, (int, float)) \
        else "costs are typically covered early"
    detail["payback_hint"] = "{} — {}".format(hint, days_part) if hint else days_part.capitalize() + "."

    # B 兼容别名：channels（Detail.vue 渠道卡消费），契约字段仍是 first_customers
    detail["channels"] = detail.get("first_customers") or []
    detail["summary"] = detail.get("one_liner")
    return detail
