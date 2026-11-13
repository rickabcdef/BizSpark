# -*- coding: utf-8 -*-
"""render.detail — E-01/E-02/E-06 详情渲染视图装配（§3.4 / F05 / T-21 / T-32）

职责边界：
- IdeaDetail 的核心装配（国家覆盖合并 + cost_total / cost_rows / payback_hint 派生）
  由 C 的 engine.detail.assemble() 完成（C-10），本模块**只做渲染视图**，不重复派生逻辑。
- 本模块产出：① 4 个内容卡的渲染数据（顺序照 ui/en/html/04-detail.html DOM，写死）；
  ② PDF 专用行（pricing & payback / local note）；③ 脏字段兜底（不出现 undefined）。
- 定价（pricing_hint / payback_hint）与合规（compliance_note）**只进本视图与 PDF**，
  详情页不新增可见模块（F05 口径澄清，E 不得往 cards 里加第五张卡）。

铁律：内容 100% 来自本地字段，渲染不依赖网络；任何字段缺失都有兜底句，绝不输出 undefined/None。
"""

# F05 步骤 3：4 个内容卡，顺序写死（与 04-detail.html DOM 完全一致）
CARD_ORDER = ("costs", "steps", "channels", "pitfalls")

# T-32 兜底句：运行期脏数据缺 pitfalls / steps 时的库内通用兜底句（英文，与对外文案一致）
FALLBACK_PITFALL = "Double-check local rules and your numbers before you spend money."
FALLBACK_STEP = "Review what you have set up so far, then take the next small step."

# T-32 超长截断上限（字符）：PDF 单页版式安全值；详情页由 B 的 line-clamp 兜底
MAX_TEXT = 220
MAX_LINE = 120


def _s(text, fallback=""):
    """T-32：任何字段最终都落成字符串，绝不出现 None / 'undefined'。"""
    if isinstance(text, str):
        cleaned = text.strip()
        if cleaned and cleaned.lower() not in ("undefined", "null", "none"):
            return cleaned
    return fallback


def _clip(text, limit):
    """T-32：超长文案截断，加省略号，不撑破版面。"""
    text = _s(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _as_list(value):
    return value if isinstance(value, list) else []


def sanitize(detail):
    """E-06：对 IdeaDetail 做渲染前清洗——缺项兜底、超长截断。返回新 dict，不改入参。"""
    d = dict(detail) if isinstance(detail, dict) else {}
    d["title"] = _clip(d.get("title"), MAX_LINE)
    d["one_liner"] = _clip(d.get("one_liner"), MAX_TEXT)
    # steps 恰好 7 条展示（不足补兜底句，多余截到 7；§3.2 契约是恰好 7，脏数据只影响渲染）
    steps = [_clip(s, MAX_TEXT) for s in _as_list(d.get("steps")) if _s(s)]
    while len(steps) < 7:
        steps.append(FALLBACK_STEP)
    d["steps"] = steps[:7]
    # pitfalls 恰好 3 条展示（缺第 3 条是 T-32 主用例，用库内通用兜底句补齐）
    pitfalls = [_clip(p, MAX_TEXT) for p in _as_list(d.get("pitfalls")) if _s(p)]
    while len(pitfalls) < 3:
        pitfalls.append(FALLBACK_PITFALL)
    d["pitfalls"] = pitfalls[:3]
    # first_customers：缺覆盖回退主条目（C 已合并），渲染层再兜底防空白
    channels = [_clip(c, MAX_LINE) for c in _as_list(d.get("first_customers")) if _s(c)]
    d["first_customers"] = channels or ["Ask people in your area directly."]
    # 成本行：缺失时给一条说明行，合计回退既有口径（C 已派生，此处只防空白）
    rows = d.get("cost_rows") if isinstance(d.get("cost_rows"), list) else []
    d["cost_rows"] = rows or [{"item": "Startup costs", "amount": _s(d.get("total_to_first_invoice"), "-")}]
    d["cost_total"] = d.get("cost_total") if isinstance(d.get("cost_total"), (int, float)) else 0.0
    d["total_to_first_invoice"] = _s(d.get("total_to_first_invoice"), "-")
    return d


def _zh():
    """PM 2026-11-13：zh 包 PDF 文案中文镜像（en 缺省不变）。"""
    try:
        from engine import zhpack
        return zhpack.is_zh()
    except ImportError:
        return False


def build_cards(detail):
    """E-02：4 个内容卡渲染数据，顺序照 04-detail.html DOM，写死不加第五张卡。

    返回 [{key, title, kind, rows/items}]；定价与合规字段不进 cards（F05 口径澄清）。
    zh 包卡片标题走中文（PM 2026-11-13）。
    """
    d = sanitize(detail)
    if _zh():
        cards = [
            {"key": "costs", "title": "起步要花多少钱", "kind": "kv",
             "rows": [{"item": _clip(r.get("item"), MAX_LINE), "amount": _s(r.get("amount"), "-")}
                      for r in d["cost_rows"]],
             "total_label": "开出第一张账单前的总投入",
             "total_value": d["total_to_first_invoice"]},
            {"key": "steps", "title": "最前面的 7 步", "kind": "ol",
             "items": d["steps"]},
            {"key": "channels", "title": "第一批客户从哪里来", "kind": "pills",
             "items": d["first_customers"]},
            {"key": "pitfalls", "title": "最容易做错的三个地方", "kind": "warn",
             "items": d["pitfalls"]},
        ]
    else:
        cards = [
            {"key": "costs", "title": "What it costs to start", "kind": "kv",
             "rows": [{"item": _clip(r.get("item"), MAX_LINE), "amount": _s(r.get("amount"), "-")}
                      for r in d["cost_rows"]],
             "total_label": "Total to first invoice",
             "total_value": d["total_to_first_invoice"]},
            {"key": "steps", "title": "Your first 7 steps", "kind": "ol",
             "items": d["steps"]},
            {"key": "channels", "title": "Where the first customers come from", "kind": "pills",
             "items": d["first_customers"]},
            {"key": "pitfalls", "title": "Three ways people get this wrong", "kind": "warn",
             "items": d["pitfalls"]},
        ]
    assert [c["key"] for c in cards] == list(CARD_ORDER), "card order is frozen by F05"
    return cards


def payback_line(detail):
    """PDF 第 5 块 `Pricing & payback` 一行（C 已派生 payback_hint，这里只清洗截断）。"""
    if _zh():
        return _clip(detail.get("payback_hint"), MAX_TEXT) or "定价与回本：按本地数字估算。"
    return _clip(detail.get("payback_hint"), MAX_TEXT) or "Pricing and payback: see your local numbers."


def local_note(detail):
    """PDF 第 8 块 `Local note` 一句（compliance_note；脏数据兜底句，页面无 undefined）。"""
    if _zh():
        return _clip(detail.get("compliance_note"), MAX_TEXT) or "开工前请先确认你所在城市与国家的规定。"
    return _clip(detail.get("compliance_note"), MAX_TEXT) or \
        "Check your city and country rules before you start."


def build_pdf_view(detail):
    """E-03 输入：把 IdeaDetail 整理成 PDF 9 块固定顺序所需的数据（与详情页一致）。"""
    d = sanitize(detail)
    zh = _zh()
    return {
        "eyebrow": "BizSpark · 一页方案" if zh else "BizSpark · One-page plan",
        "title": d["title"],
        "one_liner": d["one_liner"],
        "cost_rows": [{"item": _clip(r.get("item"), MAX_LINE), "amount": _s(r.get("amount"), "-")}
                      for r in d["cost_rows"]],
        "cost_total_label": "开出第一张账单前的总投入" if zh else "Total to first invoice",
        "cost_total": d["total_to_first_invoice"],
        "steps": d["steps"],
        "pricing_payback": payback_line(d),
        "first_customers": d["first_customers"],
        "pitfalls": d["pitfalls"],
        "local_note": local_note(d),
        "footer": "BizSpark · 一次买断 · 本机生成" if _zh() else "BizSpark · one-time purchase · generated on this device",
    }
