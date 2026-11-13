# BizSpark 发布前 native 用例人工检查清单（H-02/H-10 配套）

> 64 条用例中 10 条 `native`：自动化无法在无真包/真机/真签名的 QA 机上覆盖，
> 逐条人工执行并在「签字」列签名。执行人按 owner 列，H 汇总收回。
> 全部签完 → 本清单归档进 `qa/reports/`，作为 W6 上架前最终签字的附件。

| # | 用例 | 前置 | 步骤 | 通过标准 | Owner | 日期 | 签字 |
|---|---|---|---|---|---|---|---|
| 1 | **T-02** sidecar 崩溃自愈（P0） | 无 | 任务管理器强杀 `bizspark-core` 进程后继续操作 | 壳自动重启 sidecar **1 次**；首屏不阻塞、不弹窗、正在进行的操作温和恢复（走 T-31 缓存口径） | A | ☐ | ______ |
| 2 | **T-25** 另存为默认目录（P0） | 详情页 | 点 `Export my plan` | 弹**系统**另存为对话框；默认目录 `$DOCUMENTS/BizSpark/`；默认文件名与商机 id 对应；确认后 PDF 写入所选位置 | A/E | ☐ | ______ |
| 3 | **T-48** 新版本提示不阻断（P1） | 分销版、托管上挂一个新版本 manifest | 正常启动 | 仅一句 `next launch` 式提示；**不强制**、不阻断任何操作；断网/manifest 404 时零提示零弹窗（对照 H-04 演练 D2） | A | ☐ | ______ |
| 4 | **T-49** MSIX 卸载留 PDF（P0） | MSIX 本地安装 | 安装 → 导出 PDF 到 Documents → 设置里卸载 → 回 Documents 查看 | `runFullTrust` 生效（sidecar 起得来）；**卸载后用户 PDF 原样保留** | A/E | ☐ | ______ |
| 5 | **T-50** MAS 沙盒落点（P0） | MAS 沙盒包 | 启动后查 appDataDir 实际落点；尝试写容器外目录 | 落在 `~/Library/Containers/<bundle-id>/...`；容器外写入被沙盒拦截且**不弹错误**、应用不崩 | A/F | ☐ | ______ |
| 6 | **T-51** MAS 沙盒导出（P0） | MAS 沙盒包 | 详情页点导出 | 弹系统另存为（沙盒 powerbox）；选完目录后 PDF 成功写出、完成页正常 | A/E | ☐ | ______ |
| 7 | **T-52** MAS 签名与 entitlements（P0） | MAS 签名包 | `codesign -dv --entitlements -` 查主 App 与 helper | 主 App 签名有效；helper 带 `com.apple.security.app-sandbox` + `inherit`；`spctl -a` 通过 | A/G | ☐ | ______ |
| 8 | **T-54** 分销 dmg Gatekeeper（P0） | 分销 Mac .dmg（notarized） | 全新机器（无开发者证书信任）首次双击 | Gatekeeper 无「已损坏 / 无法验证开发者」；`spctl -a -t exec` 通过；票据已 `staple`（拔网双击也能过） | A/H | ☐ | ______ |
| 9 | **T-56** 三产线产物不混（P0） | 三条产线产物齐 | 核对证书族与产物目录/文件名 | MAS 包（Mac App Store 签名）不在分销目录；Developer ID 包不进商店提交；MSIX/NSIS/dmg 命名含产线与版本、可区分 | A/H | ☐ | ______ |
| 10 | **T-57** 断网安装全功能（P0） | 任一安装包 | 断网安装 → 跑完整主链路（5 题 → 3 条 → 详情 → 导出 → 存档 → 设置） | 全功能可用；零出网（对照 H-04 演练 D1 的 socket 记账法）；杀掉网络后重启 App 存档仍在 | **H** | ☐ | ______ |

## 执行注意

- T-02 / T-48 的"壳行为"依赖 A 的 Rust 层；QA 机无 Rust 工具链，必须在发布机执行。
- T-25 / T-51 执行前确认 D-10（Export ideaId 传递）已修复，否则导出拿不到目标 id（见验收报告缺陷登记册）。
- T-56 执行前确认 D-07（build:store 裁剪）已修复，Store 产物里 `grep -r "activate"` 必须为 0（对照 `qa/security/store_strip_check.py`）。
- T-57 可复用 `qa/offline/drill.py` 的 sitecustomize 桩思路：把桩放进安装后的 appdata 环境再跑链路，`blocked.jsonl` 计数为 0 即零出网。

**收回签字后**：在 `docs/traceability.md` 把对应行刷成「已通过（native）」，并在 `qa/reports/acceptance-report.md` W6 签字块引用本清单编号。
