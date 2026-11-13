# -*- coding: utf-8 -*-
"""render.pdf — E-03/E-04/E-05/E-08 本地单页 PDF 导出（F06 / T-25 / T-26 / T-27 / T-33 / T-34）

规则（F06）：
- reportlab 渲染**单页** A4 / Letter 自适应 PDF，9 个内容块顺序写死（与详情页一致）
- 无水印 / 无二维码 / 无在线链接 / 无分享按钮；字体 Helvetica 内置，英文版不嵌 CJK
- 全程本地写盘，不上传、不生成在线链接、不经过任何服务器
- 写盘成功返回 {filename, file_name, bytes, pages:1, path}（file_name 为 B 前端消费名）
- 目录不可写 → 仅返回可恢复错误（前端唯一提示 Choose another folder，T-34）
- 渲染异常 → E_PDF_RENDER（内部错误码，禁止展示给用户）
"""

import os
import re
import time

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, KeepTogether)

from . import detail as rd

# 单页自适应：字号从大到小逐档重排，直到恰好 1 页（T-27 pages:1）
FONT_LADDER = [9.5, 9.0, 8.5, 8.0, 7.5]
ORANGE = colors.HexColor("#E8590C")

_BLOCK_TITLES = {
    "costs": "What it costs",
    "steps": "First 7 steps",
    "channels": "First customers",
    "pitfalls": "3 pitfalls",
}


def _esc(text):
    """reportlab Paragraph 需要 XML 转义；内容均为本地字段，无外部输入注入面。"""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _slug(idea_id):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(idea_id or "idea")).strip("-").lower()
    return slug or "idea"


def _styles(base):
    lead = base * 1.05
    return {
        "eyebrow": ParagraphStyle("eyebrow", fontName="Helvetica", fontSize=base - 1,
                                  textColor=colors.HexColor("#868E96"), spaceAfter=2 * lead),
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=base + 6,
                                leading=(base + 6) * 1.15, spaceAfter=2),
        "one_liner": ParagraphStyle("one_liner", fontName="Helvetica", fontSize=base,
                                    leading=base * 1.3, textColor=colors.HexColor("#495057"),
                                    spaceAfter=6 * lead),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=base + 1,
                             leading=(base + 1) * 1.2, spaceBefore=6, spaceAfter=3),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=base,
                               leading=base * 1.3, spaceAfter=2),
        "num": ParagraphStyle("num", fontName="Helvetica", fontSize=base,
                              leading=base * 1.3, leftIndent=14, firstLineIndent=-14,
                              spaceAfter=1.5),
        "total": ParagraphStyle("total", fontName="Helvetica-Bold", fontSize=base + 1,
                                textColor=ORANGE),
        "note": ParagraphStyle("note", fontName="Helvetica", fontSize=base - 1,
                               leading=(base - 1) * 1.3, textColor=colors.HexColor("#495057"),
                               spaceAfter=2),
        "footer": ParagraphStyle("footer", fontName="Helvetica", fontSize=base - 2,
                                 textColor=colors.HexColor("#868E96"), alignment=TA_CENTER),
    }


def _build_story(view, st, cell_st):
    """F06 步骤 3：9 个内容块顺序写死，不得调序、不得增删块。"""
    story = []
    # 1 页眉小字
    story.append(Paragraph(_esc(view["eyebrow"]), st["eyebrow"]))
    # 2 标题 + one_liner
    story.append(Paragraph(_esc(view["title"]), st["title"]))
    story.append(Paragraph(_esc(view["one_liner"]), st["one_liner"]))
    # 3 What it costs 表格（逐项 + 合计）
    rows = [[Paragraph(_esc(r["item"]), cell_st["body"]), Paragraph(_esc(r["amount"]), cell_st["body"])]
            for r in view["cost_rows"]]
    rows.append([Paragraph("<b>%s</b>" % _esc(view["cost_total_label"]), cell_st["total"]),
                 Paragraph(_esc(view["cost_total"]), cell_st["total"])])
    t = Table(rows, colWidths=[70 * mm, 40 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.HexColor("#DEE2E6")),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, ORANGE),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(KeepTogether([Paragraph(_BLOCK_TITLES["costs"], st["h2"]), t]))
    # 4 First 7 steps 编号列表（01…07）
    story.append(Paragraph(_BLOCK_TITLES["steps"], st["h2"]))
    for i, s in enumerate(view["steps"], 1):
        story.append(Paragraph("%02d. %s" % (i, _esc(s)), st["num"]))
    # 5 Pricing & payback 一行
    story.append(Paragraph("Pricing &amp; payback", st["h2"]))
    story.append(Paragraph(_esc(view["pricing_payback"]), st["body"]))
    # 6 First customers 列表
    story.append(Paragraph(_BLOCK_TITLES["channels"], st["h2"]))
    for c in view["first_customers"]:
        story.append(Paragraph("• %s" % _esc(c), st["num"]))
    # 7 3 pitfalls 列表
    story.append(Paragraph(_BLOCK_TITLES["pitfalls"], st["h2"]))
    for p in view["pitfalls"]:
        story.append(Paragraph("• %s" % _esc(p), st["num"]))
    # 8 Local note 一句
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Local note:</b> %s" % _esc(view["local_note"]), st["note"]))
    # 9 页脚（固定，无页码之外的额外元素）
    story.append(Spacer(1, 6))
    story.append(Paragraph(_esc(view["footer"]), st["footer"]))
    return story


def _render_once(view, page_size, base):
    """按指定字号排版并 build 到临时文件，返回 (页数, 字节数)。"""
    tmp = view["_path"] + ".tmp"
    st = _styles(base)
    doc = SimpleDocTemplate(tmp, pagesize=page_size,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title=view["title"], author="BizSpark")
    doc.build(_build_story(view, st, st))
    size = os.path.getsize(tmp)
    return doc.page, size, tmp


def render_pdf(view, paper="A4"):
    """E-03：单页 A4/Letter 自适应渲染。view 来自 render.detail.build_pdf_view。
    返回 (tmp_path, pages, bytes)。pages 恒为 1（字号阶梯保证）。"""
    page_size = letter if str(paper).upper().startswith("LETTER") else A4
    last_err = None
    for base in FONT_LADDER:
        try:
            pages, _size, tmp = _render_once(view, page_size, base)
        except (PermissionError, OSError):
            # T-34：目录不可写/磁盘满是 IO 问题，不是版式问题 → 原样上抛换文件夹语义
            raise
        except Exception as exc:  # 版式异常才缩字号重排；最终上抛 E_PDF_RENDER（main 包装）
            last_err = exc
            continue
        if pages <= 1:
            return tmp, 1, _size
        os.remove(tmp)
    raise RuntimeError("single-page layout failed: %s" % last_err)


def export_plan(payload):
    """E-05/E-08：export_plan handler（main.py 注册）。payload: {id, path, paper?}。

    返回 (data, None)；失败返回 (None, error)。path 为空 → 取消（前端静默回详情，T-34）。
    """
    idea_id = payload.get("id") if isinstance(payload, dict) else None
    path = payload.get("path") if isinstance(payload, dict) else None
    if not idea_id:
        return None, {"code": "E_BAD_REQUEST", "message": "id is required", "recoverable": True}
    if not path or not str(path).strip():
        # 用户取消另存为 → 前端静默回详情页，不提示（F06 步骤 2 / T-34）
        return None, {"code": "E_EXPORT_CANCELLED", "message": "save dialog cancelled",
                      "recoverable": True}
    path = os.path.abspath(str(path).strip())

    # 取 IdeaDetail（C 的 get_idea：国家覆盖合并 + 派生字段）
    from engine import get_idea as _get_idea  # 局部导入避免循环依赖
    detail, err = _get_idea({"id": idea_id})
    if err:
        return None, err

    started = time.perf_counter()
    view = rd.build_pdf_view(detail)
    view["_path"] = path
    try:
        paper = payload.get("paper") if isinstance(payload.get("paper"), str) else "A4"
        tmp, pages, _size = render_pdf(view, paper=paper)
        # T-33：最终写盘仍全程本地
        os.replace(tmp, path)
    except PermissionError:
        # D-08 修复（PM）：目录不可写回附录 D 正名码 E_FS_READONLY（文案不变，仍引导换文件夹）
        return None, {"code": "E_FS_READONLY", "message": "Choose another folder",
                      "recoverable": True}
    except OSError as exc:
        # 磁盘满等其他写失败 → E_PDF_WRITE（已收编进附录 D，见 D-09 契约修订）
        return None, {"code": "E_PDF_WRITE", "message": "Choose another folder (%s)" % exc,
                      "recoverable": True}
    elapsed = time.perf_counter() - started

    data = {
        "filename": os.path.basename(path),
        "file_name": os.path.basename(path),   # B 前端 cmd.ts 消费名
        "bytes": os.path.getsize(path),
        "pages": pages,
        "path": path,
        "elapsed_ms": round(elapsed * 1000, 1),  # E-09 性能打点（≤2s 红线）
    }
    return data, None
