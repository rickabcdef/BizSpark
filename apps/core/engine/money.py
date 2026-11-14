# -*- coding: utf-8 -*-
"""engine.money — 货币统一口径（PM 2026-11-14，老板反馈：选了什么货币，价格一律跟什么货币）

规则：
- 内部数值口径统一 USD（§3.2 不变），**展示层**按所选国家换算成本地货币
- 汇率静态表 fx.json：USD→本地货币的乘数（不联网取汇率）
- 展示两种格式：fmt_code（币种码+金额，契约沿用）/ fmt_symbol（符号+金额，卡片/问卷用）
- localize_text：把文案里的 "$NN" / "NN 美元" 换成本地货币（定价提示等自由文本）
- 换算金额做友好取整：<50 取整、<500 取到 5、<5000 取到 10、其余取到 100
"""

import json
import os
import re

_CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX_PATH = os.path.join(_CORE_DIR, "data", "fx.json")

# fx.json 缺失时的兜底（USD→本地乘数，2026-11 静态值）
DEFAULT_FX = {"USD": 1.0, "CAD": 1.37, "GBP": 0.79, "AUD": 1.52, "SGD": 1.34, "PHP": 58.5}

# 国家 → 默认币种（无 per-idea overrides.currency 时使用）
COUNTRY_CURRENCY = {"US": "USD", "CA": "CAD", "GB": "GBP", "UK": "GBP",
                    "AU": "AUD", "SG": "SGD", "PH": "PHP"}

SYMBOLS = {"USD": "$", "CAD": "C$", "GBP": "£", "AUD": "A$", "SGD": "S$", "PHP": "₱"}
ZH_UNITS = {"USD": "美元", "CAD": "加元", "GBP": "英镑", "AUD": "澳元", "SGD": "新元", "PHP": "比索"}

_RE_USD_SYMBOL = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)")
_RE_USD_ZH = re.compile(r"(\d[\d,]*)\s*美元")


_fx_cache = None  # (mtime, fx) —— diagnose 全库打分会高频调用，按 mtime 缓存


def load_fx():
    """fx.json（USD→本地乘数）；缺失/脏数据回退 DEFAULT_FX。按 mtime 缓存。"""
    global _fx_cache
    try:
        m = os.path.getmtime(FX_PATH)
    except OSError:
        m = None
    if _fx_cache is not None and _fx_cache[0] == m:
        return _fx_cache[1]
    fx = dict(DEFAULT_FX)
    try:
        with open(FX_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            got = {k: float(v) for k, v in data.items()
                   if isinstance(v, (int, float)) and isinstance(k, str) and not k.startswith("_")}
            if got:
                fx = got
    except (OSError, ValueError, TypeError):
        pass
    _fx_cache = (m, fx)
    return fx


def currency_for(country, overrides=None):
    """国家 → 币种：per-idea overrides.currency 优先，缺省按国家映射，未知回退 USD。"""
    if isinstance(overrides, dict):
        cur = overrides.get(country) if country else None
        cur = cur.get("currency") if isinstance(cur, dict) else None
        if isinstance(cur, str) and cur.strip():
            return cur.strip().upper()
    return COUNTRY_CURRENCY.get(str(country or "").upper(), "USD")


def to_local(amount_usd, currency, fx=None):
    """USD 金额 → 本地整数（友好取整，half-up）。币种未知按 USD 原值。"""
    import math
    fx = fx or load_fx()
    try:
        v = float(amount_usd) * float(fx.get(currency, 1.0))
    except (TypeError, ValueError):
        return int(amount_usd or 0)
    if v < 50:
        return max(1, int(math.floor(v + 0.5)))
    if v < 500:
        return int(math.floor(v / 5.0 + 0.5)) * 5
    if v < 5000:
        return int(math.floor(v / 10.0 + 0.5)) * 10
    return int(math.floor(v / 100.0 + 0.5)) * 100


def _group(n):
    return "{:,}".format(int(n))


def fmt_code(amount_usd, currency, fx=None):
    """契约格式（engine/detail 沿用）："CAD 89"。"""
    return "{} {:,}".format(currency, to_local(amount_usd, currency, fx))


def fmt_symbol(amount_usd, currency, fx=None):
    """卡片/问卷格式：符号+金额（如 C 加元前缀）。"""
    return "{}{}".format(SYMBOLS.get(currency, currency + " "), _group(to_local(amount_usd, currency, fx)))


def fmt_range(lo_usd, hi_usd, currency, fx=None):
    return "{} – {}".format(fmt_symbol(lo_usd, currency, fx), fmt_symbol(hi_usd, currency, fx))


def localize_text(text, currency, fx=None):
    """把自由文本里的美元金额换成本地货币（不改非金额文字）。

    支持 "$NN"（en）与 "NN 美元"（zh 包）两种写法；currency=USD 时原样返回。
    """
    if not isinstance(text, str) or currency == "USD" or not text:
        return text
    fx = fx or load_fx()

    def _sym(m):
        return fmt_symbol(m.group(1).replace(",", ""), currency, fx)

    def _zh(m):
        v = to_local(m.group(1).replace(",", ""), currency, fx)
        return "{} {}".format(_group(v), ZH_UNITS.get(currency, currency))

    out = _RE_USD_SYMBOL.sub(_sym, text)
    out = _RE_USD_ZH.sub(_zh, out)
    return out
