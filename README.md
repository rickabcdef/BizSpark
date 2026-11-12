# BizSpark

本地商机诊断工具（Windows 桌面应用，Tauri + Vue3 + Python sidecar）。

## 技术栈（已定，见需求文档 §2.1）

- 壳：Tauri（A 负责）
- 前端：Vue3（B 负责）
- 核心逻辑：Python sidecar（C/D/E/F/G 共用包）

## 目录结构

按需求文档 §2.3 仓库目录树搭建：

- `apps/desktop/` — Tauri 壳（A）
- `apps/web/` — Vue3 前端，9 个页面（B）
- `apps/core/` — Python sidecar（C/D/E/F/G）
- `content/` — 商机库源稿（D，312 条）
- `hosting/` — 静态托管产物 + 发布脚本（D）
- `qa/` — 用例、E2E、性能脚本、商店素材（H）
- `docs/` — 需求文档 + 接口变更记录
- `scripts/` — build-en / build-cn / pack / sign（A）

## 分支规范（见 §2.3）

- `main` 只接受 PR
- 功能分支：`feat/{A-H}/{模块}-{短描述}`
- 契约改动：`contract/` 前缀 PR 并 @全员
- `release/1.0.0` 冻结后仅 H 可合入修复

## 关键文档

- `docs/BizSpark_开发执行版需求文档V20.docx`（本仓库唯一需求基准）
- 功能清单 F01–F14（§4）；测试用例 T-01–T-48（§9）
