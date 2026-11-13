# -*- coding: utf-8 -*-
"""render.csv — E-07 export_csv 成本表导出（F06 步骤 9，P1）

规则（F06 步骤 9）：
- 列固定三列：`item, amount, currency`（amount 为数值，currency 单独一列）
- 与 PDF 同目录（path 是文件则取其目录，是目录则直接用）
- 仍在本地、仍归用户：不上传、不生成在线链接
- 金额按 fx 静态表换算到条目 currency（fx.json 由 D 维护，**不联网取汇率**）
"""

import csv
import json
import os
import re

_CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX_PATH = os.path.join(_CORE_DIR, "data", "fx.json")

# fx.json 缺失时的兜底（与 C 的 engine.detail.DEFAULT_FX 口径一致，不联网）
DEFAULT_FX = {"USD": 1.0, "CAD": 0.74, "GBP": 0.79, "AUD": 0.66, "SGD": 0.75, "PHP": 0.018}

CSV_HEADERS = ["item", "amount", "currency"]


def _load_fx():
    try:
        with open(FX_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data:
            return {k: float(v) for k, v in data.items() if isinstance(v, (int, float))}
    except (OSError, ValueError, TypeError):
        pass
    return dict(DEFAULT_FX)


def _slug(idea_id):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(idea_id or "idea")).strip("-").lower()
    return slug or "idea"


def csv_rows(detail):
    """从 IdeaDetail 生成三列行：item, amount, currency（amount 为换算后数值）。"""
    currency = detail.get("currency") if isinstance(detail.get("currency"), str) else "USD"
    fx = _load_fx()
    rate = fx.get(currency, 1.0)
    rows = []
    breakdown = detail.get("cost_breakdown") if isinstance(detail.get("cost_breakdown"), list) else []
    for c in breakdown:
        if not isinstance(c, dict) or not isinstance(c.get("amount"), (int, float)):
            continue  # 脏行跳过，不输出 undefined
        item = str(c.get("item") or "").strip()
        if not item:
            item = "Startup cost"
        rows.append({"item": item, "amount": round(float(c["amount"]) * rate, 2),
                     "currency": currency})
    if not rows:
        total = detail.get("cost_total")
        rows.append({"item": "Total to first invoice",
                     "amount": round(float(total) * rate, 2) if isinstance(total, (int, float)) else 0.0,
                     "currency": currency})
    return rows


def export_csv(payload):
    """E-07 handler（main.py 注册）。payload: {id, path}。返回 (data, error)。

    path 是 PDF 文件路径 → 同目录写 {slug}-costs.csv；是目录 → 直接写入该目录。
    """
    idea_id = payload.get("id") if isinstance(payload, dict) else None
    path = payload.get("path") if isinstance(payload, dict) else None
    if not idea_id:
        return None, {"code": "E_BAD_REQUEST", "message": "id is required", "recoverable": True}
    if not path or not str(path).strip():
        # 与 export_plan 一致：无路径视为用户取消，前端静默处理（T-34 口径）
        return None, {"code": "E_EXPORT_CANCELLED", "message": "save dialog cancelled",
                      "recoverable": True}
    path = os.path.abspath(str(path).strip())

    from engine import get_idea as _get_idea  # 局部导入避免循环依赖
    detail, err = _get_idea({"id": idea_id})
    if err:
        return None, err

    directory = os.path.dirname(path) if os.path.splitext(path)[1] else path
    out_path = os.path.join(directory, "BizSpark-Plan-%s-costs.csv" % _slug(idea_id))

    try:
        os.makedirs(directory, exist_ok=True)
        with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            for row in csv_rows(detail):
                writer.writerow(row)
    except (PermissionError, OSError) as exc:
        # T-34：目录不可写 → 唯一提示语义是换文件夹
        return None, {"code": "E_CSV_WRITE", "message": "Choose another folder (%s)" % exc,
                      "recoverable": True}

    return {
        "filename": os.path.basename(out_path),
        "file_name": os.path.basename(out_path),   # B 前端 cmd.ts 消费名
        "path": out_path,
        "rows": len(csv_rows(detail)),
    }, None
