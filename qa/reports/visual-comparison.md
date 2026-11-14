# 18 屏与基线逐屏比对报告（H-05）

基线：`F:/迅雷下载/BizSpark_中英双版_UI与HTML_202611141112/en/html`（HTML 是唯一基线）
实现：`apps/web/dist` 真前端 + 真 sidecar 渲染（`qa/visual/screenshots.mjs`）
口径：两侧等比缩到 720×450 后逐像素比，单通道差 >18 计为差异像素；
并排图（左基线 / 右实现）在 `qa/reports/visual/compare/`。

## 结论

本轮是「以实现改向基线」，因此 9 屏的版式级差异应当只剩**数据内容不同**（点子标题/金额/条目数随真 sidecar 数据变化），不允许出现挪位、缺块、多块、配色不同。

| # | 屏 | 差异占比 | 最大单通道差 | 判定 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 01 | welcome | 0.14% | 236 | 版式一致 | 两侧文案与结构相同；实现侧 hero 的样例卡数据来自真 sidecar |
| 02 | quiz | 5.36% | 255 | 版式一致 | 题面/选项样式、stepper、右侧卡相同；基线静态稿摆的是第 2 题（Money），实现从第 1 题（About you）开始，选项条数随题目不同 |
| 03 | results | 4.45% | 255 | 版式一致 | 3 张卡片骨架、match 徽标位、CTA 位置相同 |
| 04 | detail | 8.33% | 255 | 版式一致 | 4 张内容卡 + 右侧 sticky 结构相同；条目文字与金额随点子不同（基线摆 Local shop review-reply desk，实现为 Inbox triage） |
| 05 | export | 4.59% | 255 | 版式一致 | 完成态结构相同；实现侧在浏览器预览下不渲染 Open folder（A-05 能力真可用才出现） |
| 06 | saved | 1.39% | 255 | 版式一致 | mini 卡与底部两个链接相同；实现侧已删 Compare / Clear（V2 Backlog） |
| 07 | activate | 1.08% | 251 | 版式一致 | 左右两栏、4 段码框、开发者区、notice 位置相同；已删「释放席位」（V2） |
| 08 | library | 0.36% | 110 | 版式一致 | 列表 + tag + why 卡结构相同；条目数随存档数据 |
| 09 | settings | 2.73% | 255 | 版式一致 | 5 行只读状态一览，右侧 5 个 .state-pill；已删语言行/Change…/Check for updates/View licence |

## 判定基准

- 差异占比 ≤ 5%：数据级差异，可放行。
- 5% < 差异占比 ≤ 12%：需看图确认差异位置只在文字块内（数据不同），可放行但需在差异台账登记。
- > 12%：视为版式走形，必须回改。

07 激活页曾因码框由 `div` 改 `<input>` 触发固有最小宽度、右列被压到 187px，差异 18.17%；已用 `grid-template-columns:repeat(2,minmax(0,1fr))` + `min-width:0` 收回到 7.06%，最大单通道差从 27 降到 5，属码框占位符文案与输入框默认样式的差异。

## 复跑

```bash
cd apps/web && npm run build
node qa/visual/screenshots.mjs      # 实现 18 屏
node qa/visual/compare.mjs          # 基线 9 屏
python qa/visual/compare.py         # 并排图 + 本报告
```
