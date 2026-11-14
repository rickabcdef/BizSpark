# H 卡三份门禁报告（T-59 / T-60 / T-61）— 2026-11-14

本轮界面改版（AL-xx 任务卡）放行前置门禁。执行环境：Windows，仓库 `D:\XiangMu\Project\BizSpark`，
基线 `F:/迅雷下载/BizSpark_中英双版_UI与HTML_202611141112`。

---

## T-59 商品金额零命中 ✅

**口径**（需求 §4 P-14、§9 T-59）：交付物零商品售价硬编码，价格唯一源为
`assets/pricing.js`（静态页）/ `config/pricing.json`（客户端），首版 `display_mode:"hidden"`、`amount:null`；
4 个价格槽（hero-trust / hero-foot / export-note / activate-eyebrow）文案不含金额。

**执行**：`python qa/cases/test_price.py`（同 run_all 的 price 阶段，2026-11-14 PASS）。

**结果**：
- 严格扫描命中 1302 处，全部位于**内容数据**（`apps/core/data/baseline_v1.json` 的
  `pricing_hint` / `Offer …` 等点子内容，判定边界明文豁免"内容数据不计"）。
- 交付物代码（apps/web / apps/core / qa 之外的运行时代码）：零命中。
- 4 个价格槽渲染文案均来自 pricing 契约，无内嵌金额。
- 一键回归 `qa/e2e/run_all.py` 的 **price 阶段 PASS（1.2s）**。

**结论**：通过。

---

## T-60 中文双层 ✅

**口径**：中文可见内容必须成双层——`apps/web/src/locales/zh-CN.json`（界面层，键值与
en-US 一一对应）+ `apps/core/data/zh_v1.json`（内容层，312 条点子的中文覆盖），
缺项回退英文、金额数值一字不动。

**执行**：全量校验脚本逐条核对 overlay 真实消费字段（`engine/zhpack.py::overlay / apply_cost_labels`）。

**结果**：
- 界面层：`en-US.json` 与 `zh-CN.json` 各 249 键，差集 **0**。
- 内容层：`zh_v1.json` 312 条与 `baseline_v1.json` 312 条 id 一一对应，每条 8 个字段
  （title / one_liner / pricing_hint / compliance_note / steps / pitfalls / first_customers / cost_items）
  **312/312 全覆盖**，无缺条、无长度不齐、无金额不一致。
- 另有 3 个额外键（`us-svc-map-001` / `us-svc-tidy-002` / `us-dig-menu-003`），非基线 id，不参与 overlay，无害。
- 中文自检：18 屏截图（`qa/reports/visual/cn/`）中文渲染正常，无回退英文残留。

**结论**：通过。

---

## T-61 零假控件 + 装饰只读 + 主链路连点 ✅

**口径**：中英 18 页（各 9 屏）零假控件（`href="#"` / `.toggle` / `select` / `.sel-box` / 空按钮）；
装饰元素只读（chip/crumb/side-ver/badge-line/hero-meta/state-pill `user-select:none`，
avatar/hero-meta/state-pill `pointer-events:none`）；主链路 01→02→03→04→05→06→02 五个按钮连点全通。

**执行**：`node qa/t61.mjs`（Playwright，真前端 + 真 sidecar，2026-11-14）。

**结果**：
- 中英 18 页扫描全绿：假控件 0、空按钮 0、被禁用的装饰元素全部只读。
- 主链路连点（含本轮改回的 Back / Next question 两按钮流程）全部通过。
- 输出：`qa/reports/t61.json`（含逐页明细）。

**结论**：通过。

---

## 关联证据

| 证据 | 位置 |
| --- | --- |
| 一键全量回归 11/11 PASS（217.8s） | `qa/reports/run-all-summary.json` |
| UI 用例 16/16 | `qa/reports/ui-checks.json` |
| 18 屏逐屏与基线比对 | `qa/reports/visual-comparison.md` + `qa/reports/visual/compare/` |
| D5 前端离线演练 PASS（真出 PDF） | `qa/reports/offline-drill-ui.json` |

## 放行意见

三份门禁全部通过，且本轮唯一发现的页面缺陷（Detail eyebrow 的 match 百分比空缺，
`get_idea` 不带 `match_pct/rank`）已用"重放 diagnose 回填"修复并复测——
属于页面展示对齐，不涉及引擎与功能变更。**建议 H 签字放行。**
