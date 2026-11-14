# BizSpark 开发执行版需求文档 V2.0

> 面向 8 人开发团队 · 可直接分发 · 功能到步骤级 / 数据到字段级 / 任务到文件级

| 项 | 内容 |
|---|---|
| 文档版本 | **V2.0（开发执行版）** |
| 上位文档 | 《生意快启海外买断版_需求文档V1.0.md》（产品定义与商业边界） |
| UI 基线 | `BizSpark_中英双版_UI与HTML.zip` 内 `en/html/` 9 页（**唯一验收基线**）、`en/ui/` 9 张截图、`UI总览图_英文版.png`；`cn/` 为内部自检镜像 |
| 日期 | 2026-11-12 |
| 主体 | 上海浦东 OPC 公司 |
| 团队 | 程序员 A / B / C / D / E / F / G / H，共 8 人，全员参与 |
| 产品 | BizSpark，Windows / macOS 桌面工具，一次性买断（**价格可配置、全项目不写死**，见 §3.9） |
| 首发货架 | Microsoft Store、Mac App Store 优先；其后 Gumroad / Lemon Squeezy |
| 首发市场 | US / CA / UK / AU / SG / PH（英文界面） |
| 工期 | 6 周（W1–W6），W4 末功能冻结，W6 上架 |
| 文档状态 | 契约冻结后，任何字段/接口/页面修改须走 §12 变更流程 |

---

## 目录

- §0 这份文档怎么用（给 8 个人的阅读顺序）
- §1 项目总纲与 10 条铁律
- §2 技术架构（进程模型 / 目录树 / IPC / 路径 / 错误码）
- §3 数据契约（全字段 schema / 枚举 / 校验规则）
- §4 功能需求 F01–F14（逐条到步骤级）
- §5 商机库内容生产规范（312 条分布 / 填写模板 / 审核清单）
- §6 八人分工总表与逐人任务卡（A–H，任务到人、到文件）
- §7 模块间接口契约（并行开发不互相等）
- §8 六周排期（逐人逐周 + 里程碑 + 联调点）
- §9 联调、测试用例与验收（T-01…T-48）
- §10 打包、签名、上架清单
- §11 需求追溯矩阵（功能 ↔ 人 ↔ 页面 ↔ 用例）
- §12 变更流程、纪律与风险
- 附录 A：完整商机条目示例　附录 B：delta 包示例　附录 C：IPC 命令速查　附录 D：错误码表

---

## §0 这份文档怎么用

### 0.1 八个人分别先读哪里

| 人 | 必读 | 精读 | 可略读 |
|---|---|---|---|
| A（架构/壳/发布） | 全文 | §2 §3 §7 §8 §10 | §5 内容填写细节 |
| B（前端 9 屏） | §1 §2.4 §4 全部 | §3.6 文案资源 §7.2 IPC 调用 §9 视觉用例 | §5 商机内容 |
| C（诊断引擎） | §1 §3 | §4 F02 F03 F04 §7.1 §9 引擎用例 | §10 上架 |
| D（商机库/数据） | §1 §3 | §5 全章 §4 F08 F09 §7.3 | §4 前端交互 |
| E（详情/PDF 导出） | §1 §3 | §4 F05 F06 §7.1 §9 导出用例 | §6 分工 |
| F（本地状态/更新/降级） | §1 §2.5 §3 | §4 F07 F09 F11 F13 §7.4 | §5 内容 |
| G（授权/安全） | §1 §2.5 §3.5 | §4 F10 §7.5 §9 授权用例 | §5 |
| H（QA/发布素材） | 全文 | §9 全章 §10 §11 | §5 内容填写细节 |

### 0.2 三条共识，开工前全员签字确认

1. **界面永远以 `en/html/` 为准。** 任何人觉得"这里可以加个按钮/加个筛选/加个提示"，一律不改，走 §12。
2. **中文版不是第二个产品。** 它是同一套代码用 `--mode cn` 打出来的**内部自检包** `BizSpark-SelfCheck-CN`，不上架、不进商品页素材、软件内**没有语言切换按钮**（详见 §4 F14.3）。
3. **契约先于编码。** W1 结束前 §3 数据契约与 §7 接口契约冻结；之后谁改契约，谁负责通知全部依赖方并同步改测试用例。

### 0.3 与 V1.0 的关系

V1.0 定的是「做什么、不做什么」；V2.0 定的是「谁做、按什么顺序做、做到什么程度算完、怎么验」。**两者冲突时以 V1.0 的商业边界为准，以 V2.0 的工程口径执行。** 本文档不新增任何用户可见功能。

---

## §1 项目总纲与 10 条铁律

### 1.1 一句话产品定义

> 用户买下一个桌面图标。双击 → 答 5 道题 → 看到 3 个他能做得成的生意 → 导出一张能打印的纸。全程不登录、不联网也能用、不追问、不学会。

### 1.2 用户可见链路（唯一主链路）

```
双击图标
 → F01 首屏（1 个主按钮）
 → F02 5 道题（每屏 1 题，选中自动进下一题）
 → F03 本地匹配 + F04 3 张结果卡
 → F05 点子详情（成本 / 7 步 / 定价 / 获客 / 3 坑 / 合规一句）
 → F06 导出 1 页 PDF 到本地
 → 关闭
```
**目标：首次打开到拿到 PDF ≤ 3 分钟，点击 ≤ 8 次。**

### 1.3 十一条铁律（开发不得自行突破）

| 编号 | 铁律 | 违反后果 |
|---|---|---|
| L01 | 用户端只留「小」：答几题 → 出 3 条 → 存一张纸 | 加任何一个用户可见控件即视为返工 |
| L02 | 界面不得出现「商机库 / 权重 / 引擎 / 版本 / 浪潮 / 算法」等后台词（V1.0 §7 结果页那行统计小字是唯一例外，且只讲"筛过多少条"） | 文案评审不通过 |
| L03 | 核心逻辑 100% 在客户端本地，不放在云端 | 架构否决 |
| L04 | 联网只用于：① 每月 1 号静默查 delta ② 分销版首次激活。其余一律本地 | 架构否决 |
| L05 | 托管挂了 / 忘续费 / 断网 / 404 / 超时 → **静默跳过**，不弹错、不阻塞、不降级 | 验收 T-30 系列不过 |
| L06 | 软件内零支付代码、无账号、无登录、无订阅、无自动续费 | 商店审核否决 |
| L07 | 不依赖任何按年续费的运行时服务、不调大模型 API、无 API 账单 | 商业模式否决 |
| L08 | Store 版不写授权码；分销版一码 3 台设备，激活 ≠ 登录，激活后永久离线可用 | 差评风险 |
| L09 | 好看是第一位，`en/html/` 高保真稿即像素级验收基线 | 视觉验收不过 |
| L10 | **英文为主、中文为镜**：任何改动先改英文版 → 逐字镜像中文版 → 两版同时重出截图 | 双版跑偏 |
| L11 | **价格不写死**：全项目零金额硬编码；售价由商店后台设置，工程侧唯一价格源 `config/pricing.json`，首版 `display_mode=hidden`、`amount=null`（§3.9） | 商业模式返工 |

### 1.4 本期明确不做（红线清单）

登录注册 / 云同步 / 用户账号 / 找回密码 / 支付接口 / 订单退款后台 / 订阅与会员到期 / 连续包月包年 / 消息推送 / 社区评论 / 用户上传点子 / 联网调大模型 / 用户自带 API Key / 全量 200 国本地化 / 手机端 / 积分签到 / 分享裂变 / 广告位 / 语言切换按钮 / 中文售卖页 / 国内支付 / 国内经营性资质依赖。

---

## §2 技术架构

### 2.1 选型（已定，不再讨论）

| 层 | 选型 | 理由 |
|---|---|---|
| 桌面壳 | **Tauri 2（Rust）** | 包体小（≤60MB）、可出 MSIX / .app / .dmg、原生系统另存为、可带 sidecar |
| 前端 | **Vue 3 + Vite + TypeScript** | 与 UI 稿一致，组件化还原 9 屏 |
| 核心引擎 | **Python 3.11，仅标准库 + reportlab**，PyInstaller onefile 打成 sidecar | 尊重既定 Python 技术栈；纯本地、无第三方服务 |
| 前后端通信 | **Tauri sidecar + stdio JSONL**（一行一请求、一行一响应） | 无端口、无本地 HTTP 服务、无防火墙弹窗、离线可用 |
| PDF | **reportlab**（内置 Helvetica，英文版无需 CJK） | 纯本地单页渲染、无水印 |
| 本地存储 | Tauri `appDataDir` 下 JSON 文件 + 签名凭证 | 无数据库、无 ORM |
| 远程 | 仅静态托管 `manifest.json` + `delta_YYYY-MM.json` | 无 FastAPI 常驻、无数据库、无账单 |

> **为什么不用 FastAPI / UniApp / Electron**：FastAPI 是常驻服务，会把"买断工具"变成"依赖服务器"；UniApp 不出 Windows/macOS 安装包；Electron 包体与内存不满足 §4 F14 非功能指标。三者本期均不采用。

### 2.2 进程模型

```
┌───────────────────────── Tauri 主进程 (Rust) ─────────────────────────┐
│  · 窗口 / 菜单 / 系统另存为对话框 / 深浅色跟随                          │
│  · sidecar 生命周期（启动一次、常驻、崩溃自动重启 1 次）                 │
│  · IPC 桥：WebView ⇄ sidecar（JSONL 转发，带 req_id 匹配）              │
│  · 静态托管 GET（manifest / delta），失败静默                            │
│  · 机器指纹采集（G 提供规范）、签名凭证读写                              │
└───────────────┬──────────────────────────────┬───────────────────────┘
                │ WebView 事件                  │ stdio JSONL
┌───────────────▼──────────────┐   ┌────────────▼──────────────────────┐
│ Vue3 前端（B）                │   │ bizspark-core（Python sidecar）    │
│ 9 屏 / 组件 / 文案资源 / 无网络│   │ C 诊断引擎 · D 库校验 · E PDF/CSV │
│ 只发 cmd，不自己算业务逻辑     │   │ F 状态/合并 · G 授权验签          │
└─────────────────────────────┘   └───────────────────────────────────┘
                                          │
                              ┌───────────▼───────────┐
                              │ 本地文件（§2.5）        │
                              │ baseline / delta / 存档 │
                              └───────────────────────┘
```

**关键约束**：Python sidecar **不监听任何端口**；前端**不直接读文件**（统一经 cmd）；Rust 层**不做业务判断**（只转发与提供系统能力）。三层职责越界即视为架构缺陷。

### 2.3 仓库目录树（A 建立，全员遵守）

```
bizspark/
├─ apps/
│  ├─ desktop/                    # Tauri 壳（A）
│  │  ├─ src-tauri/
│  │  │  ├─ src/main.rs           # 窗口、sidecar、IPC 桥、系统对话框、更新
│  │  │  ├─ src/fingerprint.rs    # 机器指纹（A 写壳，G 定规范并审）
│  │  │  ├─ src/updater.rs        # manifest/delta 拉取与落盘（A/F 共管）
│  │  │  ├─ tauri.conf.json       # 标识符、sidecar、权限、MSIX/签名配置
│  │  │  └─ capabilities/         # 最小权限白名单（G 审）
│  │  └─ package.json
│  ├─ web/                        # Vue3 前端（B）
│  │  ├─ src/views/               # 9 个页面，文件名对齐 en/html
│  │  │  ├─ Welcome.vue  Quiz.vue  Results.vue  Detail.vue  Export.vue
│  │  │  ├─ Saved.vue  Activate.vue  Library.vue  Settings.vue
│  │  ├─ src/components/          # IdeaCard / OptionCard / StepList / PaperPreview …
│  │  ├─ src/bridge/cmd.ts        # 唯一 IPC 出口（B 写，A 审）
│  │  ├─ src/assets/tokens.css    # 由 en/html/assets/style.css 逐 token 移植
│  │  └─ src/locales/
│  │     ├─ en-US.json            # 唯一对外文案源
│  │     └─ zh-CN.json            # 内部自检镜像，逐键对应，不增删键
│  └─ core/                       # Python sidecar（C/D/E/F/G 共用包）
│     ├─ main.py                  # JSONL 主循环、cmd 分发、错误码
│     ├─ engine/                  # C：quiz.py / filter.py / score.py / why.py
│     ├─ library/                 # D：schema.py / validate.py / delta_tool.py
│     ├─ render/                  # E：detail.py / pdf.py / csv.py
│     ├─ state/                   # F：store.py / merge.py / settings.py
│     ├─ license/                 # G：activate.py / device.py / signature.py
│     ├─ data/
│     │  ├─ baseline_v1.json      # D 产出，安装包内置
│     │  └─ schema.json           # D 产出，§3 契约机器可读版
│     └─ requirements.txt         # 仅 reportlab + pyinstaller（构建期）
├─ content/                       # D：商机库源稿（CSV/JSON 源 + 审核清单）
│  ├─ ideas/                      # 按行业分文件
│  ├─ distribution.csv            # 312 条分布表
│  └─ review-checklist.md
├─ hosting/                       # D：静态托管产物 + 发布脚本
│  ├─ manifest.json
│  ├─ delta_2026-12.json
│  └─ publish.py                  # 生成/校验/上传 delta
├─ qa/                            # H：用例、E2E、性能脚本、商店素材
│  ├─ cases/                      # T-01…T-48
│  ├─ e2e/                        # Playwright/自研脚本
│  ├─ perf/
│  └─ store-assets/               # 截图、图标、商品页文案、隐私政策
├─ docs/                          # 本文档 + V1.0 + 接口变更记录
├─ scripts/                       # A：build-en / build-cn / pack / sign
└─ README.md
```

**分支规范（A 定）**：`main` 只接受 PR；`feat/{A-H}/{模块}-{短描述}`；契约改动必须开 `contract/` 前缀 PR 并 @全员；`release/1.0.0` 冻结后仅 H 可合入修复。

### 2.4 IPC 命令表（§7 详版，此处速查）

前端只经 `src/bridge/cmd.ts` 发命令，格式 JSONL：

```json
// 请求（一行）
{"req_id":"r-0001","cmd":"diagnose","payload":{"country":"US","capital":"500-2k","hours":"<10","assets":["laptop"],"risk":"small_loss"}}
// 响应（一行）
{"req_id":"r-0001","ok":true,"data":{"ideas":[...],"checked":312,"filtered":309}}
// 失败
{"req_id":"r-0001","ok":false,"error":{"code":"E_ENGINE_NO_MATCH","message":"...","recoverable":true}}
```

| cmd | 负责 | 输入要点 | 输出要点 |
|---|---|---|---|
| `get_state` | F | 无 | 存档、设置、库版本、授权状态 |
| `save_answers` | F | 5 题答案 | ok |
| `diagnose` | C | 答案 | Top3 + checked/filtered + why 文案 |
| `get_idea` | C+D | `id` | 完整详情对象（F05 四张内容卡 + 派生字段） |
| `export_plan` | E | `id` + 目标路径 | 文件名、字节数、页数 |
| `export_csv` | E | `id` + 路径 | 文件名 |
| `save_idea` / `list_saved` / `clear_saved` / `compare_ideas` | F | `id` / `ids` | 存档列表 |
| `get_settings` / `set_settings` | F | 6 项键值 | 当前设置 |
| `check_library` / `apply_delta` | F+A | manifest / delta 内容 | 新版本号（失败静默） |
| `activate` / `license_status` / `release_seat` | G | 码 / 设备指纹 | 席位数、凭证状态 |
| `log_crash`（默认关） | F | 错误码+版本 | ok |

**禁止**：前端自己 `fetch()` 外部地址；Python 自己弹系统对话框；Rust 层算分数；任何一层写死界面文案（文案只在 `locales/*.json`）。

### 2.5 本地文件路径（F 统一封装 `state.paths.py`）

| 用途 | 路径（相对 `appDataDir/com.bizspark.desktop/`） | 负责人 |
|---|---|---|
| 全局状态 | `state.json` | F |
| 内置库（只读） | `resources/baseline_v1.json`（随包，A 打包） | A+D |
| 合并后工作库 | `library/current.json` | F |
| delta 备份与日志 | `library/deltas/`、`library/rollback/` | F |
| 授权凭证 | `license.dat`（签名，权限 600） | G |
| 导出默认目录 | `$DOCUMENTS/BizSpark/` | E+F |
| 崩溃日志（默认关） | `logs/crash.log`（不含答案/点子/路径） | F |
| 内部自检构建标记 | `build-mode.txt` = `cn-selfcheck` | A+B |

### 2.6 错误码表（附录 D 详版，此处原则）

- 全部错误**只在 Python/Rust 层记录**，前端**默认不展示**。
- 只有 3 类允许给用户看温和提示：导出目录不可写（换文件夹）、匹配结果不足 3 条（放宽一次后温和一句）、第 4 台设备（引导释放席位）。
- 其余一律 `recoverable:true` + 静默降级。**禁止红色弹窗、禁止"请检查网络后重试"、禁止错误码暴露给用户。**

### 2.7 双构建产物（关键，别做成两个产品）

| 构建 | 命令 | 文案源 | 产物 | 去向 |
|---|---|---|---|---|
| 英文售卖版 | `npm run build:en` | `en-US.json` | `BizSpark-1.0.0-Windows.msix/.exe`、`BizSpark-1.0.0-Mac.dmg` | **唯一上架产物** |
| 中文自检版 | `npm run build:cn` | `zh-CN.json` | `BizSpark-SelfCheck-CN-1.0.0.exe/.dmg` | **仅内部**，不签名上架、不进商店素材 |

两构建**共用同一份组件、同一份 CSS、同一份逻辑、同一套 9 个页面**；差异仅 `locales` 与 `build-mode.txt`。**软件内不出现语言切换按钮**（L01 / §4 F14.3）。

### 2.8 封装反向约束（**开发前冻结，不是开发完再补**）

> 完整方案见《BizSpark_打包封装与上架方案V1.0.md》。封装规则会倒过来规定开发怎么写，以下 14 条从 **W1 第一行代码**起生效，违反任一条后期必返工。

| # | 约束 | 相关人 |
|---|---|---|
| P-01 | 所有路径经 Tauri `appDataDir` / 系统对话框取，禁止硬编码绝对路径或 `~` 拼接 | F / E |
| P-02 | **导出必须经系统「另存为」**，由用户授权目标目录（Mac 沙盒 Powerbox） | A / E |
| P-03 | **月度 delta 只能是纯数据 JSON/CSV**，绝不夹带脚本、插件、可执行代码或可 eval 的逻辑（App Store 2.5.2 / DPLA §3.3.1(B) 红线） | D / F |
| P-04 | 不加载外部解释器、不 `eval` 用户内容、不执行随包之外的代码 | C / A |
| P-05 | sidecar 不监听端口、不起后台常驻服务、不开本地 HTTP | A / C |
| P-06 | bundle 内每个 Mach-O / exe 都能被单独签名；**不用运行时解压生成代码的打包方式** | A |
| P-07 | 出网只用 HTTPS GET 静态文件；声明 `network.client` / `internetClient`；失败静默 | A / F |
| P-08 | Store 构建编译期裁掉 `license` + `updater` 模块 | A / G |
| P-09 | 所有依赖随包，不联网装依赖、不运行时下载二进制 | 全员 |
| P-10 | 隐私零收集；隐私政策 URL、App Privacy「不收集」、支持邮箱 W1 备齐 | H / G |
| P-11 | **构建脚本 W1 就存在，每周出一个可安装包**（不是 W5 才第一次打包） | A |
| P-12 | 图标全尺寸变体、四段版本号（末段 0、不复用）、`runFullTrust` 受限功能说明 W1 备齐 | A / H |
| P-13 | 卸载 App 不删除用户导出的 PDF（用户数据在 Documents，不在包容器） | A / E / F |
| **P-14** | **价格不进包**：六构建目标共用同一份 `config/pricing.json` / `assets/pricing.js`，首版 `hidden`+`amount=null`；CI 跑金额门禁（T-59） | A / B / H | 价格随行就市，改配置不改代码 |

**由封装倒推的三项技术决定（已定，不再讨论）**

1. **Python 是开发语言，不是用户电脑上的运行时**：核心引擎构建时用 **Nuitka 编译成平台原生 sidecar**（不是 PyInstaller onefile 带解释器），Windows 出 exe、Mac 出可单独签名的 Mach-O。W1 的 S1 spike 验证 `reportlab` C 扩展可编；不通则把 PDF 渲染挪到前端/Rust 侧，Python 只做诊断，**绝不改界面、绝不上云端**。
2. **三条产线、六份产物、三套签名**：Microsoft Store（MSIX，`runFullTrust`、商店免费代签）/ Mac App Store（App Sandbox + helper `inherit` entitlement、免公证）/ 分销平台（Developer ID + `notarytool` + `staple`）。证书族与产物严禁交叉；Store 版不写授权码，分销版才启用 F10。
3. **W1 三个 spike 不过不许写业务代码**：S1 Nuitka 双平台编译 + PDF；S2 MAS 沙盒内启动 helper + 系统另存为导出；S3 MSIX 本地安装跑通主链路。A 主持，H 记录进 `qa/spike-report.md`。

补充验收用例 **T-49…T-58** 见《打包封装与上架方案V1.0》§8，并入 §9 一起跑。

---

## §3 数据契约（冻结后按 §12 变更）

### 3.1 问卷答案 `QuizAnswers`（C 消费，B 产出，F 缓存）

| 字段 | 类型 | 枚举 / 约束 | 默认 |
|---|---|---|---|
| `country` | string | `US\|CA\|UK\|AU\|SG\|PH` | 系统区域猜测，猜不中 `US` |
| `capital` | string | `<500\|500-2k\|2k-10k\|10k+` | 无默认，必选 |
| `hours` | string | `<10\|10-25\|full` | 无默认，必选 |
| `assets` | string[] | `car\|kitchen\|laptop\|design\|coding\|spare_room\|local_network`，可空数组 | `[]` |
| `risk` | string | `no_impact\|small_loss\|can_absorb` | 无默认，必选 |

**校验规则**：`country/capital/hours/risk` 必须命中枚举；`assets` 元素必须命中枚举；未知字段忽略不报错；`assets` 非数组时按 `[]` 处理（不弹错）。

### 3.2 商机条目 `Idea`（D 产出，C/E/F 消费）—— 全字段定义

| 组 | 字段 | 类型 | 必填 | 约束 / 枚举 | 用途 |
|---|---|---|---|---|---|
| 身份 | `id` | string | ✅ | `^[a-z]{2}-[a-z]{2,4}-[a-z0-9-]{1,20}-\d{3}$`，全局唯一 | 差量覆盖主键 |
| | `title` | string | ✅ | ≤48 字符，英文，动词/名词短语，不含 emoji | 卡片标题 |
| | `one_liner` | string | ✅ | ≤110 字符，说清"谁付钱" | 卡片摘要 |
| 硬条件 | `min_capital` | number | ✅ | ≥0，币种 USD | 成本合计参考 |
| | `capital_tier` | string | ✅ | `<500\|500-2k\|2k-10k\|10k+` | F03 硬过滤 |
| | `hours_per_week` | string | ✅ | `<10\|10-25\|full` | F03 硬过滤 |
| | `countries` | string[] | ✅ | 3.1 国家枚举子集，≥1 | F03 硬过滤 |
| | `online_or_offline` | string | ✅ | `online\|offline\|hybrid` | 标签展示 |
| | `legal_blocks` | string[] | ✅ | 国家码数组，可空 | 命中该国即剔除 |
| 软标签 | `skills_needed` | string[] | ✅ | `writing\|basic_english\|design\|coding\|sales\|driving\|cooking\|handyman\|none`，可空 | 打分 |
| | `assets_needed` | string[] | ✅ | 同 3.1 assets 枚举 + `none` | 打分 |
| | `risk_level` | string | ✅ | `low\|medium\|high` | 打分 |
| | `payback_days` | number | ✅ | 1–365 | 打分 / 详情 |
| | `recurring` | boolean | ✅ | — | 复购型偏好 |
| | `channel_ids` | string[] | ✅ | `google-maps\|nextdoor\|thumbtack\|etsy\|shopify\|facebook\|whatsapp\|walk-in\|chamber\|referral\|local-groups` | 渠道可得性 |
| 内容 | `cost_breakdown` | object[] | ✅ | ≥2 项，每项 `{item:string, amount:number}`；`amount` 合计 ≈ `min_capital`（±15%） | F05 M1 / F06 PDF |
| | `steps` | string[] | ✅ | **恰好 7 条**，每条 ≤60 字符，动词开头 | F05 M2 / F06 PDF |
| | `pricing_hint` | string | ✅ | 含具体数字（如 `$49/month for up to 15 replies`） | F06 PDF（IdeaDetail 派生） |
| | `first_customers` | string[] | ✅ | ≥3 条，**按国家给具体渠道名**，禁止"social media" | F05 M3 / F06 PDF |
| | `pitfalls` | string[] | ✅ | **恰好 3 条**，每条是具体动作，不写空话 | F05 M4 / F06 PDF |
| | `compliance_note` | string | ✅ | ≤140 字符，**仅一句提醒**，不是法律意见 | F06 PDF（详情页不显示） |
| 时代 | `wave` | string | ✅ | `mobile-internet\|ai-llm\|ai-agent\|bi-agent\|local-service\|digital-product` | 趋势新鲜度 |
| | `trend_tags` | string[] | ✅ | 自由标签 ≤5 个 | 内部 |
| | `first_seen` | string | ✅ | `YYYY-MM` | 内部 |
| | `maturity` | string | ✅ | `emerging\|growing\|mature\|saturated` | 降权 |
| 元信息 | `version` | number | ✅ | ≥1，每次 revise +1 | 合并 |
| | `updated_at` | string | ✅ | `YYYY-MM-DD` | 合并 |
| | `status` | string | ✅ | `active\|retired` | 硬过滤 |

**国家适配覆盖 `CountryOverride`**（不复制整条，按 `id` 挂变体）：

```json
{
  "id": "us-svc-ai-014",
  "overrides": {
    "US": { "currency": "USD", "first_customers": ["Google Maps 4-star shops with unanswered reviews", "Nextdoor"], "compliance_note": "US: check local business-name registration and sales-tax rules." },
    "SG": { "currency": "SGD", "first_customers": ["Facebook neighbourhood groups", "WhatsApp business lists", "Google Maps"], "compliance_note": "SG: check ACRA registration before invoicing." },
    "PH": { "currency": "PHP", "first_customers": ["Facebook Marketplace groups", "Google Maps", "barangay referrals"], "compliance_note": "PH: check barangay / DTI registration for home-based services." }
  }
}
```
**规则**：覆盖存在即用覆盖，缺失回退主条目；`currency` 仅影响成本展示符号，不改 `min_capital` 数值口径（内部统一 USD 计算，展示按汇率静态表换算，汇率写在 `fx.json`，D 维护，**不联网取汇率**）。

### 3.3 诊断结果 `DiagnoseResult`（C 产出，B 渲染）

```json
{
  "ideas": [
    { "rank": 1, "id": "us-svc-ai-014", "title": "...", "one_liner": "...",
      "match_pct": 94,
      "why": "Low money, laptop only, repeat monthly income — matches your budget and time.",
      "tags": ["From $120", "<10 h/wk", "Monthly"] }
  ],
  "checked": 312,
  "filtered": 309,
  "degraded": false,
  "degrade_note": null
}
```
- `ideas` 长度 **1–3**，永远 ≤3；`rank` 从 1 连续。
- `match_pct` 整数 60–99，**仅用于卡片小字展示**，不暴露权重。
- `why` 必须引用答案里的具体词（`$500–$2,000` / `under 10 hours` / `a laptop` / 国家名），**禁止**"基于智能算法为您推荐"类措辞。
- `tags` **恰好 3 个**：起步成本 / 时间 / 线上或本地（或复购）。
- `degraded=true` 时 `degrade_note` 为一句温和英文（见 §4 F03 步骤 8）。

### 3.4 详情对象 `IdeaDetail`（C 装配 → E 渲染）

结构 = 3.2 全字段 + 国家覆盖已合并 + 三个派生字段：
`cost_total`（number）、`cost_rows`（已按 currency 格式化）、`payback_hint`（string，由 `pricing_hint` + `payback_days` 生成一句）。

### 3.5 授权凭证 `License`（G）

```json
{ "v": 1, "code_hash": "sha256:…", "device_hash": "sha256:…",
  "seats": [ {"device_hash":"…","activated_at":"2026-11-12T10:22:00Z"} ],
  "seats_max": 3, "signed_at": "…", "sig": "ed25519:…" }
```
- 设备指纹 = `sha256(平台 + CPU/主板序列 + 磁盘卷标 + 系统安装 ID)` 的规范化串；**禁止用 IP、MAC 明文、用户名、文件路径**。
- 公钥内置客户端；私钥只在你手里（离线签发工具 `license/issue.py`，G 写，不进客户端包）。
- 激活成功写 `license.dat`（权限 600）；此后**不再回连**。

### 3.6 文案资源 `locales`（B）

- `en-US.json`：**唯一对外文案源**，键名稳定（如 `welcome.cta`、`quiz.q2.title`、`detail.sec.cost`、`export.done`）。
- `zh-CN.json`：键集合与 `en-US.json` **完全相同**（CI 校验：键差集必须为 0），值逐一中文镜像。
- 不译白名单：`BizSpark`、`Microsoft Store`、`Mac App Store`、`PDF`、`CSV`、`AI`、`Google Maps`、`Yelp`、`Etsy`、`Shopify`、`Nextdoor`、激活码样例、文件名、版本号。
- **禁止**在 Vue 组件里写死任何界面字符串；**禁止**新增 `locale.switch` 之类键。

> **中文包三层契约修订（PM，2026-11-13，老板需求：中文版不得大面积英文）**：
> 1. **界面层**：全部走 `zh-CN.json`（含问卷国家名、对比页行名、结果页国名——此前 Quiz.vue Q1 写死英文，已收编 locales）。
> 2. **引擎层**：sidecar 读 `BIZSPARK_LOCALE` 环境变量（A 壳透传 / build-cn.sh 导出）；`engine/zhpack.py` 提供中文 why 模板池、答案标签、结果卡标签、回本提示、降级提示与 PDF 卡片标题的中文镜像；缺省 en，行为与原实现一致。
> 3. **内容层**：`apps/core/data/zh_v1.json`（315 条 = 312 商机 + 3 fallback，键 = id），可见字段（标题/简介/7 步/3 坑/渠道/成本项标签/定价/合规）中文覆盖，金额数字逐条不动；文件缺失/id 缺项/数量不齐一律回退英文，绝不崩。
> 校验：V-10 键一致不变；zh 内容包金额与 baseline 逐条相等（合并脚本断言）；en 包行为零变化（H 全量回归守护）。

### 3.7 静态托管文件（D）

```json
// manifest.json —— 客户端唯一常驻出网目标，不含任何用户标识
{ "latest": "2026-12", "files": ["delta_2026-12.json"], "size_kb": 18,
  "min_client": "1.0.0", "published_at": "2026-12-01" }
```
```json
// delta_YYYY-MM.json
{ "target_baseline": "v1", "release": "2026-12-01",
  "add":    [ {…完整 Idea…} ],
  "revise": [ { "id": "…", "maturity": "growing", "version": 4 } ],
  "retire": [ "xx-legacy-003" ] }
```
- `add` 项必须是完整 Idea（过 §3.2 校验）；`revise` 只允许白名单字段：`maturity / version / updated_at / first_customers / pricing_hint / cost_breakdown / status / compliance_note / pitfalls / channel_ids`；`retire` 只给 id。
- **不硬删**：`retire` 只置 `status=retired`，磁盘上条目保留。

### 3.8 校验规则总表（D 写 `validate.py`，CI 必跑）

| 编号 | 规则 | 失败处理 |
|---|---|---|
| V-01 | 所有 `id` 唯一 | 构建失败 |
| V-02 | 必填字段齐全、类型正确 | 构建失败 |
| V-03 | `steps` 恰好 7 条、`pitfalls` 恰好 3 条、`first_customers` ≥3 | 构建失败 |
| V-04 | `cost_breakdown` 合计与 `min_capital` 偏差 ≤15% | 构建失败 |
| V-05 | 枚举值全部命中（国家/档位/wave/maturity/status） | 构建失败 |
| V-06 | `countries` 中每个国家都有覆盖或可回退主条目 | 警告 |
| V-07 | `saturated` 条目占比 ≤20% | 警告 |
| V-08 | `wave=ai-*` 合计占比 ≤12% | 警告（防写成 AI 专区） |
| V-09 | `first_customers` 不含 `social media / online promotion / 广告` 等空话 | 构建失败 |
| V-10 | `zh-CN.json` 与 `en-US.json` 键集合相同 | 构建失败 |
| V-11 | delta 的 `revise.id` 必须存在于当前库 | 构建失败 |
| V-12 | baseline 与所有 delta 合并后总量、分布符合 §5.2 | 警告 |

---

### 3.9 价格配置契约 K-11（价格写活，不写死）

> 商品价格随行就市，**是发布参数，不是产品属性**。第一版走 Microsoft Store / Mac App Store 付费下载分成销售，**售价在 Partner Center / App Store Connect 后台设置**，改价即时生效、无需发版。客户端、静态页、需求文档、UI 截图、商品文案**只讲功能与购买模式，一律不出现金额**。

**唯一价格源**

| 层 | 文件 | 负责 |
|---|---|---|
| 静态 HTML 交付 | `assets/pricing.js`（`window.BIZSPARK_PRICING`） | B |
| 工程客户端 | `config/pricing.json` + `locales` 的 `price.*` 键 | A / B |
| 商店售价 | Partner Center / App Store Connect 后台（**不进客户端**） | H |

```json
{ "display_mode": "hidden", "amount": null, "currency": "USD",
  "model": "one-time", "billing_note": null }
```
`display_mode`: `hidden|visible`；`amount`: 数字，仅 `visible` 时填写，首版 `null`；`model`: `one-time|monthly|yearly|seat`；`currency`: ISO 4217。**首版配置无任何金额，`price-render.js` 的 `visible` 分支也零硬编码，金额全部由 `amount` 动态生成。**

**三条硬规矩**
1. **零硬编码**：md / docx / HTML / CSS / JS / 截图 / 商品文案不得出现任何商品售价数字，价格只能由配置渲染。CI 门禁 T-59。
2. **首版 hidden**：`[data-price-slot]` 渲染纯功能 / 模式文案，不渲染数字、不渲染空价格框、**不新增任何用户可见控件**（L01）。
3. **后期显示只改配置**：授权码 / 包月 / 包年 / 订阅时改 `display_mode=visible` + 填 `amount`、`model`，一处改动全端生效；仍不加「改价」界面。

**边界**：商机库里的起步成本 / 定价建议（如 `From $120`、`$49/month`）是**内容数据**，不是商品售价，不受本契约约束，必须保留；门禁只扫商品售价。

**渲染槽**（B 实现，9 屏共用）：
`hero-trust` / `hero-foot` / `export-note` / `activate-eyebrow`。hidden 文案：`One-time purchase · Yours forever`、`Microsoft Store · Mac App Store · One-time purchase`、`No subscription. No auto-renew. Buy once, use it as long as you like — even with the internet off.`、`One-time purchase`；中文逐键镜像。

---

## §4 功能需求 F01–F14（逐条到步骤级）

> 每条统一格式：**负责人 / 优先级 / 对应页面 / 输入 / 处理步骤 / 输出 / 边界与降级 / 验收 / 依赖 / 用例**。
> 「处理步骤」写到可直接照着编码的粒度；「边界与降级」是 H 写用例的直接依据。

---

### F01 启动与首屏

| 项 | 内容 |
|---|---|
| 负责人 | **A（壳/冷启动）主，B（页面）辅，H 验收** |
| 优先级 | P0 |
| 页面 | `en/html/01-welcome.html` → `Welcome.vue` |

**输入**：双击图标 / Store 启动；`get_state` 返回的 `{saved_count, library_version, license_state, first_run}`。

**处理步骤**

1. A：Tauri 启动窗口，尺寸默认 1440×900，最小 1180×760；窗口标题 `BizSpark`；深墨蓝侧栏由前端渲染，窗口本体不抢样式。
2. A：并行拉起 Python sidecar（`bizspark-core`），等待首行 `{"event":"ready"}`；**超时 800ms 不阻塞界面**——前端先渲染首屏，sidecar 晚到只影响后续 diagnose。
3. A：sidecar 异常退出 → 自动重启 1 次；再失败则记录 `E_CORE_DOWN`，前端进入"仅浏览已存点子"的静默降级（不弹窗）。
4. F：读 `state.json`；不存在则创建空状态；**损坏则静默重建**，不丢其他目录文件，不弹窗。
5. F：`get_state` 在 100ms 内返回；`saved_count>0` 时 B 在侧栏 `My ideas` 显示条数角标。
6. B：渲染首屏，元素严格按 UI 稿顺序：
   - eyebrow：`A one-time desktop tool · No account · No subscription`
   - 主标题三行，第三行 `one idea.` 用橘色 `<em>`
   - 副文案一句（5 道题 → 3 个生意 → 一张可打印的纸）
   - **主 CTA 唯一**：`Find my 3 ideas →`（`btn btn-primary btn-lg`）
   - 次链接（文字按钮，弱化）：`Open my saved ideas`
   - 信任行：`One-time purchase · Yours forever` / `✓ Works offline` / `✓ Your answers never leave this device`
   - 右侧悬浮卡片（hero-mock，旋转 -4°）：一条 Top match 样例，仅装饰，**不可点**
7. B：`locales` 取文案；不请求网络、不弹权限、不放启动广告、不放向导。
8. A：冷启动计时打点，写 `logs/perf.log`（仅本机，默认不上传）。

**输出**：可点击首屏；`first_run=false` 持久化。

**边界与降级**：无网 → 完全一致；sidecar 未就绪 → 首屏照常，主 CTA 点击时若仍未就绪则排队等待（≤800ms）再执行；存档损坏 → 空存档；低分辨率（1280×720）→ 首屏仍一屏装下，不出现滚动条。

**验收**：冷启动到可点击 ≤1.5s；1440×900 首屏零滚动；无网络请求（H 抓包验证）；主 CTA 全页仅 1 个橘色实心按钮。

**依赖**：`get_state`（F）、`ready`（A/C）。　**用例**：T-01、T-02、T-03、T-28。

---

### F02 诊断问卷（5 题）

| 项 | 内容 |
|---|---|
| 负责人 | **B（交互/页面）主，C（答案校验）辅，F（缓存）辅** |
| 优先级 | P0 |
| 页面 | `02-quiz.html` → `Quiz.vue`（示例稿为第 2 题·资金，其余 4 题同版式） |

**题目表（写死，不许加题、不许改顺序、不许加自由文本）**

| # | key | 标题（en） | 控件 | 选项（value / 显示文案） | 默认 |
|---|---|---|---|---|---|
| Q1 | `country` | Where are you starting? | 单选 6 卡 | US / CA / UK / AU / SG / PH（国旗 + 国名 + 币种小字） | 系统区域猜测，猜不中 `US` |
| Q2 | `capital` | How much can you put in to start? | 单选 4 卡 | `<500` Almost nothing — under $500；`500-2k` $500 – $2,000；`2k-10k` $2,000 – $10,000；`10k+` $10,000+ | 无，必选 |
| Q3 | `hours` | Hours per week? | 单选 3 卡 | `<10` / `10-25` / `full` | 无，必选 |
| Q4 | `assets` | What do you already have? | **多选 7 项** | car / kitchen / laptop / design / coding / spare_room / local_network，另含 `Nothing yet`（选它清掉其余） | `[]`，可全不选 |
| Q5 | `risk` | How much risk is OK? | 单选 3 卡 | `no_impact` / `small_loss` / `can_absorb` | 无，必选 |

**处理步骤**

1. B：进入即渲染 5 点 stepper（已完成 ✓ / 当前橘 / 待办灰），标签固定 `About you / Money / Time / Resources / Ready`。
2. B：每屏**只渲染 1 题**，题干 + 一行小字说明；选项为 `OptionCard` 大卡（图标 + 标题 + 一行解释）。
3. B：单选点击 → 立刻 `sel` 高亮（橘边 + 橘底 radio）→ **0.35s 自动进下一题**，不需要再点 Next；这 0.35s 内重复点击忽略。
4. B：Q4 多选 → 可连选，出现唯一例外按钮 `Done`；点 `Nothing yet` 清空其余选中，再点别的选项自动取消它。
5. B：`← Back` 返回上一题，**不丢答案**；从结果页 `Change my answers` 回来时带上次答案预选。
6. F：每次选择后 `save_answers` 落 `state.json` 的 `last_answers`（仅本地缓存，设置里可清）。
7. B：未选时主推进不可用（置灰），**不弹必填校验提示**。
8. B：Q5 完成后**不发请求、不显示"计算中"loading**（本地 300ms 内出结果），直接路由到 Results，并并行调用 `diagnose`。
9. C：收到 `diagnose` 前按 §3.1 校验；非法值静默回退到最近合法值或默认，不报错。

**输出**：`QuizAnswers`（§3.1）；页面路由到 `Results.vue`。

**边界与降级**：断网 → 完全一致；答案缓存损坏 → 按默认重来，不弹窗；连点 → 去重；Q4 全不选 → `assets=[]` 合法，引擎按"无特殊资源"处理。

**验收**：全程点击 ≤6 次（Q4 多算 1 次）；无键盘输入；无自由文本；无弹窗；从首屏到结果页 ≤45 秒（真人操作）。

**依赖**：`diagnose`（C）、`save_answers`（F）。　**用例**：T-04…T-09。

---

### F03 本地匹配引擎（核心逻辑，客户端内）

| 项 | 内容 |
|---|---|
| 负责人 | **C 全责，D 提供库与 schema，H 写引擎用例** |
| 优先级 | P0 · **最高护城河，不得做成 API** |
| 页面 | 无界面（结果页 F04 消费其输出） |

**输入**：`QuizAnswers` + `library/current.json`（F 提供合并后的工作库）。

**处理步骤（逐步实现，顺序不得调换）**

1. **载入**：读工作库 → 逐条过 §3.8 V-01…V-05 轻量校验（启动时已由 D 的构建校验过，运行期只做 `status/枚举` 快检）。失败条目**跳过**，不中断。
2. **① 硬过滤**（任一不满足即剔除）：
   - `capital_tier` 覆盖所选档：规则为 `<500` 只留 `<500`；`500-2k` 留 `<500` + `500-2k`；`2k-10k` 留前三档；`10k+` 全部。**资金档向上兼容，不向下**。
   - `hours_per_week`：用户 `<10` 只留 `<10`；`10-25` 留 `<10`+`10-25`；`full` 全部。
   - `countries` 含所选国家，且 `legal_blocks` **不含**该国。
   - `status == active`。
   - `maturity == saturated` → **标记但不剔除**（步骤 6 用）。
3. **② 软打分**（8 维，权重写死在 `engine/score.py` 常量，不给用户调、不写进设置）：

| 维度 | 权重 | 计算口径 |
|---|---|---|
| 资金贴合度 | 20% | `min_capital` 落在该档中位区间得满分，越界线性衰减 |
| 技能/资源匹配 | 20% | `skills_needed ∩ 用户隐含技能` + `assets_needed ∩ assets` 的 Jaccard；`none` 视为全匹配 |
| 时间匹配 | 15% | `hours_per_week` 与用户档越接近越高 |
| 风险承受匹配 | 15% | `risk_level` ↔ `risk` 映射表：`no_impact→low`、`small_loss→medium`、`can_absorb→high`，命中满分，相邻 0.6 |
| 回本速度 | 10% | `payback_days` ≤30 满分，≤90 0.7，≤180 0.4，其余 0.2 |
| 渠道可得性 | 10% | `channel_ids` 在该国覆盖中可用数量 / 总数 |
| **趋势新鲜度** | **5%** | `wave` 越新越高、`maturity=emerging/growing` 加分，`mature` 减半，`saturated` 记 0 |
| 复购型偏好 | 5% | `recurring=true` 满分，否则 0.5 |

   > **趋势新鲜度锁死 5%**：用户要的是"他做得成的生意"，不是"最酷的技术"。禁止为追 AI 浪潮把低资金用户硬塞 Agent 创业（V-08 从数据侧再兜一层）。
4. **③ 已看降权**：与 `state.json.saved[].id` 相同的条目 ×0.85，避免每次都推同样三条。
5. **④ 排序**：总分降序 → 同分按 `payback_days` 升序 → 再同分按 `id` 字典序（**保证可重复、可测试**）。
6. **⑤ 克制输出**：取 Top 3；`saturated` **不进 Top 3**（除非可用条目不足，见步骤 8）；生成 `match_pct`（把总分线性映射到 60–99 整数，仅展示用）。
7. **⑥ Why 文案**：用模板 + 答案具体词拼一句，模板池按命中维度分 6 组，例如：
   - 资金+时间命中 → `"Low money, laptop only, repeat monthly income — matches your budget and time."`
   - 本地资源命中 → `"You have a car and a fixed local area — the highest-margin match in your city."`
   - **禁止**出现 `algorithm / AI / score / recommended by / based on intelligent` 等词。
8. **⑦ 降级**（硬要求）：硬过滤后可用条目 <3 → **只放宽时间档一次**（`<10→10-25`，`10-25→full`，`full` 不再放宽）→ 重算；仍不足则输出实际 1–2 条 + `degraded=true` + `degrade_note="Try a slightly bigger budget next time."`；**绝不返回空数组、绝不空白页、绝不报错**。
9. **⑧ 统计**：`checked` = 载入条目数；`filtered` = `checked - ideas.length`。结果页那行小字只用这两个数。
10. **⑨ 返回**：`DiagnoseResult`（§3.3），全程不联网、不写用户数据到日志。

**输出**：§3.3 JSON。

**边界与降级**：库为空/全损坏 → 回退 `resources/baseline_v1.json`（安装包内置只读副本）再算；仍失败 → `E_LIBRARY_FALLBACK` 静默 + 用内置最小 3 条兜底条目（D 预置 `fallback_ideas.json`）；任何异常都不得让前端白屏。

**验收**：312 条库在最低配笔记本（4GB/双核）上，第 5 题答完到出结果 ≤300ms；同答案重跑 10 次结果**完全一致**；飞行模式全程无出网；`saturated` 条目永不出现在 Top3；AI 类条目在 `<500 + <10h + no_impact` 组合下占比 ≤1/3。

**依赖**：`library/current.json`（F+D）、`state.saved`（F）。　**用例**：T-10…T-18。

---

### F04 结果页

| 项 | 内容 |
|---|---|
| 负责人 | **B 全责（渲染），C 提供数据，H 验收视觉** |
| 优先级 | P0 |
| 页面 | `03-results.html` → `Results.vue` |

**处理步骤**

1. B：顶部 eyebrow `Ready in 40 seconds`；H1 `Three businesses you can actually start.`
2. B：**复述用户答案**成一句：`Based on $500–$2,000, under 10 hours a week, a laptop, and United States. Nothing was sent anywhere.`（按实际答案动态拼；国家用全名映射表）。
3. B：三张 `IdeaCard` 并排（`grid g3`），每张**固定 7 个元素、顺序不变**：
   `01 / 03` 编号 · 右上 `94% MATCH` · 标题 · 一句话 · `Why this fits you:` 引句块 · 3 个标签 · 主按钮 `See the one-page plan →`。
4. B：卡片顶部 3px 色条按序：橘 / 深墨蓝 / 绿（稿里 `:nth-child` 规则，移植到组件 props `accentIndex`）。
5. B：只有 **1–2 条**（降级）时，栅格自适应为 1–2 列，**不留空卡位**；同时在页面底部显示 `degrade_note` 一句温和文案。
6. B：底部弱化操作：`← Change my answers`（回 Quiz 带预选）、`Save all three`（批量调 `save_idea` ×N）。
7. B：右下小字（**唯一允许出现"筛过多少条"的地方**）：`Older, saturated ideas are kept in the library but never pushed to the top.`
8. B：统计行 3 个数：`checked / filtered / 3`，标签固定 `ideas checked locally / ruled out by your money & time / worth your Monday`。
9. B：**禁止**渲染：筛选器、排序下拉、分页、「查看更多」、对比勾选（对比只在 `My ideas` 页）、广告位、升级解锁。
10. B：`Save all three` 后不弹大成功弹窗，仅按钮变 `✓ Saved`（2s 后还原）。

**输出**：可点进详情；可批量存档。

**边界与降级**：`diagnose` 超时（>800ms）→ 显示上一轮缓存结果（F 存 `last_result`）；无缓存则停留在本页骨架屏 ≤1s 后重试一次，仍失败静默回 Welcome（不报错）。

**验收**：与 `en/ui/03-results.png` 逐像素比对；3 张卡等高；无新增控件；`match_pct` 只以小字出现。

**依赖**：`diagnose`（C）、`save_idea`（F）。　**用例**：T-19、T-20、T-31。

---

### F05 点子详情页

| 项 | 内容 |
|---|---|
| 负责人 | **E（数据装配 + 渲染）主，B（组件）辅，D（内容）供数** |
| 优先级 | P0 · **产品价值全在这页** |
| 页面 | `04-detail.html` → `Detail.vue` |

**处理步骤**

1. E：`get_idea(id)` → 取 `Idea` + 合并国家覆盖 → 生成 `IdeaDetail`（§3.4：`cost_total` / 按 currency 格式化的 `cost_rows` / `payback_hint`）。
2. B：页头 eyebrow `Idea 01 / 03 · 94% match`；H1 = `title`；lead = `one_liner`（**不新增 `detail_intro` 之类字段**，§3.2 契约保持冻结）。
   > **口径澄清**：V1.0 §4 F05 表格里列过「定价 + 毛利粗算」「本地合规提示」两项；本版按 L09「UI 稿即验收基线」执行——这两项**只进 `IdeaDetail` 数据对象与 F06 导出的 PDF**（PDF 版式见 F06 步骤 3），**详情页不新增任何可见模块**。谁都不许为了"把字段显示全"往页面上加 kv 块或 warn 块。
3. B/E：左侧主区 **4 个内容卡，顺序写死**（与 `en/html/04-detail.html` DOM 完全一致）：

| 卡 | 标题 | 渲染规则 |
|---|---|---|
| M1 | What it costs to start | `cost_rows` 逐行 `kv`；末行 **Total to first invoice** 用橘色加粗；逐项列钱，禁止"大概几千" |
| M2 | Your first 7 steps | `steps` 渲染 `<ol class="steps">`，序号 `01…07`，**纯展示，不加勾选框**（V1.0 提过的"可勾选"按 L09 以 UI 稿为准，本期不做，放第二版评估） |
| M3 | Where the first customers come from | `first_customers` → `pill-list`；**按国家取覆盖值**；禁止"social media promotion" |
| M4 | Three ways people get this wrong | `pitfalls` 3 条 → 黄底 `warn` 块；每条具体动作 |

   派生字段 `pricing_hint` / `payback_days` / `compliance_note` **只供 PDF 与数据对象使用**，不在详情页另起模块。B/E 不得自行调序、不得加第五张卡。
4. B：右侧 `sticky` 卡：eyebrow `Your one-page plan` → 旋转 -1.2° 的 A4 缩略 `PaperPreview`（纯 CSS 占位，不渲染真实内容）→ 一句说明 → **主按钮 `Export my plan ↓`** → 次按钮 `← Back to 3 ideas` → `🔒 Nothing is uploaded. Ever.`
5. B：滚动时右侧卡 `position:sticky; top:24px` 保持可见。
6. E：所有内容 100% 来自本地字段，**渲染不依赖网络**；国家缺失覆盖时回退主条目，不空白。

**输出**：详情页 + 可触发导出。

**边界与降级**：`id` 不存在 → 静默回 Results；字段缺 `pitfalls` 第 3 条（运行期脏数据）→ 用库内通用兜底句补齐，不显示 `undefined`；超长文案 → 截断到 UI 不溢出（CSS `line-clamp`），不换行撑破卡片。

**验收**：4 个内容卡齐全、无新增可见模块；右侧 sticky 有效；断网渲染完整；与 `04-detail.png` 比对无偏差；页面不出现 `wave / maturity / version / score` 等词。

**依赖**：`get_idea`（C/E）、国家覆盖（D）。　**用例**：T-21…T-24、T-32。

---

### F06 启动包生成与导出

| 项 | 内容 |
|---|---|
| 负责人 | **E 全责（Python reportlab + 前端完成页），A 提供系统另存为，F 提供路径** |
| 优先级 | P0（PDF） / P1（CSV） |
| 页面 | `05-export.html` → `Export.vue` |

**处理步骤**

1. B：点 `Export my plan` → 前端发 `export_plan {id, path?}`。
2. A：未带 path 时调 Tauri 系统原生「另存为」对话框，默认目录 `$DOCUMENTS/BizSpark/`，默认文件名 `BizSpark-Plan-{slug}.pdf`，过滤 `*.pdf`；用户取消 → 静默回详情页，不提示。
3. E：用 **reportlab** 在本地渲染**单页 A4 / Letter 自适应** PDF，版式按以下固定顺序（与详情页一致）：
   - 页眉小字 `BizSpark · One-page plan`
   - 标题 `title` + `one_liner`
   - `What it costs` 表格（逐项 + 合计）
   - `First 7 steps` 编号列表
   - `Pricing & payback` 一行
   - `First customers` 列表
   - `3 pitfalls` 列表
   - `Local note` 一句
   - 页脚 `BizSpark · one-time purchase · generated on this device`
4. E：**无水印、无二维码、无在线链接、无「分享给朋友」、无页码之外的额外元素**；字体 Helvetica 内置；英文版不嵌 CJK 字体（内部自检包若导出中文，允许回退系统字体，仅内部用）。
5. E：写盘成功后返回 `{filename, bytes, pages:1, path}`；**不上传、不生成在线链接、不经过任何服务器**。
6. F：记住本次导出目录到 `state.json.export_dir`，下次默认带上（设置里可改）。
7. B：完成页 `05-export.html`：大绿勾 `✓` → eyebrow `Done, on your computer` → H1 `Your plan is ready.` → 一句 `One PDF, one page, no watermark. It's a file on your disk — not a link, not an account, not something that can expire.` → 文件行（图标 / 文件名 / `Saved to Documents / BizSpark · 214 KB · 1 page` / `✓ Saved`）→ 按钮 `Open folder`（A 调系统文件管理器）/ `Find another idea` → 分隔线 → 小字 `No subscription. No auto-renew. Buy once, use it as long as you like — even with the internet off.`（由价格配置渲染，**首版不含金额**）
8. B：下方补充卡 `What's inside the PDF` / `Optional extras`（CSV 说明），纯说明文字。
9. E（P1）：`export_csv` 可选导出成本表 CSV，同目录，列 `item, amount, currency`；**仍在本地、仍归用户**。

**输出**：本地 PDF（必）+ 可选 CSV。

**边界与降级**：目录不可写 / 磁盘满 → **唯一允许的用户提示**：`Choose another folder`（重新弹另存为），已填步骤不丢；缺字体 → 回退内置字体不报错；渲染异常 → 记录 `E_PDF_RENDER` 并提供「重试一次」，不弹红色错误框。

**验收**：导出 ≤2s；**断网导出成功**；PDF 恰好 1 页、可直接打印；用 `pdftotext` 能抽到 7 步与成本合计；文件不含任何外网 URL。

**依赖**：`IdeaDetail`（E）、系统对话框（A）、`export_dir`（F）。　**用例**：T-25…T-27、T-33、T-34。

---

### F07 我的点子（本地留存）

| 项 | 内容 |
|---|---|
| 负责人 | **F 全责（存储/状态机），B 页面，H 用例** |
| 优先级 | P0 |
| 页面 | `06-saved.html` → `Saved.vue` |

**处理步骤**

1. F：`save_idea(id)` 追加到 `state.json.saved[]`，字段 `{id, saved_at(ISO date), match_pct, min_capital}`；**同 id 去重**，不覆盖时间。
2. F：`list_saved()` 按 `saved_at` 倒序返回；`clear_saved()` 二次确认后清空（确认弹窗是**本功能唯一允许的确认框**，文案温和，非红色）。
3. B：列表项 `mini` 卡：图标 / 标题 / `Saved 12 Nov 2026 · From $120 · 94% match` / `Open` 按钮。
4. B：`Compare two ideas` → 并排两栏，**只显示三项**：起步成本、每周时间、回本天数；不显示评分、不显示权重、不加第三栏。
5. F：`compare_ideas(ids[2])` 返回三项字段；不足 2 条时按钮置灰（不弹提示）。
6. B：空态不是空白页：居中图 + `Double-click Find my 3 ideas. It takes 40 seconds.`
7. B：底部提示 `💡 Made your first sale? Come back and run the 5 questions again with a bigger budget. Same button, same 3 cards.`（轻引导复访，**不做推送、不做提醒**）。
8. F：主按钮 `Find new ideas →` 回 Quiz（带 `last_answers` 预选，用户可直接改预算）。

**输出**：本地存档列表。

**边界与降级**：`state.json` 损坏 → 静默重建空存档，其他目录不动；`saved[].id` 在库中已 `retired` → 仍可打开（用磁盘上保留的条目），标注不显示；重装系统后存档丢失属**预期行为**，隐私说明里写明，不提供云同步补救。

**验收**：无账号无同步；重启软件存档仍在；飞行模式全功能可用；无任何出网请求。

**依赖**：`get_idea`（C/E）。　**用例**：T-35…T-37、T-29。

---

### F08 商机库（护城河本体）

| 项 | 内容 |
|---|---|
| 负责人 | **D 全责（内容 + schema + 校验 CLI），F 消费，H 抽检** |
| 优先级 | P0 |
| 页面 | `08-update.html` 只展示版本与时间线，**不展示库编辑界面** |

**处理步骤**

1. D：按 §5 生产 `baseline_v1.json`，**312 条**，26 行业 / 6 国 / 4 资金档。
2. D：`schema.json` 为 §3.2 的机器可读版；`validate.py` 实现 §3.8 V-01…V-12，接入 CI，构建失败即阻断。
3. D：为每国写 `CountryOverride`（币种 / 获客渠道 / 合规一句），FX 用静态 `fx.json`（**不联网取汇率**）。
4. D：`fallback_ideas.json` 预置 3 条极简兜底条目（库全损时用），同样过校验。
5. A：把 `baseline_v1.json` 作为 **Tauri resource 只读内置**；F 首次启动复制到 `library/current.json` 作为工作库。
6. F：工作库只读合并产物，**任何用户操作都不改 `baseline_v1.json`**。
7. D：**老商机不删**——过时只把 `maturity` 调 `saturated` 并降权（F03 步骤 6 拦截 Top3），磁盘条目永久保留。
8. D：内容纪律——每条必须能回答「明天早上第一步干什么」；写不出不入库；禁止「做自媒体 / 开网店 / 社交媒体推广」类空话（V-09 机器拦截）。

**输出**：`baseline_v1.json` / `schema.json` / `fx.json` / `fallback_ideas.json` / `validate.py`。

**边界与降级**：运行期脏条目 → F03 步骤 1 跳过；整库损坏 → F 回退内置只读副本 → 再失败用 `fallback_ideas.json`。

**验收**：`validate.py` 全绿；V-08（AI 类 ≤12%）不过警告；随机抽 30 条由 H 人工核「第一步可执行」。

**依赖**：无（D 可 W1 并行开工）。　**用例**：T-38、T-39。

---

### F09 月度增量更新（联网的唯一理由）

| 项 | 内容 |
|---|---|
| 负责人 | **F（客户端合并/回滚/降级）主，A（拉取）辅，D（生成/发布）辅** |
| 优先级 | P1 |
| 页面 | `08-update.html` → `Library.vue` |

> **口径校准（必须写进代码注释）**：**1 号是发布窗口，不是商机自动长出来**。2025-03 包里出现 AI 商机，前提是 2 月由 D 写进 3 月包；2025-07 包里出现商业智能体商机同理。**换挡 = 加权迁移**，新条目浮上来、老条目沉下去，永不消失。按真实日历现在已是 **2026-11**，AI / 智能体是**当下存量**，所以 baseline 首版就自带这批条目（§5.2 的 6%），从 **2026-12-01** 起按月换血，不能等"到某年才出现"。

**处理步骤**

1. A：每月 1 号（或启动离上次检查 ≥30 天）**静默** GET `https://static.<域名>/bizspark/manifest.json`，超时 3s、重试 0 次；请求**不带任何用户标识 / UA 自定义 / cookie**。
2. A：任何失败（无网 / 超时 / 404 / 证书 / 解析错 / 托管到期 / 忘续费）→ **静默跳过**，不重试轰炸、不弹错、不写用户可见日志、不阻塞启动。
3. A：`manifest.latest` ≤ 本地 `library_version` → 结束。
4. A：`min_client > 当前客户端版本` → 静默跳过（老客户端不强行吃新包）。
5. A：下载 `files[]`（合计 ≤200KB），校验 JSON 可解析 + `target_baseline` 匹配；失败 → 静默跳过。
6. F：**合并前先备份** `library/current.json` → `library/rollback/{version}.json`（保留最近 3 份）。
7. F：按序应用 `add`（完整 Idea，过 §3.2 快检）/ `revise`（**仅白名单字段**，见 §3.7）/ `retire`（只置 `status=retired`，**不删磁盘条目**）。
8. F：合并后跑 V-01/V-02/V-11；**失败整体回滚**到备份，用户无感。
9. F：成功后更新 `state.json.library_version`，写一条本地时间线记录（供 Library 页展示），**不上传任何确认**。
10. B：Library 页只显示：当前版本一行（`2026.11 · 312 ideas · 26 industries · 6 countries`）+ `✓ Up to date` 标签 + 4 条时间线 + 右侧说明卡 + 右下轻 toast `Library checked · you're up to date. No action needed.`
11. B：时间线内容（写死在 `locales`，由 F 给版本号动态填）：`1 Dec 2026 · Next / Agent-era small services`、`1 Nov 2026 · Installed / AI-assisted service ideas`、`1 Oct 2026 / Local service pack`、`Baseline · v1.0 / 312 ideas shipped inside the installer`。
12. B：右侧卡 `How the monthly swap works` 三行 `kv`：`Update fails / no Wi-Fi → Silently skipped`、`Your saved ideas → Untouched`、`Cost to you → Static files only`；橘底卡 `Why new ideas keep showing up`（讲季节与换挡，不出现 `wave / maturity` 术语）。
13. D：`hosting/publish.py` 负责生成 delta → 跑 `validate.py` → 上传静态托管 → 更新 `manifest.json`；**每月你唯一的固定活儿，半天到一天**。
14. **免费**：买断用户不因更新再付一分钱；商品页写明更新是免费增强、不是义务、断网不影响已有内容。

**输出**：本地工作库换版；用户零操作。

**边界与降级**：断网一个月 → 回来后一次性合并缺失 delta（按 release 顺序逐包应用）；托管关一整天 → 软件启动与功能**无任何变化**；用户手动关掉「每月检查」→ 100% 离线，永久。

**验收**：T-30 系列（把托管关掉、拔网线、改 manifest 为 404 / 脏 JSON / 超大包，逐一验证零弹窗零阻塞）；合并失败自动回滚；`retire` 后磁盘条目仍在。

**依赖**：`manifest/delta`（D）、拉取（A）、`state.library_version`（F）。　**用例**：T-30-1…T-30-6、T-40。

---

### F10 授权激活（分渠道）

| 项 | 内容 |
|---|---|
| 负责人 | **G 全责，A（指纹采集/凭证文件权限）辅，B 页面** |
| 优先级 | P0（分销版） / Store 版 = 0 代码 |
| 页面 | `07-activate.html` → `Activate.vue`（**Store 版永不出现此页**） |

**渠道矩阵（写死）**

| 渠道 | 支付 | 授权码 | 客户端代码 |
|---|---|---|---|
| Microsoft Store 付费下载 | 平台 | 无 | **不写任何授权代码**，编译期用 `feature=store` 裁掉 `license` 模块 |
| Mac App Store | 平台（StoreKit） | 无 | 同上 |
| Gumroad / Lemon Squeezy | 平台 | 有 | 走本 F10 |

**处理步骤（分销版）**

1. 平台收款后发码（格式 `BZSP-K7Q2-M9XA-XXXX`，4 段）；G 用**离线签发工具** `license/issue.py` 生成码池，私钥**绝不进客户端包**。
2. B：激活页 eyebrow `For copies bought outside the stores`；H1 `Activate once. Use offline.`；一句说明 Store 版看不到此页。
3. B：4 个 `code-in` 输入框（第 4 段示例为 `••••` 未填态），支持粘贴整码自动分格、自动大写、过滤非字母数字。
4. B：下方 `One code works on up to 3 of your own devices.` + 设备位展示（2 亮 1 空 + `2 of 3 devices used`）。
5. G：`activate(code, device_hash)`：
   - 校验码格式与内置公钥验签；
   - 查 `license.dat`：不存在 → 新建 `{seats:[本设备], seats_max:3}`；存在且本设备已在 seats → 直接返回成功（**幂等**）；
   - 存在且 seats 已满 3 且本设备不在内 → 返回 `E_LICENSE_SEAT_FULL`（前端引导 `Changed computer? Release a seat`，**不显示"授权失败"**）；
   - 成功写 `license.dat`（权限 600）+ 本地签名凭证。
6. G：**设备指纹** = `sha256(平台 + 主板/CPU 序列 + 磁盘卷标 + 系统安装 ID)` 规范化串；**禁止 IP / MAC 明文 / 用户名 / 文件路径**（海外 VPN 与换网常见，IP 会误伤）。
7. G：激活成功后**不再回连**；每次启动只读本地凭证验签（离线），**无网络校验、无心跳、无"欢迎回来"**。
8. B：绿底 notice 原样：`Activation is not a login. Once verified, a small signed file is kept on this device. After that the tool works with the internet off — we never check again.`
9. B：右侧深墨蓝卡原样：`One-time purchase` / `Buy once. Own it forever.` / 5 条 ✓（No subscription / No auto-renewal / No account, no email / Core features work offline / Library updates are free & optional）。
10. B：白卡 `Why a code at all?` 原样：讲"安装包可被复制，码只证明这份副本付过钱，**不是不信任你**"。
11. G：`release_seat` 首版**不做后台**：点了给一段说明 + 你的支持邮箱，人工处理；**不做账号、不做找回密码**。
12. B：主按钮 `Activate & start →` → 成功直接进 Welcome。

**输出**：`license.dat`（本地签名凭证）。

**边界与降级**：拔网线后重启 → 功能 100% 可用；换电脑/重装 → 用掉第 3 个位；第 4 台 → 温和引导释放；码输错 → 输入框下**一行温和提示**（不改版式、不弹窗）；凭证文件损坏 → 允许重新输入同一码（幂等），不锁死。

**验收**：T-41…T-45；Store 构建产物里 `grep` 不到 `activate` 相关代码路径；激活后抓包零出网。

**依赖**：`license_status`（G）、指纹采集（A）。　**用例**：T-41…T-45。

---

### F11 设置（6 项封顶）

| 项 | 内容 |
|---|---|
| 负责人 | **F 全责，B 页面** |
| 优先级 | P1 |
| 页面 | `09-settings.html` → `Settings.vue` |

**6 项写死，多一项都不做**

| # | 项 | 控件 | 默认 | 说明文案 |
|---|---|---|---|---|
| 1 | Country | 下拉 6 国 | 系统猜测 | Sets currency, local channels and the one-line legal note |
| 2 | Language | 下拉，仅 `English` 可见 | English | `English in v1.0`（**内部自检包显示 `中文（自检）`，且不可切换**） |
| 3 | Where plans are saved | `Change…` 系统目录 | `$DOCUMENTS/BizSpark` | 显示当前路径 |
| 4 | Monthly library check | 开关 | 开 | Optional. Failure is always silent. |
| 5 | Follow system appearance | 开关 | 开 | Light / dark |
| 6 | Anonymous crash notes | 开关 | **关** | Off by default. No answers, no ideas, no files. |

**处理步骤**

1. F：`get_settings` / `set_settings` 读写 `state.json.settings`；非法键忽略不报错。
2. B：右侧隐私卡 eyebrow `Privacy, in one sentence` + 大标题 `Your answers, your saved ideas and your exported plans never leave this device.` + 一句 `The only outbound request is "is there a newer idea file?" once a month. It carries no user data. Turn it off and the tool is 100% offline, forever.`
3. B：About 卡 4 行 `kv`：`Version 1.0.0` / `Library 2026.11 (312 ideas)` / `Licence One-time · activated`（绿）/ `Account None`；按钮 `Check for updates`（手动触发，仍静默失败）/ `View licence`。
4. F：崩溃日志开启时**只写错误码 + 版本 + 时间戳**，禁止写答案、点子 id、文件路径、设备指纹。
5. **禁止新增**：账号、通知、主题商店、高级设置、实验功能、数据上传开关、语言切换。

**验收**：设置项恰好 6 行；关闭月度检查后抓包零出网；深浅色跟随系统不闪白。

**依赖**：`state.settings`。　**用例**：T-46、T-47。

---

### F12 客户端自动更新

| 项 | 内容 |
|---|---|
| 负责人 | **A 全责** |
| 优先级 | P1 |
| 页面 | 无独立页（轻提示） |

**处理步骤**

1. Store 版：完全交给商店，**客户端不写 updater、不弹更新提示**（编译期裁掉）。
2. 分销版：启动时检查新安装包版本（与 F09 的 `manifest.json` **分离、互不依赖**）→ 有新版只显示一句 `A newer version is ready for next launch`，**不强制、不阻断当前使用、不自动重启**。
3. 库更新 ≠ 程序更新：两者用不同文件、不同开关、不同失败处理；F09 挂了不影响 F12，反之亦然。
4. 下载失败静默跳过。

**验收**：Store 包无 updater 代码；分销版提示不阻断主链路。

**依赖**：无。　**用例**：T-48。

---

### F13 空态、异常与统一降级口径

| 项 | 内容 |
|---|---|
| 负责人 | **F 统一实现，全员遵守，H 逐条验收** |
| 优先级 | P0 |

| 场景 | 行为（写死） |
|---|---|
| 首次启动 / 无网 | 一切正常，用 baseline |
| 更新失败 / 托管挂了 / 忘续费 | 静默跳过，界面无任何变化 |
| sidecar 未就绪 / 崩一次 | 自动重启 1 次；再失败仅浏览已存点子，不弹窗 |
| 匹配结果不足 3 条 | 放宽时间档**一次**，展示 1–2 条 + 温和一句，绝不空白页 |
| 整库损坏 | 内置只读副本 → 再 `fallback_ideas.json` |
| `state.json` 损坏 | 静默重建，不弹窗、不动其他文件 |
| 导出路径不可写 | 只提示换文件夹 |
| 详情页脏字段 | 兜底句补齐，不出现 `undefined` |
| 第 4 台设备激活 | 引导释放席位，不报「授权失败」 |
| 系统深浅色切换 | 跟随，不闪白 |
| 用户断网一个月 | 完全无感，回来后按序合并缺失 delta |
| 用户取消另存为 | 静默回详情页 |

**全局禁令**：红色错误弹窗、`Please check your connection`、错误码外露、loading 转圈超过 1s、任何需要用户理解的报错。

---

### F14 非功能需求与双构建

| 项 | 内容 |
|---|---|
| 负责人 | **A（性能/包体/构建）主，H 验收，B/G 配合** |
| 优先级 | P0 |

**F14.1 性能指标（H 用 `qa/perf/` 脚本量）**

| 指标 | 阈值 |
|---|---|
| 冷启动到可点击 | ≤1.5s |
| `diagnose`（312 条，4GB 双核） | ≤300ms |
| 导出 PDF | ≤2s |
| 首次打开到拿到 PDF（真人） | ≤3 分钟，点击 ≤8 次 |
| 常驻内存 | ≤300MB |
| 包体 | Windows ≤80MB / Mac ≤80MB（Tauri + PyInstaller sidecar 实测目标 ≤60MB） |
| 出网请求 | 核心链路 **0**；仅月度 manifest + 分销版首次激活 |

**F14.2 其它**

- 离线：飞行模式完整跑通「答题 → 3 条 → PDF」。
- 隐私：零用户数据出设备；唯一出网请求不含任何用户标识。
- 可访问性：键盘可操作、对比度 ≥4.5:1、系统字号跟随。
- 崩溃日志默认关闭，开启后内容白名单见 F11 步骤 4。

**F14.3 中文自检构建（关键，防止做成第二个产品）**

1. 同一套组件 / CSS / 逻辑 / 9 页，**只换 `zh-CN.json`**，产物名 `BizSpark-SelfCheck-CN-1.0.0`。
2. **软件内不出现语言切换按钮**；设置页第 2 项在自检包里只显示 `中文（自检）` 且不可操作。
3. 不签名上架、不进 `qa/store-assets/`、不进任何商品页素材、不对外分发。
4. `zh-CN.json` 保持 `BizSpark / Microsoft Store / Mac App Store / PDF / CSV / AI / Google Maps / Yelp / Etsy / Shopify / Nextdoor / 激活码样例 / 文件名 / 版本号` 不译。
5. 不换中式字体、不加红金纹样印章、不因中文字少挪版式；中文由系统 CJK 字体回退。
6. **同步纪律**：任何改动先改英文版 → 逐字镜像中文版 → 两版同时重出 9 张截图；分歧以英文版为准。
7. CI 校验 V-10（键集合差集为 0）不过则构建失败。

**验收**：T-28（抓包）、T-29（离线）、T-40（宕机）、V-10；中文包 `grep` 不到 `locale.switch`。

---

## §5 商机库内容生产规范（D 的执行手册）

### 5.1 总量与分布基线（312 条）

| 维度 | 分布 |
|---|---|
| **行业 26 个** | 本地服务 28%（87）· 线上副业 24%（75）· B2B 小外包 18%（56）· 内容与数字产品 14%（44）· 手作与线下小生意 10%（31）· **AI / 智能体相关 6%（19）** |
| **资金 4 档** | `<500` 40%（125）· `500-2k` 32%（100）· `2k-10k` 20%（62）· `10k+` 8%（25） |
| **时间 3 档** | `<10` 45% · `10-25` 35% · `full` 20% |
| **形态** | online 45% · offline 35% · hybrid 20% |
| **国家** | 6 国全覆盖 ≥80%；US/UK 各 ≥90%；SG/PH ≥60% |
| **wave** | `local-service / mobile-internet / digital-product` 合计 ≥70%；`ai-llm / ai-agent / bi-agent` **合计 ≤12%**（V-08） |
| **maturity** | `emerging` 15% · `growing` 35% · `mature` 35% · `saturated` ≤15%（V-07） |

> **低门槛能上手的生意永远占大头**；AI 类是「跟上时代」，不是把库写成 AI 专区。按真实日历 2026-11，AI / 智能体是**当下存量**，baseline 首版就自带，不能等"到某年才出现"。
>
> **【PM 修订 2026-11-14】** 老板实测发现"同一门生意换个地点，工具价差 14 倍"（擦玻璃刮水器 USD 28→3,478）。根因是变体成本按 `min_capital` 固定比例机械缩放。已按"**同一座城市同样的工具花同样的钱**"归一（`tools/normalize_cluster_costs.py`：簇内工具价统一为基准条目价，`min_capital`=成本合计，`capital_tier` 重算）。因此本表资金档分布目标修订为 **`<500` 65% · `500-2k` 23% · `2k-10k` 5% · `10k+` 8%**；AI/智能体组目标 6%→**10%**（2026-12 换血包合入后实际 10.1%，月度换血按设计优先补 AI 内容）。推荐引擎同步增加**同行业簇去重**：Top3 必须来自 3 门不同生意，簇内代表取该用户条件下得分最高的变体。
>
> **【PM 修订 2026-11-14 · 货币展示口径（老板两轮拍板定稿）】** 工具不在中国发售、面向全球用户，金额**一律"货币符号 + 数字"**，全站唯一口径：
> `$`（USD）· `CA$`（CAD）· `£`（GBP）· `A$`（AUD）· `S$`（SGD）· `₱`（PHP）。
> ① **禁止**外露币种码写法（`CAD 690` / `USD 500`）与裸数字（`起步 120`）——"代码写法"会让用户觉得工具把他当外人、降低信任；
> ② 美元也带 `$`，`$` 单独出现即美元；加/澳/新元必须带国家前缀，避免歧义；
> ③ CAD 统一写 `CA$`（比 `C$` 更明确是"加拿大"）；后端 `engine.money.SYMBOLS`、`state/store.py`、`web/src/money.ts`、`web/src/bridge/price.ts` 四处符号表必须同值；
> ④ 文本里的旧写法（`$49` / `49 美元` / `500–2,000 美元`）由 `engine.money.localize_text` 统一改写为符号样式，USD 也不例外；
> ⑤ 唯一例外：CSV 导出属数据表，保留 `amount`（数值）+ `currency`（币种码）两列，便于用户自己套公式。

### 5.2 26 行业清单（D 按此分文件）

```
本地服务(8)：review-reply / home-cleaning / pet-care / lawn-garden / mobile-car-wash /
             errand-runner / window-cleaning / appliance-tuneup
线上副业(6)：product-photo / resume-polish / ebook-formatting / calendar-va /
             transcription-local / online-tutoring
B2B 小外包(5)：invoice-chasing / google-maps-setup / simple-bookkeeping /
               quote-templates / inbox-tidy
内容与数字产品(4)：template-packs / neighbourhood-newsletter / local-guide-pdf / stock-photo-local
手作与线下(2)：market-stall / repair-corner
AI / 智能体(1)：ai-agent-setup-local   ← 仅 19 条，集中在这一类
```

### 5.3 每条商机的填写模板（D 逐条过「明天早上第一步」测试）

```json
{
  "id": "us-svc-ai-014",
  "title": "Local shop review-reply desk",
  "one_liner": "Help 20 local shops reply to Google/Yelp reviews with a fixed template pack",
  "min_capital": 120, "capital_tier": "<500", "hours_per_week": "<10",
  "countries": ["US","CA","UK","AU","SG","PH"], "online_or_offline": "online",
  "legal_blocks": [],
  "skills_needed": ["writing","basic_english"], "assets_needed": ["laptop"],
  "risk_level": "low", "payback_days": 30, "recurring": true,
  "channel_ids": ["google-maps","nextdoor","walk-in","chamber"],
  "cost_breakdown": [
    {"item":"Domain + one-page site","amount":12},
    {"item":"Template pack (you write it once)","amount":0},
    {"item":"20 printed intro letters","amount":8},
    {"item":"First month of a mail tool","amount":15}
  ],
  "steps": ["Pick one street with 20+ independent shops","Write 10 reply templates",
            "Print 20 letters with one free sample reply","Walk in on a Tuesday morning",
            "Offer $49/month for up to 15 replies, first month free",
            "Deliver in 24 h by email","Ask shop #1 for one introduction after week three"],
  "pricing_hint": "$49/month for up to 15 replies",
  "first_customers": ["Google Maps 4-star shops with unanswered reviews","Nextdoor local business posts","Your own street, in person","Chamber of commerce newsletter"],
  "pitfalls": ["Don't sell 'AI writing' — sell 'your reviews get answered by tomorrow'",
               "Don't take more than 25 clients before templates are done",
               "Check local rules on soliciting businesses in person"],
  "compliance_note": "US: check local business-name registration and sales-tax rules.",
  "wave": "ai-llm", "trend_tags": ["ai","local-service","retainer"],
  "first_seen": "2026-11", "maturity": "growing",
  "version": 3, "updated_at": "2026-11-01", "status": "active"
}
```

### 5.4 内容审核清单（D 自检 + H 抽检 30 条）

- [ ] `title` 一眼知道卖什么，不含 `AI-powered / revolutionary / 一站式` 等虚词
- [ ] `one_liner` 回答了「谁付钱」
- [ ] `steps[0]` 是**明天早上能做的具体动作**（有地点/对象/数量）
- [ ] `steps` 恰好 7 条，每条动词开头
- [ ] `cost_breakdown` 逐项列钱，合计 ≈ `min_capital`
- [ ] `pricing_hint` 含具体数字
- [ ] `first_customers` ≥3 且是具体渠道名，**不是** "social media / 线上推广 / 打广告"
- [ ] `pitfalls` 恰好 3 条且是可执行告诫
- [ ] `compliance_note` 只有一句，不是法律意见
- [ ] 6 国覆盖或明确回退；SG/PH 渠道写成 Facebook / WhatsApp / Google Maps 本地形态
- [ ] `wave` 与 `maturity` 符合 §5.1 分布
- [ ] 无空话、无 emoji、无中文（英文版内容库）

### 5.5 月度 delta 生产 SOP（你每月半天到一天的活儿）

1. 挑 **10–20 条**新商机（当月技术/平台/季节变化），填 §5.3 模板。
2. 对存量做 `revise`：把过气条目 `maturity → saturated`（只改白名单字段），改渠道/成本/合规。
3. 平台关停 / 政策变化的标 `retire`（**只置 status，不删**）。
4. `python hosting/publish.py --release 2026-12-01` → 自动跑 `validate.py`（V-01…V-12）→ 生成 `delta_2026-12.json` → 更新 `manifest.json` → 上传静态托管。
5. 本地用自检包跑一遍 T-40（合并失败回滚）与 T-30 系列再发布。
6. **不额外向老用户收钱**，买断说话算话。

> 这是桌面图标不被删掉、用户做成第一单后还愿意回来找第二个点子的唯一原因，也是「代码能被抄、库抄不走」的那道墙。

---

## §6 八人分工总表与逐人任务卡

### 6.1 分工总表（一人一模块，边界不重叠）

| 人 | 角色 | 主责模块 | 核心交付物 | 主责功能 | 关键依赖 |
|---|---|---|---|---|---|
| **A** | 技术负责人 / 桌面壳与发布 | `apps/desktop/src-tauri/`、`scripts/` | Tauri 壳、sidecar 桥、双构建、MSIX/签名、CI | F01、F12、F14、F09 拉取 | 全员（联调总协调） |
| **B** | 前端 / 视觉还原 | `apps/web/` | 9 屏 Vue 组件、`cmd.ts`、`tokens.css`、`locales/` | F01、F02、F04、F05(组件)、F06(完成页)、F07(页面)、F09(页面)、F11(页面) | A 的 IPC 桥、C/E/F/G 的 cmd |
| **C** | 诊断引擎 | `apps/core/engine/`、`main.py` 分发 | JSONL 主循环、硬过滤、8 维打分、Why、降级 | F02(校验)、F03、F04(数据)、F05(`get_idea`) | D 的库 + schema、F 的工作库 |
| **D** | 数据 / 商机库 / 内容工程 | `apps/core/library/`、`content/`、`hosting/` | 312 条 baseline、schema、validate.py、delta 工具链 | F08、F09(发布侧)、F03(供数) | 无（W1 即可并行开工） |
| **E** | 详情装配 / 本地导出 | `apps/core/render/` | `IdeaDetail` 装配、reportlab 单页 PDF、CSV | F05、F06 | C 的 `get_idea`、D 的字段、A 的系统对话框 |
| **F** | 本地状态 / 合并 / 降级 | `apps/core/state/` | `state.json`、存档、设置、delta 合并与回滚、全部降级路径 | F07、F09(客户端)、F11、F13 | D 的 delta、A 的拉取、C 的 `state.saved` |
| **G** | 授权 / 安全 / 合规审查 | `apps/core/license/`、离线签发工具 | 激活码、机器指纹、签名凭证、3 席位、权限审查 | F10、§2.6 错误码审查、隐私审查 | A 的指纹采集与文件权限 |
| **H** | QA / 测试 / 发布素材 | `qa/` | T-01…T-48 用例、E2E、性能脚本、商店素材、隐私政策、验收报告 | §9 §10 §11 | 全员（不写业务代码，但有权打回） |

**协作规则**

1. A 是唯一联调入口；跨模块问题先在 §7 契约表里找，找不到由 A 裁决并补进契约。
2. H **不写业务代码**，但拥有验收否决权；任一 T 用例不过，对应负责人不得进入下一周任务。
3. D 的内容生产与 C 的引擎**并行**：W1 双方按 §3.2 冻结字段后各干各的，互不等待。
4. B 不自己算任何业务结果；C/E/F/G 不写任何界面字符串（文案只在 `locales/`）。
5. 每人任务卡里的「禁止事项」与 §1.3 铁律同等效力。

### 6.2 程序员 A 任务卡（技术负责人 / 壳与发布）

| 任务号 | 内容 | 文件 | 验收 |
|---|---|---|---|
| A-01 | 建仓库、分支规范、PR 模板、CI 骨架（跑 V-01…V-12、V-10、lint） | 根 `README.md`、`.github/` | 8 人都能按规范提 PR |
| A-02 | Tauri 2 初始化：窗口 1440×900 / 最小 1180×760 / 标题 / 深浅色跟随 | `tauri.conf.json`、`main.rs` | 双平台起窗一致 |
| A-03 | sidecar 生命周期：启动、等 `ready`、800ms 不阻塞界面、崩溃自动重启 1 次 | `main.rs` | T-02、T-03 |
| A-04 | IPC 桥：JSONL 双向转发 + `req_id` 匹配 + 超时 800ms + 错误码透传（不透给用户） | `main.rs`、`bridge.rs` | §7.1 全表联通 |
| A-05 | 系统能力：另存为对话框、打开文件夹、文件路径白名单、最小权限 capabilities | `main.rs`、`capabilities/` | G 审过最小权限 |
| A-06 | 机器指纹采集原语（**按 G 定的规范实现，不自创算法**） | `fingerprint.rs` | G 验签通过、无 IP/MAC 明文 |
| A-07 | 静态托管 GET：3s 超时、0 重试、无用户标识、失败静默 | `updater.rs` | T-30-1…T-30-6 全过 |
| A-08 | 双构建：`build:en` / `build:cn`（仅换 locales + `build-mode.txt`） | `scripts/build-*.sh` | 两包 9 页一致，中文包无切换按钮 |
| A-09 | 打包：Windows `MSIX`(Store) + `.exe`(分销)、Mac 签名 `.app/.dmg`；Store 构建编译期裁掉 `license` 与 `updater` | `scripts/pack.sh`、`sign.sh` | 包体 ≤80MB；Store 包 grep 不到 activate |
| A-10 | F12 分销版轻更新提示（与 F09 完全分离） | `updater.rs` | T-48 |
| A-11 | 性能打点（冷启动/diagnose/导出），写本机 `logs/perf.log` | `main.rs` | F14.1 全部达标 |
| A-12 | 联调总协调：每日 15 分钟站会、契约变更记录、`docs/changelog-contract.md` | `docs/` | W2 契约冻结、W4 功能冻结 |
| A-13 | 配合 H 出商店技术材料（沙盒说明、权限说明、签名证书） | `qa/store-assets/` | 审核无补件 |
| **A-14** | `config/pricing.json` 落库、构建期注入六构建目标、CI 金额门禁脚本（T-59） | `config/` `scripts/` | 全项目零金额硬编码；改配置全端生效 |

**禁止**：在 Rust 层写业务判断 / 在 Rust 层写界面文案 / 让 sidecar 监听端口 / 给 Store 包带授权代码 / 因"顺手"加任何用户可见控件。

**工期**：W1（A-01…A-04）→ W2（A-05…A-07）→ W3（A-08、A-11）→ W4（A-09、A-10）→ W5（A-09 签名、A-13）→ W6（发布值守）。

### 6.3 程序员 B 任务卡（前端 / 视觉还原）

| 任务号 | 内容 | 文件 | 验收 |
|---|---|---|---|
| B-01 | 把 `en/html/assets/style.css` 的 `:root` token 逐值移植，不改任何色值/圆角/阴影 | `tokens.css` | 与稿零偏差 |
| B-02 | 抽公共组件：`AppShell`(246px 侧栏+70px topbar)、`OptionCard`、`IdeaCard`、`StepList`、`PaperPreview`、`KvRow`、`Toggle`、`Tag` | `components/` | 9 页复用，无重复 CSS |
| B-03 | 9 个 View 逐页还原，**文件名与 `en/html` 一一对应** | `views/*.vue` | 与 `en/ui/*.png` 逐像素比对（H 验） |
| B-04 | 路由：Welcome→Quiz→Results→Detail→Export；侧栏 6 项可直达 Saved/Library/Activate/Settings | `router.ts` | 每条链路 ≤8 次点击 |
| B-05 | `cmd.ts`：唯一 IPC 出口，封装 §2.4 全部 cmd、统一超时与静默失败 | `bridge/cmd.ts` | A 审过；组件里零 `fetch` |
| B-06 | F02 问卷交互：选中 0.35s 自动进下一题、Q4 多选 + `Done`、Back 带预选、连点去重 | `Quiz.vue` | T-04…T-09 |
| B-07 | F04 结果页：3 卡 7 元素固定、降级 1–2 卡自适应、答案复述句、统计行 | `Results.vue` | T-19、T-20 |
| B-08 | F05 组件支持：4 个内容卡顺序照 DOM、不加第五张卡、右侧 sticky、脏字段不显示 undefined | `Detail.vue` | T-21…T-24 |
| B-09 | F06 完成页 + F07 列表/空态/对比两栏 + F09 Library 时间线 + F11 设置 6 行 + F10 激活页 | 各 View | 各页与稿一致 |
| B-10 | `en-US.json` 全量文案键；`zh-CN.json` 逐键镜像（不增删键、不译白名单） | `locales/` | V-10 通过 |
| B-11 | 深浅色跟随系统、键盘可操作、对比度 ≥4.5:1、系统字号跟随 | 全局 | T-47 |
| B-12 | 配合 H 重出两版 9 张截图 + 两张总览图 | `qa/store-assets/` | 与 UI 稿一致 |
| **B-13** | `[data-price-slot]` 占位 + `price-render.js` 渲染器；`locales` 增 `price.*` 键（不含金额） | `views/` `locales/` | T-59 过；hidden 时 9 屏只讲功能 |

**禁止**：组件里写死任何界面字符串 / 自己算分数或筛点子 / 加筛选器、排序、分页、语言切换、loading 转圈 >1s / 因中文字少挪版式 / 给中文包加中式字体与装饰。

**工期**：W1（B-01…B-03 骨架）→ W2（B-04…B-06）→ W3（B-07、B-08）→ W4（B-09、B-10、B-11）→ W5（B-12 + 视觉回归）→ W6（素材定稿）。

### 6.4 程序员 C 任务卡（诊断引擎）

| 任务号 | 内容 | 文件 | 验收 |
|---|---|---|---|
| C-01 | `main.py` JSONL 主循环：`req_id`、cmd 分发、`ready` 首行、统一错误码 | `main.py` | §2.4 全 cmd 可路由 |
| C-02 | §3.1 答案校验（枚举命中、非法静默回退） | `engine/quiz.py` | T-09 |
| C-03 | 步骤 1–2 硬过滤（资金向上兼容、时间档、`countries/legal_blocks/status`、saturated 标记不剔） | `engine/filter.py` | T-10、T-11 |
| C-04 | 步骤 3 八维打分，权重常量化（趋势锁 5%）、风险映射表、渠道可得性 | `engine/score.py` | T-12、T-13、T-14 |
| C-05 | 步骤 4–5 已看降权 ×0.85、排序三级 tiebreak（**结果可重复**） | `engine/score.py` | T-15 |
| C-06 | 步骤 6–7 Top3 克制输出 + `match_pct` 60–99 + 6 组 Why 模板池 | `engine/why.py` | T-16、T-17 |
| C-07 | 步骤 8 降级：放宽时间档**一次**、1–2 条 + `degrade_note`、绝不空数组 | `engine/score.py` | T-18、T-31 |
| C-08 | 步骤 9–10 统计 `checked/filtered`、零出网、不写用户数据到日志 | `engine/` | T-28、T-29 |
| C-09 | 整库损坏回退链：`current.json → baseline 只读副本 → fallback_ideas.json` | `engine/` | T-38 |
| C-10 | `get_idea(id)` 装配（合并国家覆盖、派生 3 字段），交给 E 渲染 | `engine/detail.py` | §3.4 |
| C-11 | 引擎单元测试（312 条夹具、8 维边界、同答案重跑 10 次一致） | `apps/core/tests/` | H 纳入 T-10…T-18 |

**禁止**：做任何网络调用 / 暴露权重给用户 / 输出 >3 条 / 返回空数组 / 为追 AI 提高趋势权重 / 写界面文案。

**工期**：W1（C-01、C-02 + 与 D 冻字段）→ W2（C-03、C-04）→ W3（C-05…C-08、C-10）→ W4（C-09、C-11）→ W5 联调 → W6 值守。

### 6.5 程序员 D 任务卡（商机库 / 内容工程）

| 任务号 | 内容 | 文件 | 验收 |
|---|---|---|---|
| D-01 | 与 C 在 W1 冻结 §3.2/§3.7 字段，产出机器可读 `schema.json` | `apps/core/data/schema.json` | 契约冻结签字 |
| D-02 | `validate.py` 实现 V-01…V-12，接入 CI，构建失败阻断 | `library/validate.py` | 全绿 |
| D-03 | 按 §5.1 分布表建 `distribution.csv`，26 行业分文件 | `content/` | 分布偏差 ≤2% |
| D-04 | 生产 **312 条** baseline，逐条过 §5.4 清单（含"明天早上第一步"测试） | `content/ideas/` | H 抽检 30 条全过 |
| D-05 | 6 国 `CountryOverride`（币种/获客渠道/合规一句）+ 静态 `fx.json`（**不联网取汇率**） | `apps/core/data/` | V-06 无警告 |
| D-06 | `baseline_v1.json` + `fallback_ideas.json`（3 条极简兜底，同样过校验） | `apps/core/data/` | V-01…V-05 通过 |
| D-07 | `delta_tool.py`：add/revise/retire 三操作生成 + 白名单字段检查 + V-11 | `library/delta_tool.py` | T-40 |
| D-08 | `hosting/publish.py`：一键生成 → 校验 → 上传 → 更新 `manifest.json` | `hosting/` | 月度 SOP 可复现 |
| D-09 | 首月 `delta_2026-12.json` 样例（+14 条 bi-agent、若干 revise、1 条 retire） | `hosting/` | §3.7 格式、过校验 |
| D-10 | 内容纪律巡检：V-08（AI ≤12%）、V-09（空话拦截）、V-07（saturated ≤20%） | CI | 三条不过警告 |

**禁止**：写"做自媒体/开网店/社交媒体推广"类空话 / 删老商机（只降 maturity）/ 联网取汇率 / 把库写成 AI 专区 / 单独改前端。

**工期**：W1（D-01…D-03）→ W2（D-04 前 150 条、D-05）→ W3（D-04 后 162 条、D-06）→ W4（D-07…D-10）→ W5 抽检修订 → W6 起转月度 SOP。

### 6.6 程序员 E 任务卡（详情装配 / 本地导出）

| 任务号 | 内容 | 文件 | 验收 |
|---|---|---|---|
| E-01 | `IdeaDetail` 装配：`cost_total`、`cost_rows`（按 currency 格式化）、`payback_hint` | `render/detail.py` | §3.4 |
| E-02 | 4 个内容卡数据映射（定价/合规只进 PDF 与数据对象），顺序照 DOM | `render/detail.py` | T-21 |
| E-03 | reportlab 单页 A4/Letter 自适应版式，9 个内容块顺序写死 | `render/pdf.py` | T-25、T-26 |
| E-04 | 无水印 / 无二维码 / 无在线链接 / 页脚固定 / Helvetica 内置 | `render/pdf.py` | `pdftotext` 校验 |
| E-05 | 写盘 + 返回 `{filename, bytes, pages:1, path}`；全程本地 | `render/pdf.py` | T-27、T-33 |
| E-06 | 脏字段兜底句（缺第 3 条坑、超长文案截断），不出现 `undefined` | `render/detail.py` | T-32 |
| E-07 | `export_csv`（P1）：`item, amount, currency` 三列，同目录 | `render/csv.py` | 列正确 |
| E-08 | 配合 A 的另存为：取消 → 静默回详情；不可写 → 只提示换文件夹 | `render/pdf.py` | T-34 |
| E-09 | 导出性能 ≤2s；配合 H 出 PDF 快照比对 | `qa/perf/` | F14.1 |

**禁止**：上传任何文件 / 生成在线链接 / 加水印或二维码 / 加"分享"按钮 / 用联网字体 / 改 UI 稿模块顺序。

**工期**：W1（E-01）→ W2（E-02、E-03 骨架）→ W3（E-03…E-06）→ W4（E-07…E-09）→ W5 联调 → W6 值守。

### 6.7 程序员 F 任务卡（本地状态 / 合并 / 降级）

| 任务号 | 内容 | 文件 | 验收 |
|---|---|---|---|
| F-01 | `state.json` schema + `paths.py` 统一路径（§2.5），首次创建、损坏静默重建 | `state/store.py`、`paths.py` | T-35 |
| F-02 | `get_state` / `save_answers` / `last_result` 缓存（结果页超时兜底用） | `state/store.py` | T-03、T-31 |
| F-03 | 存档命令：`save_idea` 去重 / `list_saved` 倒序 / `clear_saved` 二次确认 / `compare_ideas` 只返三项 | `state/store.py` | T-36、T-37 |
| F-04 | 设置 6 项读写，非法键忽略；崩溃日志白名单（错误码+版本+时间戳） | `state/settings.py` | T-46、T-47 |
| F-05 | delta 合并：备份 → add/revise/retire（白名单）→ V-01/V-02/V-11 → 失败整体回滚 | `state/merge.py` | T-40 |
| F-06 | 回滚目录保留最近 3 份；断网一月回来按 release 顺序逐包合并 | `state/merge.py` | T-30-6 |
| F-07 | `library_version` 与本地时间线记录（供 Library 页展示，不上传确认） | `state/merge.py` | T-40 |
| F-08 | §4 F13 **全部降级路径**统一实现（表内 12 个场景逐条） | `state/` 全局 | H 逐条验 |
| F-09 | 工作库只读合并产物，任何用户操作不改 `baseline_v1.json` | `state/merge.py` | 文件校验和不变 |
| F-10 | 导出目录记忆 `export_dir` | `state/store.py` | 第二次默认带上 |

**禁止**：云同步 / 账号 / 写用户数据到日志 / 弹红色报错 / 硬删磁盘商机条目 / 让更新失败阻塞启动。

**工期**：W1（F-01、F-02）→ W2（F-03、F-04、F-10）→ W3（F-05…F-07）→ W4（F-08、F-09）→ W5 联调 → W6 值守。

### 6.8 程序员 G 任务卡（授权 / 安全 / 合规）

| 任务号 | 内容 | 文件 | 验收 |
|---|---|---|---|
| G-01 | 定机器指纹规范（交 A 实现）：`sha256(平台+主板/CPU 序列+磁盘卷标+系统安装 ID)`，**禁 IP/MAC 明文/用户名/路径** | `docs/fingerprint-spec.md` | A 按规范实现 |
| G-02 | 离线签发工具 `issue.py` + 码池格式 `BZSP-XXXX-XXXX-XXXX`；**私钥绝不进客户端包** | `tools/issue.py`（不打包） | 包内 grep 不到私钥 |
| G-03 | `activate`：验签、幂等、3 席位、`E_LICENSE_SEAT_FULL` 温和返回 | `license/activate.py` | T-41…T-44 |
| G-04 | `license.dat` 写入权限 600、Ed25519 本地验签、每次启动**只读本地不回连** | `license/signature.py` | T-45 抓包零出网 |
| G-05 | `release_seat` 首版无后台：说明 + 支持邮箱，人工处理 | `license/activate.py` | 无账号无找回 |
| G-06 | 审 `capabilities/` 最小权限、审 §2.6 错误码不外露、审隐私声明与商品页合规文案 | `docs/security-review.md` | H 签收 |
| G-07 | Store 构建编译期裁剪检查（授权模块不进包） | 配合 A | T-42 |
| G-08 | 激活页 5 条 ✓ 文案与 notice 文案核对（与 `07-activate.html` 逐字一致） | 配合 B | 视觉验收 |

**禁止**：做成登录 / 心跳校验 / 用 IP 绑设备 / 私钥进包 / 报"授权失败" / 加账号体系。

**工期**：W1（G-01、G-02）→ W2（G-03、G-04）→ W3（G-05…G-08）→ W4 安全复审 → W5 配合打包 → W6 值守。

### 6.9 程序员 H 任务卡（QA / 测试 / 发布素材）

| 任务号 | 内容 | 文件 | 验收 |
|---|---|---|---|
| H-01 | 编写 T-01…T-48 用例（前置/步骤/预期/负责人/优先级），逐条可执行 | `qa/cases/` | 全员评审通过 |
| H-02 | E2E 脚本：主链路、离线、宕机、存档、导出、授权、双构建 | `qa/e2e/` | 一键跑全量 |
| H-03 | 性能脚本：冷启动 / diagnose / 导出 / 内存 / 包体 / 抓包出网数 | `qa/perf/` | F14.1 达标 |
| H-04 | 离线演练：飞行模式 + 托管关一整天 + manifest 404/脏 JSON/超大包 | `qa/cases/T-30*` | 零弹窗零阻塞 |
| H-05 | 视觉回归：两版各 9 张截图 + 2 张总览图，与 `en/ui`、`cn/ui` 逐页比对 | `qa/store-assets/` | 偏差 ≤2px 观感 |
| H-06 | 商店素材：图标、截图（**只用英文版**）、商品页文案、隐私政策一页、支持邮箱 | `qa/store-assets/` | 审核无补件 |
| H-07 | 商品页文案 5 条必写：`One-time purchase` / `No subscription` / `No auto-renewal` / `Works offline` / `Your data stays on this device` | 同上 | G 审过 |
| H-08 | 中文包检查：无语言切换按钮、不进商店素材、V-10 键一致 | `qa/cases/` | T-28 |
| H-09 | 抽检 D 的 30 条商机内容（§5.4 清单） | `qa/content-review.md` | 全过 |
| H-10 | 每周出验收报告 + W4 功能冻结签字 + W6 上架前最终签字 | `qa/reports/` | 有签字记录 |
| H-11 | 维护 §11 追溯矩阵状态列（每条功能 ↔ 用例 ↔ 结论） | `docs/traceability.md` | 100% 覆盖 |
| **H-12** | T-59：全项目零金额扫描 + 改 `display_mode` 后两版 9 屏回归；审商品页文案无金额 | `qa/cases/` | W4 前通过 |

**禁止**：替业务模块写代码 / 未过用例就放行下一周 / 把中文截图放进商店素材。

**工期**：W1（H-01、H-11 骨架）→ W2（H-02、H-03 框架）→ W3（逐模块验 C/D/E/F）→ W4（H-04、H-05、H-09）→ W5（H-06…H-08、H-10）→ W6 最终签字与值守。

---

## §7 模块间接口契约（并行开发不互相等）

### 7.1 契约冻结表（W1 末由 A 主持，全员签字）

| 契约 | 供给方 | 消费方 | 冻结内容 | 变更代价 |
|---|---|---|---|---|
| K-1 `Idea` schema | D | C / E / F | §3.2 全字段 + 枚举 | 高（要改 4 人） |
| K-2 `QuizAnswers` | B | C / F | §3.1 五字段 | 中 |
| K-3 `DiagnoseResult` | C | B | §3.3，长度 1–3 | 中 |
| K-4 `IdeaDetail` | C→E | B / E | §3.4 + DOM 顺序 | 中 |
| K-5 IPC cmd 表 | A+C+E+F+G | B | §2.4 全表 + 错误码 | 高 |
| K-6 `state.json` | F | A / B / C | §F-01 结构 | 中 |
| K-7 delta / manifest | D | A / F | §3.7 三操作 + 白名单 | 高 |
| K-8 `License` | G | A / B | §3.5 + 指纹规范 | 中 |
| K-9 `locales` 键集合 | B | 双构建 / CI | §3.6，V-10 | 低 |
| K-10 错误码表 | G 审 | 全员 | 附录 D | 低 |
| **K-11 价格配置** | A | B / H / 六构建目标 | §3.9 `config/pricing.json` + `assets/pricing.js` | 中 |

**冻结后**：改任一契约必须开 `contract/` PR、@全员、同步改 `schema.json` + 测试用例 + 本文档，A 记录进 `docs/changelog-contract.md`。**不允许私聊改字段。**

### 7.2 前端 → 核心调用时序（B 照此写，不必等后端实现）

```
Welcome:   get_state ──────────────► F
Quiz:      save_answers(每题) ─────► F
           diagnose(Q5 完成) ──────► C ──(读 current.json)── F/D
Results:   save_idea ×N ───────────► F
Detail:    get_idea(id) ───────────► C/E
Export:    export_plan(id, path) ──► E ──(系统对话框)── A
Saved:     list_saved / compare_ideas / clear_saved ──► F
Library:   check_library(静默) ────► A ──► F(apply_delta)
Settings:  get_settings / set_settings ──► F
Activate:  activate / license_status / release_seat ──► G
```
B 可先用 `qa/mocks/cmd-mock.ts`（H 提供）按 K-3/K-4 假数据开发，**不等 C/E 完成**。

### 7.3 A → F 更新交接

| 交接物 | 格式 | 失败处理 |
|---|---|---|
| `manifest.json` 原文 | string | 解析失败 → A 静默丢弃，不叫 F |
| `delta_*.json` 原文 | string | 同上 |
| `apply_delta(payload)` | `{manifest, files[]}` | F 校验 → 备份 → 合并 → 回滚；返回新版本号或 `skipped` |

A **不解析业务字段**，F **不发网络请求**，职责不越界。

### 7.4 C ↔ F 数据交接

- C 只读 `library/current.json`（F 产物）与 `state.saved`（F 产物），**不写**任何状态文件。
- F 只写状态/库文件，**不算分**。
- 结果缓存 `last_result` 由 F 写，供 `diagnose` 超时兜底（F04 步骤 10）。

### 7.5 E ↔ A 系统能力交接

- E 只返回"要存的默认文件名 + 内容字节流意图"，**不自己弹窗**。
- A 提供 `save_dialog(default_path)` → 返回用户选中路径或 `cancelled`。
- 取消 → E 不写盘、不报错；不可写 → A 返回 `E_FS_READONLY`，E 触发一次 `Choose another folder`。

---

## §8 六周排期（逐人逐周）

### 8.1 周任务表

| 周 | A | B | C | D | E | F | G | H | 里程碑 |
|---|---|---|---|---|---|---|---|---|---|
| **W1** | A-01…04 + **A-15 价格配置** + **S1/S2/S3 封装 spike** 仓库/壳/sidecar/IPC | B-01…03 token/组件/9 页骨架 | C-01、C-02 主循环/校验 | D-01…03 schema/校验/分布表 | E-01 装配骨架 | F-01、F-02 状态/路径 | G-01、G-02 指纹规范/签发工具 | H-01、H-11 用例/矩阵骨架 | **W1 末：K-1…K-10 契约冻结签字** |
| **W2** | A-05…07 系统能力/指纹/GET | B-04…06 路由/cmd/问卷 | C-03、C-04 硬过滤/打分 | D-04 前 150 条 + D-05 国别覆盖 | E-02、E-03 四卡映射/PDF 骨架 | F-03、F-04、F-10 存档/设置 | G-03、G-04 激活/验签 | H-02、H-03 E2E/性能框架 | **W2 末：主链路可跑通（可用 mock 库）** |
| **W3** | A-08、A-11 双构建/打点 | B-07、B-08 结果/详情 | C-05…C-08、C-10 排序/Why/降级/get_idea | D-04 后 162 条 + D-06 baseline/fallback | E-03…E-06 PDF/写盘/兜底 | F-05…F-07 合并/回滚/版本 | G-05…G-08 解绑/权限/文案 | 逐模块验 C/D/E/F，出首份报告 | **W3 末：312 条库到位，真库跑通 diagnose** |
| **W4** | A-09、A-10 打包/轻更新 | B-09…B-11 其余 5 页/locales/a11y | C-09、C-11 回退链/单测 | D-07…D-10 delta 工具/首月包/巡检 | E-07…E-09 CSV/另存为/性能 | F-08、F-09 全部降级路径 | 安全复审、Store 裁剪检查 | H-04、H-05、H-09 宕机/视觉/内容抽检 | **W4 末：功能冻结（H 签字），之后只修缺陷** |
| **W5** | A-09 签名、A-13 技术材料 | B-12 两版截图回归 | 联调、缺陷修复 | 抽检修订、月度 SOP 演练 | 联调、PDF 快照 | 联调、合并演练 | 配合打包、验签复核 | H-06…H-08、H-10 商店素材/隐私政策/双版检查 | **W5 末：候选发布包 RC1 出包** |
| **W6** | 发布值守、热修 | 视觉最终确认 | 值守 | 12 月 delta 预备 | 值守 | 值守 | 值守 | **最终签字 + 上架提交** | **W6：Microsoft Store / Mac App Store 上架；分销版随后** |

### 8.2 联调点（A 主持，全员到）

| 点 | 时间 | 检查内容 |
|---|---|---|
| J-1 | W1 末 | 契约 K-1…K-10 冻结；`schema.json` 与 `locales` 键集合通过 CI；**S1/S2/S3 三个封装 spike 全过，且已出第一个可装包** |
| J-2 | W2 末 | 用 mock 库跑通「首屏→5 题→3 卡→详情→PDF」；B 与 C/E 的 cmd 全联通 |
| J-3 | W3 末 | 换真库 312 条；diagnose ≤300ms；6 国覆盖正确；PDF 单页 |
| J-4 | W4 末 | 功能冻结；T-01…T-48 首轮全跑；宕机/离线演练 |
| J-5 | W5 末 | RC1 双平台包 + 双构建 + 商店素材齐备 |
| J-6 | W6 | 上架前最终签字（H）+ 灰度观察 |

### 8.3 并行性说明（为什么 8 人不会互相等）

- D 的库与 C 的引擎**只靠 K-1 契约耦合**，W1 冻结后完全并行；C 先用 H 的 3 条夹具开发。
- B 靠 K-3/K-4 mock 数据开发 9 屏，不等 C/E。
- G 的授权与 A 的指纹靠 G-01 规范解耦；A 只实现原语。
- F 的合并靠 K-7 与 D 的样例 delta 解耦；A 只负责把原文交过来。
- H 从 W1 就写用例，用例本身就是各模块的可执行规格。

---

## §9 联调、测试用例与验收

> 格式：`编号 | 前置 | 步骤 | 预期 | 负责人 | 优先级`。H 维护，A 主持跑，**任一 P0 不过不得进入下一周**。
> **编号说明**：共 T-01…T-58，其中 **T-30 是系列名**，实际用例为 T-30-1…T-30-6（无单独 T-30 行）；**T-49…T-58 为封装用例**，详见《打包封装与上架方案V1.0》§8，与本章一起跑。合计 64 条可执行用例（含 T-59）；文中「T-30 系列 / T-30*」均指这 6 条。

### 9.1 启动与问卷（T-01…T-09）

| 编号 | 前置 | 步骤 | 预期 | 负责 | 级 |
|---|---|---|---|---|---|
| T-01 | 全新安装 | 双击图标 | ≤1.5s 出首屏；1440×900 零滚动；仅 1 个橘色主 CTA | A/B | P0 |
| T-02 | 无 | 强杀 sidecar 后启动 | 自动重启 1 次；首屏不阻塞、不弹窗 | A | P0 |
| T-03 | sidecar 两次失败 | 启动 | 进入"仅浏览已存点子"静默降级，无任何红色提示 | A/F | P0 |
| T-04 | 首屏 | 点 `Find my 3 ideas` | 进 Q1，stepper 第 1 点橘 | B | P0 |
| T-05 | Q2 | 点 `$500 – $2,000` | 0.35s 自动进 Q3；不出现 Next 按钮 | B | P0 |
| T-06 | Q3/Q4 | 连点 3 次同一选项 | 选中态稳定、不重复进页 | B | P0 |
| T-07 | Q4 | 选 3 项 → 点 `Nothing yet` → 再选 1 项 | 清空逻辑正确；`Done` 可用 | B | P0 |
| T-08 | Q5 完成 | 点 `← Back` 两次后重来 | 答案全部保留预选 | B/F | P0 |
| T-09 | 构造非法 `QuizAnswers` | 发 `diagnose` | 静默回退到合法值，不报错、不弹窗 | C | P1 |

### 9.2 引擎（T-10…T-18）

| 编号 | 前置 | 步骤 | 预期 | 负责 | 级 |
|---|---|---|---|---|---|
| T-10 | 真库 312 条 | `<500 + <10 + no_impact` | 只返回 `capital_tier=<500` 且 `hours=<10` 的条目；资金不向下兼容 | C | P0 |
| T-11 | 某条 `legal_blocks=["US"]` | 选 US 诊断 | 该条被剔除，不出现在结果 | C | P0 |
| T-12 | 固定答案 | 查 `score.py` 权重 | 趋势新鲜度恰为 5%，其余 7 维合计 95% | C | P0 |
| T-13 | 固定库 | 把某条 `wave` 改成 `bi-agent` 后重算 | 排名变化幅度符合 5% 权重，不会因换标签直接进 Top3 | C | P0 |
| T-14 | `saturated` 条目 | 诊断 | 永不进 Top3；仍在库文件中 | C/D | P0 |
| T-15 | 同一答案 | 重跑 10 次 | 结果**完全一致**（含 tiebreak） | C | P0 |
| T-16 | 结果 | 检查 `why` | 含答案具体词；不含 `algorithm/AI/score/recommended by` | C | P0 |
| T-17 | 结果 | 检查长度 | `ideas.length` ∈1–3；`match_pct` ∈60–99 整数 | C | P0 |
| T-18 | 构造仅 2 条可用 | 诊断 | 放宽时间档**一次**；输出 2 条 + `degraded=true` + 温和 note；无空白页 | C | P0 |

### 9.3 结果与详情（T-19…T-24、T-31、T-32）

| 编号 | 前置 | 步骤 | 预期 | 负责 | 级 |
|---|---|---|---|---|---|
| T-19 | 正常结果 | 比对 `en/ui/03-results.png` | 3 卡等高、7 元素顺序一致、无新增控件 | B/H | P0 |
| T-20 | 正常结果 | 读顶部复述句 | 与实际答案一致（金额/小时/资源/国家全名） | B | P0 |
| T-21 | 点进详情 | 数模块 | 4 个内容卡齐全、顺序与 `04-detail.html` DOM 一致，无新增可见模块 | B/E | P0 |
| T-22 | 详情 | 滚动到页底 | 右侧 `PaperPreview` 卡始终可见 | B | P0 |
| T-23 | 切 SG 国家 | 看 `first_customers` | 出现 Facebook / WhatsApp / Google Maps 本地渠道，非 "social media" | D/E | P0 |
| T-24 | 详情 | 全文搜索 | 不含 `wave/maturity/version/score/algorithm` | B/H | P0 |
| T-31 | `diagnose` 超时 1.2s | 进结果页 | 显示 `last_result` 缓存；无缓存则骨架 ≤1s 后重试一次 | B/F | P1 |
| T-32 | 脏数据缺第 3 条 pitfall | 进详情 | 兜底句补齐，页面无 `undefined`、无溢出 | E | P1 |

### 9.4 导出（T-25…T-27、T-33、T-34）

| 编号 | 前置 | 步骤 | 预期 | 负责 | 级 |
|---|---|---|---|---|---|
| T-25 | 详情 | 点 `Export my plan` | 弹系统另存为，默认 `$DOCUMENTS/BizSpark/`、默认文件名正确 | A/E | P0 |
| T-26 | 导出完成 | `pdfinfo` / `pdftotext` | 恰好 1 页；含 7 步与成本合计；无 URL/水印/二维码 | E/H | P0 |
| T-27 | 导出 | 计时 | ≤2s；返回 `pages:1` | E | P0 |
| T-33 | **飞行模式** | 完整导出 | 成功；抓包零出网 | E/H | P0 |
| T-34 | 目录设为只读 | 导出 | 仅提示 `Choose another folder`，重弹另存为；步骤不丢 | A/E | P1 |

### 9.5 离线 / 宕机 / 隐私（T-28、T-29、T-30-1…T-30-6、T-40）

| 编号 | 前置 | 步骤 | 预期 | 负责 | 级 |
|---|---|---|---|---|---|
| T-28 | 全新安装 + 抓包 | 跑完整主链路 | 核心链路出网请求 = **0** | H/A | P0 |
| T-29 | 飞行模式 | 答题→3 条→PDF→关→重启→看存档 | 全功能可用，存档仍在 | F/H | P0 |
| T-30-1 | 拔网线 | 启动 | 无任何变化、无弹窗 | A/F | P0 |
| T-30-2 | 托管关一整天 | 启动 + 用一遍 | 无任何变化 | A/F | P0 |
| T-30-3 | manifest 返回 404 | 启动 | 静默跳过 | A | P0 |
| T-30-4 | manifest 脏 JSON | 启动 | 静默跳过 | A | P0 |
| T-30-5 | delta 超 200KB / 字段非法 | 启动 | 静默跳过，不落盘 | A/F | P0 |
| T-30-6 | 断网一个月后恢复 | 启动 | 按 release 顺序一次性合并缺失 delta，用户无感 | F | P1 |
| T-40 | 构造合并失败 delta | 触发 apply_delta | 自动回滚到备份，版本号不变，用户无感；`retire` 条目磁盘仍在 | F/D | P0 |

### 9.6 存档 / 设置 / 授权 / 更新 / 双版（T-35…T-48）

| 编号 | 前置 | 步骤 | 预期 | 负责 | 级 |
|---|---|---|---|---|---|
| T-35 | 人为损坏 `state.json` | 启动 | 静默重建空存档，其他目录不动 | F | P0 |
| T-36 | 存 3 条，重复存同一条 | `list_saved` | 去重；按 `saved_at` 倒序 | F | P0 |
| T-37 | 选 2 条对比 | `Compare two ideas` | 只显示成本/时间/回本三项，无评分无权重 | B/F | P1 |
| T-38 | 删除 `current.json` + 破坏工作库 | 诊断 | 回退 baseline 只读副本；再破坏则用 `fallback_ideas.json` | C/F | P0 |
| T-39 | CI 跑 `validate.py` | 检查 312 条 | V-01…V-12 全绿；V-07/V-08 无警告 | D/H | P0 |
| T-41 | 分销版首次 | 输入正确码激活 | 成功；`license.dat` 权限 600；设备位 1/3 | G | P0 |
| T-42 | **Store 构建产物** | 检索包内 | 无 `activate` / `license` / `updater` 相关代码路径 | A/G | P0 |
| T-43 | 同设备重复激活 | 再输同一码 | 幂等成功，不占第 2 个位 | G | P0 |
| T-44 | 已占 3 台 | 第 4 台激活 | 温和引导 `Release a seat`，无"授权失败"字样 | G | P0 |
| T-45 | 激活后**拔网重启** | 用全部功能 + 抓包 | 100% 可用；零出网、无心跳 | G/H | P0 |
| T-46 | 设置页 | 数行数 | 恰好 6 行；无账号/通知/主题商店 | B/F | P0 |
| T-47 | 关月度检查 + 切系统深浅色 | 观察 | 抓包零出网；界面跟随不闪白 | B/F/H | P1 |
| T-48 | 分销版新版本可用 | 启动 | 仅一句 `next launch` 提示，不强制、不阻断 | A | P1 |
| **T-59** | 全量交付物 | ① 全项目扫商品售价金额 ② 改 `display_mode=visible` 且填 `amount` 后重跑两版 9 屏 ③ 改回 `hidden` | ① **零命中**（商机内容金额不计）② 4 个价格槽按配置渲染出金额、无硬编码残留 ③ 回到纯功能文案；截图与 UI 稿版式一致 | A/B/H | **P0** |

### 9.7 发布验收（H 最终签字，一条链路定生死）

1. 飞行模式：双击 → 5 题 → 3 条 → 导出 PDF → 关闭，全程无报错、零出网。
2. 静态托管关掉一整天：软件启动与功能无任何变化。
3. 首次到 PDF ≤3 分钟，点击 ≤8 次。
4. UI 与 `en/html/` 逐页比对，偏差 ≤2px 级别观感；中文包逐页无溢出、无方块字。
5. 商品页与软件内**找不到**「订阅/自动续费/登录/云服务」字样（除 `No subscription` 这类否定式文案）。
6. F14.1 六项性能全达标；包体 ≤80MB。
7. 中文自检包不签名、不进 `qa/store-assets/`、无语言切换按钮。
8. **验证关**：首批 ≥30 个真实付费用户、商品页→购买转化率 ≥3%，再考虑第二端与增值。

---

## §10 打包、签名、上架清单（A 执行，H 备料，G 审合规）

| 项 | Microsoft Store | Mac App Store | Gumroad / Lemon Squeezy |
|---|---|---|---|
| 产物 | `MSIX`（Store）/ `.exe`（分销） | 签名 `.app` / `.dmg` | `.exe` / `.dmg` |
| 构建 | `build:en` + `feature=store` | `build:en` + `feature=store` | `build:en` + `feature=reseller` |
| 收款 | 平台 | 平台 | 平台 |
| 授权码 | 不做（编译期裁掉） | 不做 | 做，3 台 |
| 退款 | 平台规则 | 平台规则 | 平台规则 |
| 商品页 5 条必写 | `One-time purchase` / `No subscription` / `No auto-renewal` / `Works offline` / `Your data stays on this device` | 同左 | 同左 + 激活码交付说明 |
| 必备材料 | 图标、英文截图（**只用 en/ui**）、隐私政策一页、支持邮箱、权限说明 | 同左 + 沙盒说明 + 签名证书 | 同左 + 码池导入 |
| 审核红线 | 非纯网页套壳（有本地引擎 + 离线能力 + 真实安装包） | 同左；4.2 风险由离线能力规避 | 无 |

**资质口径（起步阶段，写给代账会计）**：只卖海外、服务器在境外、无国内售卖页与国内支付 → 不办国内 ICP 经营性许可、不做国内 App 备案、不接微信/支付宝商户号；公司正常记账报税，跨境软件收入单独建账，按「软件出口 / 跨境服务」处理增值税口径。软著后续想办再补，不阻塞上架。海外侧准备：隐私政策一页、平台退款说明、Apple/Microsoft 商店条款。

**上架顺序**：W6 先 Microsoft Store + Mac App Store（验证「付费下载 → 打开即用」闭环），分销平台随后（这时才启用 G 的激活码）。

> **本章为清单级摘要，完整执行版见《BizSpark_打包封装与上架方案V1.0.md》**：MSIX `AppxManifest` 关键项与 `makeappx`/`msstore publish` 命令、Mac App Store 主 App 与 helper 的 entitlements 及 `codesign`、分销版 `notarytool` + `staple` 四步、Nuitka 编译选型与退路、14 条封装反向约束（已写入 §2.8）、W1 三个 spike、T-49…T-58 补充用例、中国 OPC 主体的 W-8BEN / CNAPS / 隐私政策 URL 备料节奏。
>
> **重要口径**：封装不是开发完成后的工序，而是**开发前置约束**。构建脚本 W1 落地、每周出一个可安装包；W1 三个 spike 未通过前不许写业务代码。三条产线证书族与产物严禁交叉；Store 付费下载由商店在安装前完成验证，因此 Store 版不写授权码。

---

## §11 需求追溯矩阵（H 维护状态列）

| 功能 | 主责 | 协助 | UI 页 | 契约 | 用例 | 状态 |
|---|---|---|---|---|---|---|
| F01 启动首屏 | A | B/F | 01 | K-5 K-6 | T-01…03、T-28 | 待开发 |
| F02 问卷 | B | C/F | 02 | K-2 | T-04…09 | 待开发 |
| F03 匹配引擎 | C | D/F | — | K-1 K-2 K-3 | T-10…18、T-38 | 待开发 |
| F04 结果页 | B | C | 03 | K-3 | T-19、T-20、T-31 | 待开发 |
| F05 详情 | E | B/D | 04 | K-4 | T-21…24、T-32 | 待开发 |
| F06 导出 | E | A/F | 05 | K-5 | T-25…27、T-33、T-34 | 待开发 |
| F07 我的点子 | F | B | 06 | K-6 | T-35…37、T-29 | 待开发 |
| F08 商机库 | D | F/H | 08 | K-1 | T-39 | 待开发 |
| F09 月度更新 | F | A/D/B | 08 | K-7 | T-30-1…6、T-40 | 待开发 |
| F10 授权 | G | A/B | 07 | K-8 | T-41…45 | 待开发 |
| F11 设置 | F | B | 09 | K-6 K-9 | T-46、T-47 | 待开发 |
| F12 程序更新 | A | — | — | — | T-48 | 待开发 |
| F13 降级口径 | F | 全员 | 全部 | K-10 | T-28…T-40 | 待开发 |
| F14 非功能/双构建 | A | B/G/H | 全部 | K-9 | T-28、T-29、V-10 | 待开发 |
| **价格配置** | A | B/H/G | 01 / 05 / 07 | **K-11** | **T-59** | 待开发 |

**100% 覆盖要求**：每个 F 至少 1 条 P0 用例、1 个负责人、1 张 UI 页（无界面的注明 —）；H 在 W4 冻结前把「状态」列全部刷成「已通过」，否则不放行。

---

## §12 变更流程、纪律与风险

### 12.1 变更流程（8 人团队最容易乱的地方）

1. **任何**字段 / 接口 / 页面 / 文案 / 配色变更，先提 `contract/` 或 `feat/` PR，写清影响哪条 K 契约、哪条 F 功能、哪些 T 用例。
2. A 裁决 → 若涉及 K-1/K-5/K-7 高代价契约，@全员确认。
3. 同步改：`schema.json` / `locales/en-US.json` **先改英文** → 逐字镜像 `zh-CN.json` → 改 T 用例 → 改本文档对应条款 → 两版重出截图。
4. CI 跑 V-01…V-12 + V-10 + E2E 全绿才合。
5. W4 功能冻结后**只修缺陷**，不接新需求；确需新增走「第二版」清单，不塞进 1.0.0。

### 12.2 八人共同纪律

- **英文为主、中文为镜**：任何改动先英文、后中文镜像；分歧以英文为准。
- **用户那一面不加东西**：想加按钮/筛选/提示，先问「用户会不会多一次点击」，多一次就不做。
- **界面文案只在 `locales`**，业务层不写字符串。
- **不联网就不许弹错**：所有失败静默降级，只有 F06/F03/F10 三处允许温和提示。
- **复杂沉到阴面**：库、权重、delta、验签做厚，但界面一个后台词都不露。
- **H 有一票否决**：用例不过，负责人不进下一周。

### 12.3 风险表

| 风险 | 触发信号 | 应对 | 责任 |
|---|---|---|---|
| 8 人并行改契约 | 出现「我这边字段叫 X 你那边叫 Y」 | K-1…K-10 冻结 + `contract/` PR + changelog | A |
| 追浪潮把库写成 AI 专区 | `wave=ai-*` 占比上升 | 趋势权重锁 5% + V-08 ≤12% 构建警告 | C/D |
| 规则越加越多界面变系统 | 有人提「加个筛选/加个排序」 | §12.2 第二条 + H 视觉回归 | B/H |
| 托管到期 / 忘记续费 | 静态托管账单 | 核心逻辑本地 + 静默跳过，天然免疫 | A/F |
| 安装包被转发 | 分销版流出 | 3 席位激活码；Store 版由商店兜底 | G |
| 商机内容写空话 | `first_customers` 出现 social media | V-09 构建拦截 + §5.4 清单 + H 抽检 | D/H |
| 商店审核纯网页套壳 4.2 | 被拒 | 真实安装包 + 本地引擎 + 离线能力 | A/H |
| 中文版被做成第二个产品 | 有人提「加语言切换」 | §4 F14.3 + T-28 + 不进商店素材 | A/B |
| 用户期待「永久更新」 | 客服问 | 商品页写明：买断的是软件与内置库；更新是免费增强、非义务，断网不影响已有内容 | H/G |
| sidecar 打包体积超标 | 包体 >80MB | 精简 Python 依赖（仅 reportlab）、Tauri 替代 Electron | A |

---

## 附录 A 完整商机条目示例

见 §5.3（可直接作为 `baseline_v1.json` 第一条夹具）。

## 附录 B delta 包示例

```json
{
  "target_baseline": "v1",
  "release": "2026-12-01",
  "add": [
    { "id": "us-svc-bi-021", "title": "Monthly AI-agent care for local shops", "wave": "bi-agent",
      "maturity": "emerging", "first_seen": "2026-12", "status": "active", "version": 1,
      "..." : "其余字段按 §3.2 填满，过 validate.py" }
  ],
  "revise": [
    { "id": "us-svc-ai-014", "maturity": "growing", "version": 4, "updated_at": "2026-12-01" }
  ],
  "retire": [ "xx-legacy-003" ]
}
```
> **1 号是发布窗口，不是商机自动长出来**：3 月包里的 AI 商机，是 2 月写进去的；7 月包里的商业智能体商机同理。换挡 = 加权迁移，永不删老条目。

## 附录 C IPC 命令速查

见 §2.4 表；完整错误码见附录 D；前端唯一出口 `apps/web/src/bridge/cmd.ts`。

## 附录 D 错误码表（仅内部，禁止展示给用户）

| code | 含义 | recoverable | 用户可见 |
|---|---|---|---|
| `E_CORE_DOWN` | sidecar 两次启动失败 | true | 否（仅浏览已存点子） |
| `E_STATE_CORRUPT` | `state.json` 损坏 | true | 否（静默重建） |
| `E_LIBRARY_FALLBACK` | 工作库损坏，已回退 | true | 否 |
| `E_ENGINE_NO_MATCH` | 硬过滤后 0 条（已走降级） | true | 否（1–2 条 + 温和 note） |
| `E_FS_READONLY` | 导出目录不可写 | true | **是**：`Choose another folder` |
| `E_PDF_RENDER` | PDF 渲染异常 | true | 仅一次「重试」，无红色框 |
| `E_LICENSE_SEAT_FULL` | 第 4 台设备 | true | **是**：`Release a seat` 引导 |
| `E_LICENSE_BAD_CODE` | 码格式/验签失败 | true | **是**：输入框下一行温和提示 |
| `E_DELTA_INVALID` | delta 校验失败 | true | 否（回滚） |
| `E_MANIFEST_FAIL` | manifest 拉取/解析失败 | true | 否（静默跳过） |
| `E_UNKNOWN_CMD` | 未知 cmd | true | 否 |
| `E_INTERNAL` | sidecar 内部异常（已捕获，进程不崩） | true | 否（静默记录） |
| `E_IDEA_NOT_FOUND` | 请求的 id 不在当前库 | true | 否（前端回退列表） |
| `E_EXPORT_CANCELLED` | 用户取消另存为对话框 | true | 否（无提示，符合预期） |
| `E_CSV_WRITE` | CSV 写盘失败（磁盘满等） | true | **是**：`Choose another folder` |
| `E_PDF_WRITE` | PDF 写盘失败（磁盘满等） | true | **是**：`Choose another folder` |
| `E_LIBRARY_WRITE` | 工作库写盘失败（已回滚） | true | 否（下次操作重试） |

> D-09 契约修订（PM，2026-11-13）：以上 6 码为运行期实际在用码，正式收编；目录不可写（权限类）统一归 `E_FS_READONLY`，`E_PDF_WRITE`/`E_CSV_WRITE` 仅指磁盘满等其他写失败。

---

> **总纲（贴在每个工位上）**：界面做小，后台做厚；用户那头越轻，你这头越值钱。卖的不是功能，是「我替你想完了」。
> **文档基线**：V1.0 定边界，V2.0 定执行；UI 以 `en/html/` 为准；契约以 §3 §7 为准；验收以 §9 为准。


