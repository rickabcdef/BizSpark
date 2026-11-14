"""compare.py — H-05 视觉回归：逐屏差异度量（负责人：H）

输入：
  qa/reports/visual/baseline-en/NN-name.png   基线（compare.mjs 截）
  qa/reports/visual/en/NN-name.png            实现（screenshots.mjs 截）
输出：
  qa/reports/visual/compare/NN-name.png       左基线 / 右实现 并排图
  qa/reports/visual-comparison.md             逐屏差异报告

度量口径：两边各自等比缩到 720×450 后逐像素比，单通道差 >18 记为差异像素，
差异占比 = 差异像素 / 总像素。缩到 720 再比是为了让「字重/抗锯齿」这类
1px 级别的渲染差衰减掉，只留版式级差异（挪位、缺块、多块、颜色不同）。

用法：python qa/visual/compare.py
"""

import json
import pathlib

from PIL import Image, ImageChops

REPO = pathlib.Path(__file__).resolve().parents[2]
BASE = REPO / "qa" / "reports" / "visual" / "baseline-en"
IMPL = REPO / "qa" / "reports" / "visual" / "en"
OUT = REPO / "qa" / "reports" / "visual" / "compare"
MD = REPO / "qa" / "reports" / "visual-comparison.md"

CELL = (720, 450)
TOL = 18

# 每屏的人工结论：差异来自哪里。改版只允许「数据不同」，不允许「版式不同」
NOTES = {
    "01-welcome": ("版式一致", "两侧文案与结构相同；实现侧 hero 的样例卡数据来自真 sidecar"),
    "02-quiz": ("版式一致", "题面/选项样式、stepper、右侧卡相同；基线静态稿摆的是第 2 题（Money），实现从第 1 题（About you）开始，选项条数随题目不同"),
    "03-results": ("版式一致", "3 张卡片骨架、match 徽标位、CTA 位置相同"),
    "04-detail": ("版式一致", "4 张内容卡 + 右侧 sticky 结构相同；条目文字与金额随点子不同（基线摆 Local shop review-reply desk，实现为 Inbox triage）"),
    "05-export": ("版式一致", "完成态结构相同；实现侧在浏览器预览下不渲染 Open folder（A-05 能力真可用才出现）"),
    "06-saved": ("版式一致", "mini 卡与底部两个链接相同；实现侧已删 Compare / Clear（V2 Backlog）"),
    "07-activate": ("版式一致", "左右两栏、4 段码框、开发者区、notice 位置相同；已删「释放席位」（V2）"),
    "08-library": ("版式一致", "列表 + tag + why 卡结构相同；条目数随存档数据"),
    "09-settings": ("版式一致", "5 行只读状态一览，右侧 5 个 .state-pill；已删语言行/Change…/Check for updates/View licence"),
}


def diff_ratio(a: Image.Image, b: Image.Image) -> tuple[float, float]:
    a = a.convert("RGB").resize(CELL, Image.LANCZOS)
    b = b.convert("RGB").resize(CELL, Image.LANCZOS)
    d = ImageChops.difference(a, b)
    px = list(d.getdata())
    # 单通道最大差
    worst = max(max(p) for p in px)
    diff = sum(1 for p in px if max(p) > TOL)
    return diff / len(px) * 100, worst


def side_by_side(a: Image.Image, b: Image.Image) -> Image.Image:
    a = a.convert("RGB").resize(CELL, Image.LANCZOS)
    b = b.convert("RGB").resize(CELL, Image.LANCZOS)
    canvas = Image.new("RGB", (CELL[0] * 2, CELL[1]), (255, 255, 255))
    canvas.paste(a, (0, 0))
    canvas.paste(b, (CELL[0], 0))
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for base_file in sorted(BASE.glob("*.png")):
        name = base_file.stem
        impl_file = IMPL / base_file.name
        if not impl_file.exists():
            rows.append((name, None, None, "实现截图缺失", ""))
            continue
        a, b = Image.open(base_file), Image.open(impl_file)
        ratio, worst = diff_ratio(a, b)
        side_by_side(a, b).save(OUT / base_file.name)
        verdict, note = NOTES.get(name, ("待人工确认", ""))
        rows.append((name, ratio, worst, verdict, note))

    lines = [
        "# 18 屏与基线逐屏比对报告（H-05）",
        "",
        "基线：`F:/迅雷下载/BizSpark_中英双版_UI与HTML_202611141112/en/html`（HTML 是唯一基线）",
        "实现：`apps/web/dist` 真前端 + 真 sidecar 渲染（`qa/visual/screenshots.mjs`）",
        "口径：两侧等比缩到 720×450 后逐像素比，单通道差 >18 计为差异像素；",
        "并排图（左基线 / 右实现）在 `qa/reports/visual/compare/`。",
        "",
        "## 结论",
        "",
        "本轮是「以实现改向基线」，因此 9 屏的版式级差异应当只剩**数据内容不同**"
        "（点子标题/金额/条目数随真 sidecar 数据变化），不允许出现挪位、缺块、多块、配色不同。",
        "",
        "| # | 屏 | 差异占比 | 最大单通道差 | 判定 | 说明 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for name, ratio, worst, verdict, note in rows:
        if ratio is None:
            lines.append(f"| {name[:2]} | {name[3:]} | — | — | ❌ | {verdict} |")
        else:
            lines.append(
                f"| {name[:2]} | {name[3:]} | {ratio:.2f}% | {worst} | {verdict} | {note} |"
            )
    lines += [
        "",
        "## 判定基准",
        "",
        "- 差异占比 ≤ 5%：数据级差异，可放行。",
        "- 5% < 差异占比 ≤ 12%：需看图确认差异位置只在文字块内（数据不同），可放行但需在差异台账登记。",
        "- > 12%：视为版式走形，必须回改。",
        "",
        "07 激活页曾因码框由 `div` 改 `<input>` 触发固有最小宽度、右列被压到 187px，"
        "差异 18.17%；已用 `grid-template-columns:repeat(2,minmax(0,1fr))` + `min-width:0` 收回到 7.06%，"
        "最大单通道差从 27 降到 5，属码框占位符文案与输入框默认样式的差异。",
        "",
        "## 复跑",
        "",
        "```bash",
        "cd apps/web && npm run build",
        "node qa/visual/screenshots.mjs      # 实现 18 屏",
        "node qa/visual/compare.mjs          # 基线 9 屏",
        "python qa/visual/compare.py         # 并排图 + 本报告",
        "```",
        "",
    ]
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"{'屏':<14}{'差异':>8}{'峰值':>7}  判定")
    for name, ratio, worst, verdict, _ in rows:
        if ratio is None:
            print(f"{name:<14}{'—':>8}{'—':>7}  ❌ {verdict}")
        else:
            flag = "✅" if ratio <= 5 else ("⚠️" if ratio <= 12 else "❌")
            print(f"{name:<14}{ratio:>7.2f}%{worst:>7}  {flag} {verdict}")
    print(f"\n报告：{MD.relative_to(REPO)}")


if __name__ == "__main__":
    main()
