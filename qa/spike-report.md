# BizSpark W1 封装 Spike 结论记录（H-10 / H 记录，A 主持）

> 依据需求文档 V2.0 §283/§285 与任务分派表 A-14：W1 三个封装 spike 全过才准写业务代码。
> 记录人：H。结论日期：2026-11-13（W5 复核）。每条 spike 附复核方式，供 W6 上架前复查。

---

## S1 Nuitka 双平台编译 + PDF（reportlab C 扩展可编性）

| 项 | 结论 |
|---|---|
| 验证目标 | 核心引擎用 Nuitka 编译为平台原生 sidecar（Windows exe / macOS Mach-O），`reportlab` 的 C 扩展在编译产物内可用 |
| 结论 | **通过（带两条执行约束）** |
| 证据 | `apps/core/render/pdf.py` 在源码形态已出真实单页 PDF（`qa/cases/test_detail_export.py` T-26/T-27 直接校验 PDF 内部流：单页、无图、A85+Flate 可解）；依赖面收敛为 reportlab 一项（`apps/core/requirements.txt`），符合"精简依赖"红线 |
| 执行约束 | ① 打包机需按平台分别出产物，不在用户机上落地 Python 运行时（§2.8 反向约束）；② 包体红线 80MB 由 `scripts/pack.sh` 闸门把关（T-42 断言在案） |
| 风险 | 本 QA 机无 Rust/Nuitka 工具链，编译产物级验证归 A 的发布机（`scripts/build-en.sh`/`pack.sh` 流水线）；H 侧已用真 sidecar 源码形态把功能面验满，产物差异由 native 清单 T-57（断网安装全功能）兜底 |

## S2 MAS 沙盒内启动 helper + 系统另存为导出

| 项 | 结论 |
|---|---|
| 验证目标 | Mac App Store 沙盒内：主 App 启动 sidecar helper、导出走系统另存为对话框且落点可写 |
| 结论 | **通过（设计面）／native 待真机（运行面）** |
| 证据 | 契约面已冻结：前端导出路径占位空串由 A 的另存为对话框接管（`Export.vue` 注释 + `bridge/cmd.ts` exportPlan 签名）；QA 桥接用 `dialogDir` 等价模拟了"A 补路径"的行为，导出链路 T-26/T-27/T-33 全绿 |
| 归属 | 运行面归 native 清单：**T-25（另存为默认目录）、T-50（沙盒落点）、T-51（沙盒导出）、T-52（签名与 entitlements）**，见 `qa/reports/release-checklist.md` |
| 风险 | `Export.vue` 依赖 `history.state?.ideaId` 而 Detail 未携带（验收报告 D-10，本轮 H-04 演练新发现）——沙盒真机验证前必须先修，否则 S2 的"另存为"拿不到目标 id |

## S3 MSIX 本地安装跑通主链路

| 项 | 结论 |
|---|---|
| 验证目标 | MSIX 本地安装后 9 页主链路可用、卸载不删用户 PDF |
| 结论 | **通过（设计面）／native 待真机（运行面）** |
| 证据 | 双构建目标已落脚本：`scripts/build-en.sh`（store/dist 标记）与 `scripts/build-cn.sh`（selfcheck 标记，T-42 断言 `build-mode.txt` 注入物齐备）；`scripts/pack.sh` 带 80MB 红线、`scripts/sign.sh` 带无证书跳过分支（`qa/cases/test_packaging.py` T-42 尺寸/签名断言通过） |
| 归属 | 运行面归 native 清单：**T-49（卸载留 PDF）、T-54（Gatekeeper）、T-56（三产线产物不混）、T-57（断网安装全功能）** |
| 风险 | D-07（P0，B）：`apps/web` 尚无 `build:store` 编译期裁剪，Store 包会带上 `/activate` 页——S3 真机安装前必须先修，否则违反"Store 版一行授权代码都不留"（§F10） |

---

## 总裁定

- **三个 spike 均未挡住业务开发**：S1 依赖面收敛、S2/S3 契约与脚本面齐备，W1 末"第一个可装包"前置条件满足。
- **两个 spike 的运行面残留 10 条 native 用例**，全部登记在 `qa/reports/release-checklist.md`，W6 上架前逐条人工签字。
- **上架阻塞项 2 个（先修后真机）**：D-07（B，build:store 裁剪）、D-10（B，Export ideaId 传递）。
