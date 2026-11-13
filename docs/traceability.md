# BizSpark 需求追溯矩阵（H-11 维护）

> 对应需求文档 V2.0 §11。状态列由 H 维护，数据来源：`qa/cases/`（64 条用例登记表 `cases.json`）、
> `qa/reports/run-all-summary.json`、`qa/reports/ui-checks.json`、`qa/reports/perf.json`、
> `qa/reports/offline-drill.json`、`qa/content-review.md`。
> 缺陷编号 D-xx 见 `qa/reports/acceptance-report.md` 缺陷登记册。

**状态取值**：`已通过`（自动化断言全绿）· `缺陷已立案`（用例红，缺陷进登记册，冻结前必修）
· `native 待真机`（自动化无法覆盖，走 `qa/reports/release-checklist.md` 人工签字）
· `已通过（脚本+人工）`（脚本验主体，剩余维度人工）

---

## F ↔ 用例 ↔ 状态

| 功能 | 主责 | 协助 | UI 页 | 用例 | 状态 | 说明 |
|---|---|---|---|---|---|---|
| F01 启动首屏 | A | B/F | 01 | T-01✅ T-02⏳native T-03✅ T-28✅ | **有缺陷待清** | T-02 需真机杀 sidecar 演练；T-03 用 failMode=E_CORE_DOWN 验过降级 |
| F02 问卷 | B | C/F | 02 | T-04✅ T-05✅ T-06✅ T-07✅ T-08✅ T-09✅ | **已通过** | 含 zh 自检包键一致（T-28 覆盖） |
| F03 匹配引擎 | C | D/F | — | T-10…T-18 全✅ T-38✅ | **已通过** | 真库 312 条；T-11 国别阻断走 SG+构造库 |
| F04 结果页 | B | C | 03 | T-19✅ **T-20❌D-01** T-31✅ | **缺陷已立案** | D-01（P0，B）：复述句为空 |
| F05 详情 | E | B/D | 04 | T-21✅ T-22✅ T-23✅ T-24✅ **T-32❌D-02/D-03** | **缺陷已立案** | D-02 pitfall 缺第 3 条；D-03 长文本不截断 |
| F06 导出 | E | A/F | 05 | T-25⏳native T-26✅ T-27✅ T-33✅ **T-34❌D-08** | **缺陷已立案** | T-33 socket 桩实测零出网；D-08 错误码与附录 D 漂移（另见 D-09 错误码巡检） |
| F07 我的点子 | F | B | 06 | T-35✅ T-36✅ T-29✅ **T-37❌D-06** | **缺陷已立案** | D-06（P1，F）：compare 多出 title 行 |
| F08 商机库 | D | F/H | 08 | **T-39✅**（H-09 抽检 30 条全过） | **已通过** | `qa/content-review.md` 30 条明细 |
| F09 月度更新 | F | A/D/B | 08 | T-30-1…4✅ **T-30-5❌D-05** T-30-6✅ **T-40❌D-04** | **缺陷已立案** | D-04 白名单外字段落库；D-05 缺体积闸门 |
| F10 授权 | G | A/B | 07 | T-41✅ T-43✅ T-44✅ T-45✅ 篡改✅ | **已通过** | 字段验签、席位、跨设备、码池 |
| F11 设置 | F | B | 09 | T-46✅ T-47✅ | **已通过** | 深色对比、6 行设置 |
| F12 程序更新 | A | — | — | T-48⏳native | **native 待真机** | 提示不阻断，须真包 updater |
| F13 降级口径 | F | 全员 | 全部 | T-28…T-40 相关全跑（含 H-04 演练 D1–D5） | **已通过** | 离线演练总评 PASS_WITH_KNOWN_ISSUES（D-05 在案） |
| F14 非功能/双构建 | A | B/G/H | 全部 | T-28✅ T-29✅ V-10✅ perf 六项✅ | **已通过** | 冷启 1253ms / diagnose p95 37.9ms / 导出 55ms / RSS 35.7MB / 包体 1.5MB / 出网 0 |
| F14.3 中文包 | A/B | H | — | T-28✅（无语言切换、V-10 键一致、不进商店素材） | **已通过** | H-08 结论见验收报告 §3 |
| **价格配置** | A | B/H/G | 01/05/07 | **T-59✅**（双口径扫描边界版 0 命中） | **已通过** | 严格扫描 1297 处全在内容数据白名单内 |
| **打包/上架** | A | B/G/H | — | **T-42❌D-07** T-55✅ **T-58✅** T-56/T-57⏳native T-49…T-52/T-54⏳native | **缺陷已立案** | D-07（P0，B）：无 build:store，Store 包必带 Activate 页 |

**汇总**：64 条用例 = 自动化 54 条（其中 47 绿 / 7 红对应 7 个立案缺陷）+ native 10 条（release-checklist 人工签）。
**放行条件（§11 原文）**：W4 冻结前 7 个缺陷全部修复复测、10 条 native 全部签字，「有缺陷待清/缺陷已立案」清零后才刷成「已通过」并放行。

---

## 用例 ↔ 自动化落点（可复现）

| 用例组 | 测试文件 | 条数 | 最近结论 |
|---|---|---|---|
| T-09…T-18 | `qa/cases/test_engine.py` | 16 | 16/16 ✅ |
| T-21…T-27/T-32…T-34 | `qa/cases/test_detail_export.py` | 16 | 14/16（D-02/D-03） |
| T-29/T-30-5/6/T-35/36/38/40 | `qa/cases/test_state.py` | 16 | 14/16（D-04/D-05） |
| T-41…T-45+篡改 | `qa/cases/test_license.py` | 6 | 6/6 ✅ |
| T-39/T-53/H-09 | `qa/cases/test_content.py` | 8 | 8/8 ✅ |
| T-42/T-55/T-56/T-58 | `qa/cases/test_packaging.py` | 11 | 10/11（D-07） |
| 契约巡检 | `qa/cases/test_contract.py` | 10 | 9/10（D-09 错误码漂移） |
| T-59 | `qa/cases/test_price.py` | 4 | 4/4 ✅ |
| T-01/03…T-08/T-19/T-20/T-31/T-37/T-46…T-48 | `qa/cases/test_ui.py` + `qa/e2e/ui_checks.mjs` | 16 | 14/16（D-01/D-06） |
| H-04 离线演练 | `qa/offline/drill.py` + `qa/offline/offline_ui.mjs` | D1–D5 | PASS_WITH_KNOWN_ISSUES |
| H-03 性能 | `qa/perf/perf_suite.py` | 6 项 | 全 PASS（`qa/reports/perf.json`） |
| H-05 视觉 | `qa/visual/screenshots.mjs` | 9+9 屏 | 溢出全 0（`qa/reports/visual/metrics.json`） |

一键复现：`python qa/e2e/run_all.py`（`--with-visual` 含截图回归）。
