# BizSpark 验收报告（H-10）

- 记录人：H（QA / 发布素材 / 最终签字）
- 报告日期：2026-11-13
- 被测基线：`sde-H` 分支工作区（A~G 七个模块分支已合入 PM 分支的产物，QA 只读复用）
- 用例基线：64 条（T-01…T-48、T-30-1…6、T-49…T-58、T-59），登记表 `qa/cases/cases.json`
- 一键复现：`python qa/e2e/run_all.py`（`--fast` 跳性能/演练；`--with-visual` 含截图回归）

---

## 1. 总评

| 维度 | 结论 | 数字 |
|---|---|---|
| 自动化用例 | **54 条自动化：47 绿 / 7 红对应 7 个立案缺陷** | 详见 §4 缺陷登记册 |
| native 用例 | 10 条待真机人工签字 | `qa/reports/release-checklist.md` |
| F14.1 性能红线 | **六项全 PASS** | 冷启 1253.3ms（限 1500）· diagnose p95 37.9ms（限 300）· 导出 55.3ms（限 2000）· RSS 35.7MB（限 300）· 包体源体积 1.5MB（真包 ≤80 由 pack.sh 把关）· **出网 0** |
| H-04 离线演练 | **PASS_WITH_KNOWN_ISSUES** | D1–D5 九场景，唯一残留 D-05（已立案） |
| H-05 视觉回归 | **18 屏（en+cn 9+9）溢出全 0** | `qa/reports/visual/metrics.json`；英文 9 张已进 `qa/store-assets/screenshots/en/` |
| H-09 内容抽检 | **30/30 全过 §5.4 清单** | `qa/content-review.md` |
| H-08 中文包检查 | **通过** | 见 §3 |
| H-12 零金额扫描 | **通过（双口径）** | 边界版 0 命中；严格版 1297 处全部落在内容数据白名单（`apps/core/data/`、`quiz.py` 资金档标签、`locales/` 镜像文案、`qa/cases` 用例描述、`docs/`） |
| T-58 商店素材 | **齐备** | 图标 1024/512/256（`qa/store-assets/icon/`，`make_icons.py` 可重产）· 仅英文截图 10 张 · 隐私政策一页 · 商品页含 5 条必写句+支持邮箱 · 素材全文零金额 |

**放行意见：不放行。** 存在 2 个上架阻塞缺陷（D-07、D-10）与 5 个体验/数据缺陷（D-01…D-06、D-09），修复复测后按 §6 流程签字放行。

## 2. 各周验收记录

| 周 | 计划 | 实际 | 裁定 |
|---|---|---|---|
| W1 | H-01 用例 / H-11 矩阵骨架 / 记录 S1–S3 spike | 64 条用例登记表 + `docs/traceability.md` + `qa/spike-report.md`（三 spike 均未挡路，2 条运行面残留进 native 清单） | ✅ 通过 |
| W2 | H-02 E2E 框架 / H-03 性能框架 | `qa/e2e/bridge_server.mjs`（真前端+真 sidecar 桥接）+ `run_all.py` 一键全量 + `perf_suite.py` 六项 | ✅ 通过 |
| W3 | 逐模块验 C/D/E/F | engine 16/16 · license 6/6 · state/export 立案 D-02…D-05 · content 抽检全过 | ✅ 通过（带立案） |
| W4 | H-04 离线演练 / H-05 视觉 / H-09 抽检 / **功能冻结** | 演练 D1–D5 PASS_WITH_KNOWN_ISSUES · 18 屏溢出 0 · 30/30 抽检 | ✅ 通过；**冻结附条件：D-01…D-07/D-09 修复前不解除打回权** |
| W5 | H-06 商店素材 / H-07 商品页 / H-08 中文包 | 素材齐备（§1）· 5 条必写句逐字在案 · 中文包检查通过（§3） | ✅ 通过 |
| W6 | 上架前最终签字 | **待 W4 缺陷清零 + 10 条 native 签字后执行**（§6） | ⏳ 未到 |

## 3. H-08 中文包检查结论（T-28）

1. **无语言切换按钮**：全代码 `grep` 无 `locale.switch` / 语言切换控件；`settings._valid` 把 `language` 锁死为构建模式对应值（`en-US` / 自检包 `zh-CN`），软件内不可切换（F14.3）。
2. **不进商店素材**：`qa/store-assets/screenshots/` 仅 `en/` 目录 10 张；自动化断言 `test_packaging.T58StoreMaterials.test_screenshots_english_only` 持续把守（出现 `screenshots/cn/` 即红）。
3. **V-10 键一致**：`zh-CN.json` 与 `en-US.json` 逐键比对（含占位符 `{dir}`/`{kb}`/`{pages}`），品牌词 `BizSpark` 保留不译；`test_contract` 巡检在案。

## 4. 缺陷登记册（H 立案，冻结期必修清单）

| 编号 | 用例 | 级别 | 主责 | 描述 | 复现 |
|---|---|---|---|---|---|
| D-01 | T-20 | **P0** | B | 结果页复述句为空：`Results.vue` 用空 payload `diagnose({})` 且未读 `last_answers` → `Based on , , and US.` | `test_ui.T20` |
| D-02 | T-32 | P1 | C | `get_idea` 详情数据缺第 3 条 pitfall（`engine/detail.py` 无 E 侧 `render/detail.py` 的兜底补齐） | `test_detail_export.T32...pitfall` |
| D-03 | T-32 | P1 | C | `summary`/`steps` 不截断（实测 2220 字符），详情页必溢出 | `test_detail_export.T32...overlong` |
| D-04 | T-40 | **P0** | F/D | `apply_delta` 白名单外字段可写库（`secret_extra` 落盘）、`title` 可被非白名单字段覆盖；白名单只在 `create_delta` 校验，运行期未复用 `merge_delta` 约束 | `test_state.T30...illegal_fields` |
| D-05 | T-30-5 | **P0** | F | delta 无体积闸门：3.2MB/1200 条新增包被接受写库（需求：>200KB 静默跳过） | `test_state.T30...oversized` |
| D-06 | T-37 | P1 | F | `compare_ideas` 返回 `title` 字段，前端 KvRow 当数据行露出（应只有成本/工时/回本三项） | `test_ui.T37` |
| D-07 | T-42 | **P0** | B | `apps/web` 无 `build:store` 编译期裁剪与 Store 标记 → Store 包必带 `/activate` 页，违反"Store 版一行授权代码都不留" | `test_packaging.T42...store_build_mode` |
| D-08 | T-34 | P2 | E | 不可写目录回 `E_PDF_WRITE` 而非附录 D 的 `E_FS_READONLY`（用户文案正确，仅码值漂移） | `test_contract`（漂移清单） |
| D-09 | 巡检 | P2 | C/D/E/F | 附录 D 之外出现 6 个错误码：`E_INTERNAL`/`E_IDEA_NOT_FOUND`/`E_EXPORT_CANCELLED`/`E_CSV_WRITE`/`E_PDF_WRITE`/`E_LIBRARY_WRITE`——要么进附录 D，要么改归已有码 | `test_contract.ErrorCodeDrift` |
| D-10 | H-04/D5 | **P0** | B | `Detail.vue` 跳 `/export` 未携带 `ideaId`，`Export.vue` 读 `history.state?.ideaId` 恒空 → 点「Export my plan」导出静默失败、完成页无文件行（H-04 前端演练新发现） | `qa/offline/offline_ui.mjs`（记录 `defects`） |

> 修复责任不含 H（H 不写业务代码）；每项修复后 H 复测对应用例并把 `docs/traceability.md` 状态列刷新。

## 5. H 交付物索引

| 交付物 | 位置 |
|---|---|
| 用例登记表（64 条，唯一数据源） | `qa/cases/cases.json` + `registry.py` |
| 自动化用例（9 个模块） | `qa/cases/test_*.py`（54 条 + 契约巡检 + 篡改 + 码池） |
| E2E 桥接 / UI 用例 / 一键全量 | `qa/e2e/bridge_server.mjs` / `ui_checks.mjs` / `run_all.py` |
| 离线演练（H-04） | `qa/offline/drill.py` + `offline_ui.mjs` → `qa/reports/offline-drill(.json)` |
| 性能（H-03） | `qa/perf/perf_suite.py` → `qa/reports/perf.json` |
| 视觉回归 + 截图（H-05/H-06） | `qa/visual/screenshots.mjs` → `qa/reports/visual/` + `qa/store-assets/screenshots/en/` |
| 商店素材（H-06/H-07） | `qa/store-assets/`：`icon/`×3（`make_icons.py`）· `privacy-policy.md` · `product-page.md` · 仅英文截图 |
| 内容抽检（H-09） | `qa/content-review.md`（30 条明细） |
| 追溯矩阵（H-11） | `docs/traceability.md` |
| Spike 结论 | `qa/spike-report.md` |
| native 人工清单 | `qa/reports/release-checklist.md` |

## 6. 签字页

### W4 功能冻结签字（附条件通过）

> 冻结范围：1.0.0 全部 F01–F14 与价格配置。冻结期**只修 §4 登记册缺陷**，不接新需求。

- 功能面已冻结：是 ☐ 否 ☐
- §4 登记册缺陷在冻结期清零：是 ☐ 否 ☐（未清零则冻结解除延后）
- 签字（PM）：____________ 日期：______
- 签字（H，一票否决权）：____________ 日期：______

### W6 上架前最终签字（未到，触发条件）

> 触发条件全部满足后方可签字：① §4 缺陷清零且复测绿；② `release-checklist.md` 10 条 native 全签；
> ③ `traceability.md` 状态列全部「已通过」；④ `qa/store-assets/` 素材终版（替换真实支持邮箱后复跑 T-58）；⑤ 每周五可装包最近一次全绿。

- 自动化回归全绿：是 ☐ 否 ☐（`run_all.py --with-visual`）
- native 清单收齐：是 ☐ 否 ☐
- 商店素材终版确认（含真实 support 邮箱）：是 ☐ 否 ☐
- **上架放行：是 ☐ 否 ☐**
- 签字（H）：____________ 日期：______

---

### 备注两点

1. **支持邮箱是占位符**：`support@bizspark.app`（G 在 `activate.py` 与 security-review 已标注）——上架前必须替换为真实可收信邮箱，替换后重跑 `test_packaging`（T-58 断言商品页/隐私政策含邮箱）。
2. **本机 QA 环境限制**：无 Rust/Nuitka 工具链、无签名证书、无真机——凡依赖发布机/真机的验证全部收进 native 清单，不在本报告虚报通过。
