# -*- coding: utf-8 -*-
"""render.pdf — E-03/E-04/E-05/E-08 本地单页 PDF 导出（F06 / T-25 / T-26 / T-27 / T-33 / T-34）

规则（F06）：
- reportlab 渲染**单页** A4 / Letter 自适应 PDF，9 个内容块顺序写死（与详情页一致）
- 无水印 / 无二维码 / 无在线链接 / 无分享按钮
- 全程本地写盘，不上传、不生成在线链接、不经过任何服务器
- 写盘成功返回 {filename, file_name, bytes, pages:1, path}（file_name 为 B 前端消费名）
- 目录不可写 → 仅返回可恢复错误（前端唯一提示 Choose another folder，T-34）
- 渲染异常 → E_PDF_RENDER（内部错误码，禁止展示给用户）

PM 2026-11-14（老板反馈）：① 中文导出内容乱码 → 检测到 CJK 文本时改用
含中文字形的字体（Windows 微软雅黑/黑体，兜底 STSong-Light CID）；
② 块标题随语言本地化；③ 中文版默认文件名为「BizSpark-方案-<标题>.pdf」
（payload.path 传目录时自动命名，英文版仍为 BizSpark-Plan-<id>.pdf）。
"""

import os
import re
import time

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, KeepTogether)

from . import detail as rd

# 单页自适应：字号从大到小逐档重排，直到恰好 1 页（T-27 pages:1）
FONT_LADDER = [9.5, 9.0, 8.5, 8.0, 7.5]
ORANGE = colors.HexColor("#E8590C")

_FONT = None  # (regular, bold)；懒注册一次


def _try_register(name, candidates):
    """按候选顺序注册第一个可用的 TTF/TTC 字体，成功返回字体名。"""
    for path, idx in candidates:
        try:
            if not os.path.isfile(path):
                continue
            if idx is None:
                pdfmetrics.registerFont(TTFont(name, path))
            else:
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=idx))
            return name
        except Exception:
            continue
    return None


def _cjk_fonts():
    """返回 (regular, bold) 字体名：优先系统 CJK 字体，兜底 STSong-Light CID。"""
    global _FONT
    if _FONT:
        return _FONT
    win = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    reg = _try_register("BSCJK", [
        (os.path.join(win, "msyh.ttc"), 0), (os.path.join(win, "msyh.ttf"), None),
        (os.path.join(win, "simsun.ttc"), 0), (os.path.join(win, "simhei.ttf"), None),
    ])
    bold = _try_register("BSCJK-B", [
        (os.path.join(win, "msyhbd.ttc"), 0), (os.path.join(win, "simhei.ttf"), None),
    ]) if reg else None
    if not reg:
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            reg = "STSong-Light"
        except Exception:
            reg = "Helvetica"
    _FONT = (reg, bold or reg)
    return _FONT


def _has_cjk(view):
    """视图里任一文本含 CJK 字符就需要中文字体（en 包标题也可能带中文变体）。"""
    for k, v in view.items():
        if k.startswith("_") or not isinstance(v, str):
            continue
        if any("\u2e80" <= ch <= "\u9fff" or "\u30a0" <= ch <= "\u30ff" for ch in v):
            return True
    return False


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


def _safe_title(name, limit=48):
    """文件名安全化：去非法字符与首尾空白/点，限长（中文标题一字一位）。"""
    s = re.sub(r'[\\/:*?"<>|\r\n\t]+', " ", str(name or "")).strip(" .")
    return (s[:limit].rstrip(" .")) or "plan"


def _default_pdf_name(detail, view):
    """默认文件名：中文版「BizSpark-方案-<标题>.pdf」，英文版沿用 id slug。"""
    if rd._zh():
        return "BizSpark-方案-%s.pdf" % _safe_title(view.get("title") or detail.get("id") or "plan")
    return "BizSpark-Plan-%s.pdf" % _slug(detail.get("id"))


def _styles(base, font_reg="Helvetica", font_bold="Helvetica-Bold"):
    lead = base * 1.05
    return {
        "eyebrow": ParagraphStyle("eyebrow", fontName=font_reg, fontSize=base - 1,
                                  textColor=colors.HexColor("#868E96"), spaceAfter=2 * lead),
        "title": ParagraphStyle("title", fontName=font_bold, fontSize=base + 6,
                                leading=(base + 6) * 1.15, spaceAfter=2),
        "one_liner": ParagraphStyle("one_liner", fontName=font_reg, fontSize=base,
                                    leading=base * 1.3, textColor=colors.HexColor("#495057"),
                                    spaceAfter=6 * lead),
        "h2": ParagraphStyle("h2", fontName=font_bold, fontSize=base + 1,
                             leading=(base + 1) * 1.2, spaceBefore=6, spaceAfter=3),
        "body": ParagraphStyle("body", fontName=font_reg, fontSize=base,
                               leading=base * 1.3, spaceAfter=2),
        "num": ParagraphStyle("num", fontName=font_reg, fontSize=base,
                              leading=base * 1.3, leftIndent=14, firstLineIndent=-14,
                              spaceAfter=1.5),
        "total": ParagraphStyle("total", fontName=font_bold, fontSize=base + 1,
                                textColor=ORANGE),
        "note": ParagraphStyle("note", fontName=font_reg, fontSize=base - 1,
                               leading=(base - 1) * 1.3, textColor=colors.HexColor("#495057"),
                               spaceAfter=2),
        "footer": ParagraphStyle("footer", fontName=font_reg, fontSize=base - 2,
                                 textColor=colors.HexColor("#868E96"), alignment=TA_CENTER),
    }


def _build_story(view, st, cell_st):
    """F06 步骤 3：9 个内容块顺序写死，不得调序、不得增删块。

    PM 2026-11-14：块标题走 view 的本地化标题（h_* 键），缺失回退英文常量。
    """
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
    story.append(KeepTogether([Paragraph(_esc(view.get("h_costs") or _BLOCK_TITLES["costs"]), st["h2"]), t]))
    # 4 First 7 steps 编号列表（01…07）
    story.append(Paragraph(_esc(view.get("h_steps") or _BLOCK_TITLES["steps"]), st["h2"]))
    for i, s in enumerate(view["steps"], 1):
        story.append(Paragraph("%02d. %s" % (i, _esc(s)), st["num"]))
    # 5 Pricing & payback 一行
    story.append(Paragraph(_esc(view.get("h_pricing") or "Pricing &amp; payback"), st["h2"]))
    story.append(Paragraph(_esc(view["pricing_payback"]), st["body"]))
    # 6 First customers 列表
    story.append(Paragraph(_esc(view.get("h_channels") or _BLOCK_TITLES["channels"]), st["h2"]))
    for c in view["first_customers"]:
        story.append(Paragraph("• %s" % _esc(c), st["num"]))
    # 7 3 pitfalls 列表
    story.append(Paragraph(_esc(view.get("h_pitfalls") or _BLOCK_TITLES["pitfalls"]), st["h2"]))
    for p in view["pitfalls"]:
        story.append(Paragraph("• %s" % _esc(p), st["num"]))
    # 8 Local note 一句
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>%s</b> %s" % (_esc(view.get("h_note") or "Local note:"),
                                             _esc(view["local_note"])), st["note"]))
    # 9 页脚（固定，无页码之外的额外元素）
    story.append(Spacer(1, 6))
    story.append(Paragraph(_esc(view["footer"]), st["footer"]))
    return story


def _render_once(view, page_size, base):
    """按指定字号排版并 build 到临时文件，返回 (页数, 字节数)。"""
    tmp = view["_path"] + ".tmp"
    reg, bold = _cjk_fonts() if _has_cjk(view) else ("Helvetica", "Helvetica-Bold")
    st = _styles(base, font_reg=reg, font_bold=bold)
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
    # PM 2026-11-14：country 缺省回退问卷答案（货币口径全链路一致）
    from engine import get_idea as _get_idea  # 局部导入避免循环依赖
    from engine import answers_country as _answers_country
    country = payload.get("country") if isinstance(payload.get("country"), str) else None
    if not country or not country.strip():
        country = _answers_country()
    detail, err = _get_idea({"id": idea_id, "country": country})
    if err:
        return None, err

    started = time.perf_counter()
    view = rd.build_pdf_view(detail)

    # PM 2026-11-14：path 传目录（无 .pdf 后缀）时按语言自动命名
    # —— 中文「BizSpark-方案-<标题>.pdf」，英文「BizSpark-Plan-<id>.pdf」
    raw = str(path).strip()
    if not raw.lower().endswith(".pdf"):
        os.makedirs(raw, exist_ok=True)
        raw = os.path.join(raw, _default_pdf_name(detail, view))
    path = os.path.abspath(raw)
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
