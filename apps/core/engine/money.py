# -*- coding: utf-8 -*-
"""engine.money — 货币统一口径（PM 2026-11-14，老板反馈：选了什么货币，价格一律跟什么货币）

规则：
- 内部数值口径统一 USD（§3.2 不变），**展示层**按所选国家换算成本地货币
- 汇率静态表 fx.json：USD→本地货币的乘数（不联网取汇率）
- 展示统一用 fmt_symbol（符号+金额）：$ / CA$ / £ / A$ / S$ / ₱
  （PM 2026-11-14 老板定稿：工具面向全球用户，符号写法更亲切、像"自己人"；
   "CAD 690" 这类代码写法一律不外露。fmt_code 保留为兼容别名，输出同符号样式。）
- localize_text：把文案里的 "$NN" / "NN 美元" / "A–B 美元" 换成本地货币（定价提示等自由文本）
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

# 展示符号（CAD 用 CA$：比 C$ 更明确是"加拿大"，与 store.py 同口径）
SYMBOLS = {"USD": "$", "CAD": "CA$", "GBP": "£", "AUD": "A$", "SGD": "S$", "PHP": "₱"}

_RE_USD_SYMBOL = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)")
_RE_USD_ZH_RANGE = re.compile(r"(\d[\d,]*)\s*[–\-—]\s*(\d[\d,]*)\s*美元")
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


def fmt_symbol(amount_usd, currency, fx=None):
    """展示格式（全站唯一口径）：符号+金额，如 $NN / CA$NN / £NN / ₱NN。"""
    return "{}{}".format(SYMBOLS.get(currency, currency + " "), _group(to_local(amount_usd, currency, fx)))


def fmt_code(amount_usd, currency, fx=None):
    """兼容别名（旧调用方/契约字段仍走这里）：输出与 fmt_symbol 一致，不再外露币种码。"""
    return fmt_symbol(amount_usd, currency, fx)


def fmt_range(lo_usd, hi_usd, currency, fx=None):
    return "{} – {}".format(fmt_symbol(lo_usd, currency, fx), fmt_symbol(hi_usd, currency, fx))


def localize_text(text, currency, fx=None):
    """把自由文本里的美元金额换成本地货币符号（不改非金额文字）。

    支持 "$NN"（en）、"NN 美元"、"A–B 美元" 三种写法；currency=USD 时把"美元"统一成 "$"。
    """
    if not isinstance(text, str) or not text:
        return text
    fx = fx or load_fx()

    def _sym(m):
        return fmt_symbol(m.group(1).replace(",", ""), currency, fx)

    def _zh_range(m):
        return fmt_range(m.group(1).replace(",", ""), m.group(2).replace(",", ""), currency, fx)

    def _zh(m):
        return fmt_symbol(m.group(1).replace(",", ""), currency, fx)

    out = _RE_USD_SYMBOL.sub(_sym, text)
    out = _RE_USD_ZH_RANGE.sub(_zh_range, out)
    out = _RE_USD_ZH.sub(_zh, out)
    return out
