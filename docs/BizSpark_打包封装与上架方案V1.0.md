# BizSpark 打包封装与上架方案 V1.0

> 配套：《BizSpark_开发执行版需求文档V2.0.md》§2 架构 / §10 上架章节的**展开版**
> 定位：**开发前就要冻结的约束**，不是开发完再补的一道工序
> 日期：2026-11-12 ｜ 主体：上海浦东 OPC 公司 ｜ 负责人：程序员 A（主）、H（验收）、G（合规）

---

## §0 先把这件事说透：封装为什么要前置

你说得对，而且这正好是前面聊技术方案时最容易被漏掉的一层：

> **开发前**要问「用什么技术做，用户体验最好」；**开发完成后**才动手封装。
> 但**封装的规则会倒过来规定开发怎么写**——所以封装方案必须在 W1 就定死，不能等做完再想。

举个马上会踩的例子：如果 E 在导出 PDF 时图省事，用 Python 直接 `open("~/Documents/BizSpark/plan.pdf","w")`，Windows 版一切正常；等 W5 打 Mac App Store 包，**沙盒会直接拦掉**——App Store 版不许往指定容器之外写文件，必须走系统「另存为」对话框由用户授权。这时候再回头改导出模块，等于 F05/F06 重写一遍。

再举一个：如果月度更新包里除了 JSON 数据还夹带一段"让客户端执行的新逻辑"，Mac App Store 会按 **2.5.2 / DPLA §3.3.1(B)**「不得下载、安装或执行引入或改变功能的代码」直接拒审。[citation:15]

所以这份文档干的事就一件：**把三条上架产线的封装要求，反写成开发期必须遵守的约束，并从 W1 起每周真的打出一个能装的包。**

> 「桌面工具上架 Apple」这里指 **Mac App Store**（macOS 桌面应用），不是 iOS App Store。iPhone/iPad 端按 V2.0 已定，放第二版，本期不涉及。

---

## §1 三条产线总览（一次代码，六个构建目标）

| 项 | ① Microsoft Store | ② Mac App Store | ③ 海外分销平台（Gumroad / Lemon Squeezy 等） |
|---|---|---|---|
| 用户动作 | 商店付费下载 → 自动安装 → 打开即用（**金额由商店后台设置，不进客户端**） | 同左 | 平台付款 → 收下载链接 + 激活码 → 自己装 |
| **产物** | `MSIX`（Win32 桌面应用） | 签名 `.app` → 提交 `.pkg` | Win `.exe` / Mac `.dmg` |
| 签名 | **微软免费代签**（提交未签包即可）[citation:1] | `Mac App Distribution` + `Mac Installer Distribution` 证书 + App Store profile | Win：CA 证书（可选）；Mac：`Developer ID Application` |
| 沙盒 | 声明 `runFullTrust`，按用户权限运行 | **强制 App Sandbox** | 无沙盒 |
| 公证 | 不适用 | **不需要**（提交审核已含等效检查）[citation:17] | Mac **必须**：`notarytool` + `staple`[citation:6][citation:14] |
| 收款 | Microsoft Store 商业平台 | App Store（StoreKit / 付费下载） | 分销平台 |
| **授权码** | **不写**（付费下载在安装前已完成购买验证） | **不写** | **写**，一码 3 台设备（F10） |
| 更新 | 商店每 24h 自动检查[citation:1] | 商店 | 自有轻量 updater（F12），HTTPS + 签名校验 |
| 托管 | 微软免费 | Apple | 自己/分销平台 |
| 抽成 | 按平台规则 | 按平台规则 | 按平台规则（通常更自由） |

**三条产线的证书族与产物严禁混用**：Mac App Store 签名的包不能挂到自己网站或分销平台卖；Developer ID 签名的包也不能提交商店。[citation:17] 所以是**三套签名路径、三套产物、清晰命名**，共用同一份业务代码。

**六个构建目标（A 在 `scripts/` 落地）**

| # | 命令 | 产物 | 去向 | 编译期裁掉 |
|---|---|---|---|---|
| 1 | `build:store-win-en` | `BizSpark-1.0.0.0-x64.msix` | Microsoft Store | `license` + `updater` |
| 2 | `build:store-mac-en` | `BizSpark-1.0.0.pkg` | Mac App Store | `license` + `updater` |
| 3 | `build:reseller-win-en` | `BizSpark-Setup-1.0.0.exe` | 分销平台 | 无（启用激活码） |
| 4 | `build:reseller-mac-en` | `BizSpark-1.0.0.dmg` | 分销平台 | 无（启用激活码） |
| 5 | `build:selfcheck-cn-win` | `BizSpark-SelfCheck-CN-1.0.0.exe` | **仅内部** | 无 |
| 6 | `build:selfcheck-cn-mac` | `BizSpark-SelfCheck-CN-1.0.0.dmg` | **仅内部** | 无 |

> 中文自检包**不签名上架、不进商店素材、不对外分发**，只是你自己看自己练那一版（V2.0 §4 F14.3）。

---

## §2 最关键的一个选型：Python 究竟怎么进包

V2.0 定的是「Python 3.11 写核心引擎，作为 Tauri sidecar 随包」。这一步在 Windows 没问题，在 **Mac App Store 沙盒里是唯一的真风险点**，必须现在就定，不能等 W5。

### 2.1 三条路对比

| 方案 | 做法 | Windows MSIX | Mac App Store | 结论 |
|---|---|---|---|---|
| PyInstaller `--onefile` | 打成单文件，运行时解压到临时目录再起解释器 | ✅ 能跑 | ❌ **高风险**：沙盒下临时解压生成未签名代码、解释器随包，且启动慢（4–8s）[citation:11][citation:13] | **否** |
| PyInstaller `--onedir` | 主 exe + 一堆 `.so`/framework 目录 | ✅ 能跑 | ⚠️ 可行但重：bundle 内**每一个 Mach-O 都要单独签名**并带 `inherit` entitlement | 备选 |
| **Nuitka 编译成原生二进制** | Python 源码编译为 C → 本地 Mach-O / exe，**不携带独立解释器** | ✅ 最干净 | ✅ **最稳**：一个签过名的原生 helper，启动 0.3–1s[citation:11][citation:13] | ✅ **推荐** |

### 2.2 推荐方案（不改语言、不改逻辑、只改编译方式）

> **Python 源码仍是唯一真源**（C/D/E/F/G 照 V2.0 写），只是构建时不用 PyInstaller，改用 **Nuitka** 把 `apps/core/` 编译成平台原生可执行文件，作为 Tauri sidecar 随包。

好处正好压在你最在意的三件事上：

- **Mac 沙盒友好**：bundle 里没有 Python.framework、没有一堆 `.so`、没有运行时解压出来的未签名代码，只有一个可以 `codesign` 的 helper。
- **2.5.2 更干净**：所有逻辑是随包固定的原生二进制，不下载、不解释、不执行任何外部代码。[citation:15]
- **用户体验更好**：冷启动快（对 F14.1 的 ≤1.5s 有帮助）、包体小、内存低——刚好对上"用户那一面越轻越好"。

Apple 官方明确支持沙盒 App 内嵌命令行工具，条件是 helper 带 `com.apple.security.app-sandbox` + `com.apple.security.inherit` 并单独签名（Embed Helper Tools + Code Sign On Copy）。[citation:7] 所以 Tauri sidecar 这条路本身是合规的，问题只在"带不带解释器"。

### 2.3 必须 W1 验证的风险（不验证不许写业务代码）

Nuitka 对纯标准库支持良好，但 **`reportlab` 含 C 扩展**，需要实编确认。[citation:11][citation:13] 因此 §6 的 S1 spike 要先跑：

- 通 → 按 2.2 执行，PDF 仍在 Python 侧本地生成，V2.0 架构一行不改。
- 不通 → **退路（不改产品、只挪一层）**：PDF 渲染从 Python 侧挪到前端/Rust 侧（本地 `pdf-lib` 之类，仍 100% 离线、无水印、单页），Python 只负责诊断与数据装配。**绝不因为打包问题去改界面或加云端。**

> 一句话：**Python 是开发语言，不是运行时依赖。** 用户电脑上不该出现"要装 Python 才能用"这回事，商店审核也不该看到"一个解释器和一堆脚本"。

---

## §3 三条产线怎么封（到命令级）

### 3.1 ① Microsoft Store：MSIX 打包 Win32 桌面应用

微软官方给 Win32 应用两条路：打包成 MSIX（商店免费托管、免费签名、自动更新），或只列 EXE/MSI（自己托管、自己买证书）。[citation:1] 你走**第一条**，最省事。

**包内布局**
```
layout/
├─ AppxManifest.xml
├─ BizSpark.exe                 # Tauri 主进程
├─ bizspark-core                # Nuitka 编译出的 sidecar（helper）
├─ resources/baseline_v1.json   # D 的 312 条内置库（只读）
├─ locales/en-US.json
└─ Assets/  StoreLogo.png / Square44x44Logo.png / …（含 targetsize 变体）
```

**`AppxManifest.xml` 关键项（A 写成模板，版本号自动生成）**

| 项 | 值 | 为什么 |
|---|---|---|
| `EntryPoint` | `Windows.FullTrustApplication` | 标记为普通 Win32 可执行，不是 UWP[citation:5] |
| `uap10:TrustLevel` | `mediumIL` | 以用户权限运行[citation:5] |
| `rescap:Capability` | **`runFullTrust`** | 桌面应用标配：要起子进程、访问用户选中的文件；不声明会启动即崩[citation:5] |
| `Capability` | `internetClient` | 仅用于每月一次 manifest GET（F09） |
| `minVersion` | `10.0.17763.0`（Win10 1809） | MSIX 稳定支持 Win32 的起点[citation:5] |
| `Publisher` | **从 Partner Center 原样复制** `CN=<GUID>` | 手敲必被拒[citation:5] |
| `Version` | 四段，第四段必须为 0，且**永不复用** | 测试上传也消耗版本号[citation:5] |

**构建与提交**
```bash
# 1. Nuitka 编 core（Windows / MSVC）→ layout/bizspark-core
# 2. Tauri build → layout/BizSpark.exe + resources/locales
makeappx pack /d layout /p BizSpark_1.0.0.0_x64.msix /o
# 3. 本地自测（未签包）
Add-AppxPackage -Path .\BizSpark_1.0.0.0_x64.msix
# 4. 提交：必须在 Windows runner 上跑，Linux 容器做不了
msstore publish ...        # 需 Azure AD 应用凭证[citation:5]
```
- 商店**免费代签**，所以提交未签名的 `.msix / .msixupload` 即可。[citation:1]
- 若 Nuitka 产物由 MSVC 编译，注意 VC++ 运行库依赖，在 manifest 声明对应 framework package，避免干净机器缺 `MSVCP140.dll`。[citation:5]
- 提交页的「受限功能说明」要写清楚一段：`runFullTrust` 仅用于在用户授权下生成本地 PDF 与启动随包的诊断组件，不访问网络之外的系统资源。[citation:10]

### 3.2 ② Mac App Store：沙盒 + helper 签名

**证书与配置**
- `Mac App Distribution` / `Mac Installer Distribution` 证书 + App Store provisioning profile（**不是 Developer ID**，两族不能混）[citation:17]
- 提交走 App Store Connect / Transporter；**MAS 分发不需要公证**，因为提交审核已含等效检查。[citation:17]
- Hardened Runtime 对 App Store 分发非强制，但建议开。[citation:7]

**主 App entitlements（`entitlements.mas.plist`）**
```xml
com.apple.security.app-sandbox                 = true
com.apple.security.network.client              = true   <!-- F09 每月一次 GET -->
com.apple.security.files.user-selected.read-write = true <!-- F06 系统另存为导出 -->
```
> 关键：**导出必须走系统「另存为」对话框**（Powerbox 用户授权），不能由 Python/Rust 自己写 `~/Documents`。这正是 §0 那个反例的解法。

**sidecar helper entitlements（`entitlements.mas.inherit.plist`）**
```xml
com.apple.security.app-sandbox = true
com.apple.security.inherit     = true   <!-- 继承主 App 沙盒权限 -->
```
签名与嵌入（Apple 官方做法）：[citation:7][citation:8]
```bash
codesign --force --options runtime \
  --entitlements entitlements.mas.inherit.plist \
  --identifier com.bizspark.desktop.core \
  --sign "3rd Party Mac Developer Application: ..." \
  bizspark-core
# 构建时把 helper 放进 Embed Helper Tools / Code Sign On Copy
```

**沙盒下的路径变化（F 必须知道）**
- `appDataDir` 会落到 `~/Library/Containers/com.bizspark.desktop/Data/...`，不是 `~/Library/Application Support/`。所有路径必须经 Tauri API 取，禁止拼字符串。
- 用户导出的 PDF 在用户自己选的目录（Documents 等），**不在容器里**——所以卸载 App 不会删掉用户那张纸（T-49 要验）。

### 3.3 ③ 海外分销：Developer ID + 公证 + staple

**Windows**：出 `.exe` 安装包（或便携版），CA 证书签名可降 SmartScreen 误报；平台负责收款与发激活码。

**macOS 四步流水线，一步都不能跳**（跳了 Gatekeeper 直接拦）：[citation:6][citation:14]
```bash
# 1 签名（Developer ID + Hardened Runtime + 安全时间戳）
codesign --force --options runtime --timestamp \
  --sign "Developer ID Application: ..." BizSpark.app

# 2 打包 dmg
# 3 公证 —— 2026 年只能用 notarytool（altool 已于 2023-11-01 停用）
xcrun notarytool submit BizSpark-1.0.0.dmg --wait ...
# 4 staple（把票据嵌进去，离线首次启动也能验）
xcrun stapler staple BizSpark-1.0.0.dmg
```
- 公证是自动恶意代码扫描，**不是 App Review**。[citation:17]
- 分销版才启用 G 的激活码（一码 3 台），Store 版编译期裁掉 `license` 模块。
- 自有 updater（F12）必须 HTTPS + 校验下载包签名，且与 F09 的库更新完全分离。

---

## §4 钱怎么收、授权怎么算

**Store 付费下载不需要应用内授权码。** 用户在商店完成购买，商店在安装前已经验证过；「能装到这台机器上」本身就是凭证。[citation:1] 所以：

- Microsoft Store / Mac App Store 版：**一行授权代码都不写**，打开即完整版（与 V2.0 §4 F10 一致）。
- 这跟你前面「借平台信任」的判断是同一件事：淘宝买家敢输密码是因为支付宝兜底，你的用户敢付款是因为商店兜底。
- 分销版才需要激活码——因为**安装包文件能被复制转发**，码只证明"这份副本付过钱"，不是不信任用户。

**中国 OPC 主体的收款材料（H 从 W1 开始备，别等 W6）**

| 平台 | 要办的 |
|---|---|
| Microsoft Partner Center | 注册（一次性费用）、**W-8BEN 税表**（证明中国税务居民、非美国纳税主体）、Payout profile、收款银行账户的 **CNAPS 12 位联行号**、收益类型选 `sell`（付费应用）[citation:10] |
| Apple Developer Program | 年费（按 Apple 当期标准）、Agreements / Tax / Banking、App Store Connect 里的付费 App 协议 |
| 两边都要 | 隐私政策 URL（**即使完全不收集数据也必须填**）[citation:10]、支持邮箱、App Privacy 问卷填「不收集」、商品页 5 条文案（V2.0 §10） |
| 公司财务 | 跨境软件收入单独建账，按「软件出口 / 跨境服务」口径处理增值税 |

**关于"不给自己挖坑"，这里主动说清**：Apple 开发者年费是**唯一躲不掉的按年支出**，但它**只影响你发新版本 / 保持上架**，绝不影响已经买了的用户——他电脑上那个 `.app` 照常打开、照常离线用、照常导出 PDF。这跟你当初否决「核心逻辑放云端」的理由完全一致：**别让任何一笔续费变成用户软件变砖的前提**。

---

## §4.5 价格不进包：分成销售的定价口径

**第一版只讲功能，包里不带价格。** Microsoft Store / Mac App Store 是付费下载分成销售，**售价在 Partner Center / App Store Connect 后台设置**，随行就市、改价即时生效、**不需要重新打包、不需要发版**。所以三条产线的安装包里**根本不需要有价格这个数据**。

| 层 | 位置 | 首版状态 |
|---|---|---|
| 商店售价 | Partner Center / App Store Connect 后台 | 可随时设置，**不进客户端** |
| 工程客户端 | `config/pricing.json` | `display_mode=hidden`、`amount=null` |
| 静态 HTML | `assets/pricing.js` | 同上，改一处 18 页全生效 |

```json
{ "display_mode": "hidden", "amount": null, "currency": "USD", "model": "one-time", "billing_note": null }
```

- **零硬编码**：md / docx / HTML / CSS / JS / 截图 / 商品文案不得出现任何商品售价数字；价格只能由配置渲染（CI 门禁 T-59）。
- **首版 hidden**：价格槽渲染纯功能 / 模式文案（`One-time purchase · Yours forever`），不显示数字、不显示空价格框、不新增控件。
- **后期显示只改配置**：做授权码 / 包月 / 包年 / 订阅时改 `display_mode=visible` + 填 `amount`、`model`，一处改动全端生效；**仍不加改价界面**。
- **边界**：商机库里的起步成本 / 定价建议是内容数据，不是商品售价，保留。
- **商品页文案**（G 审）：首版只写 `One-time purchase` / `No subscription` / `No auto-renewal` / `Works offline` / `Your data stays on this device`，**不写金额**。
- **对封装的影响**：`config/pricing.json` 与 `assets/pricing.js` 随六个构建目标一起注入，**同一份配置**；Store 构建默认 `hidden`，分销 / 订阅构建按发布需要切换，切换的是配置不是代码。P-11 的每周出包流水线把 T-59 金额门禁一起跑。

---

## §5 封装反向约束清单（开发期 14 条，全员遵守）

> 这一节是全文重点：**封装不是 W5 的工序，是 W1 就贴在工位上的编码规矩。** 违反任何一条，后期都要返工。

| # | 约束 | 谁最相关 | 为什么 |
|---|---|---|---|
| P-01 | 所有路径经 Tauri `appDataDir` / 系统对话框取，**禁止硬编码绝对路径或 `~` 拼接** | F / E | MAS 容器路径不同 |
| P-02 | **导出必须经系统「另存为」**，由用户授权目标目录 | A / E | 沙盒 Powerbox；否则 MAS 版写不出去 |
| P-03 | **月度 delta 只能是纯数据 JSON/CSV**，绝不夹带任何脚本、插件、可执行代码、可 eval 的逻辑 | D / F | 2.5.2 / DPLA §3.3.1(B) 拒审红线[citation:15] |
| P-04 | 不加载外部解释器、不 `eval` 用户内容、不执行随包之外的代码 | C / A | 同上；Nuitka 方案天然满足 |
| P-05 | sidecar **不监听端口、不起后台常驻服务**、不开本地 HTTP | A / C | 审核与沙盒；V2.0 已定 JSONL stdio |
| P-06 | bundle 内每个 Mach-O / exe **都能被单独签名**；不用运行时解压生成代码的打包方式 | A | Apple helper 签名要求[citation:7] |
| P-07 | 出网只用 **HTTPS GET 静态文件**；声明 `network.client` / `internetClient`；失败静默 | A / F | 最小权限 + F09 降级 |
| P-08 | **Store 构建编译期裁掉 `license` + `updater` 模块** | A / G | Store 版不写授权码 |
| P-09 | 所有依赖随包（含图标、字体、baseline 库），**不联网装依赖、不运行时下载二进制** | 全员 | 2.5.2「self-contained in their bundles」[citation:15] |
| P-10 | 隐私：零收集；隐私政策 URL、App Privacy「不收集」、支持邮箱 **W1 备齐** | H / G | 商店审核必查[citation:10] |
| P-11 | **构建脚本 W1 就存在，每周出一个可安装包**（不是 W5 才第一次打包） | A | 把封装风险摊到 6 周里，别攒到最后炸 |
| P-12 | 图标全尺寸变体、四段版本号（末段 0、不复用）、`runFullTrust` 受限功能说明，W1 备齐 | A / H | MSIX 校验与提审[citation:5][citation:10] |
| P-13 | **卸载 App 不得删除用户导出的 PDF**（用户数据在 Documents，不在包容器） | A / E / F | 买断工具的基本体面 |
| **P-14** | **价格不进包**：六个构建目标共用同一份 `config/pricing.json` / `assets/pricing.js`，首版 `hidden`+`amount=null`；CI 跑金额门禁（§4.5 / T-59） | A / B / H | 价格随行就市，改配置不改代码 |

> 加一条口径：三条产线的**证书族、产物名、分发渠道严禁交叉**。Store 签名的包不上分销平台，Developer ID 包不提交商店。[citation:17]

---

## §6 W1 三个 Spike（不过不许写业务代码）

A 主持，各半天，H 记录结论进 `qa/spike-report.md`。**这三个是"封装前置"的真正落地动作。**

| 号 | 验证什么 | 通过标准 | 不通过怎么办 |
|---|---|---|---|
| **S1** | Nuitka 把 `apps/core/`（含 `reportlab`）编成 Windows exe + macOS Mach-O，跑通 `diagnose` 与单页 PDF | 双平台原生二进制、无独立解释器、冷启 <1s、PDF 1 页 | 走 §2.3 退路：PDF 渲染挪到前端/Rust 侧，Python 只做诊断 |
| **S2** | 最小 Tauri demo 在 **MAS 沙盒**下：启动带 `inherit` entitlement 的 helper + 经系统另存为导出一个文件到 Documents | helper 签名校验通过、沙盒内不越界写、导出成功 | 调整 entitlements / 改走系统对话框；此路不通则 Mac Store 顺延，先上 Windows Store |
| **S3** | MSIX 打包 + `Add-AppxPackage` 本地安装 → 跑通「首屏 → 5 题 → 3 条 → PDF」 | `runFullTrust` 生效、sidecar 能起、卸载后用户 PDF 仍在 | 修 manifest / VC++ 依赖声明 |

> S2 是最容易被跳过、也最值钱的一个。它用半天替你排除掉「W5 才发现 Mac 版要重写导出模块」这种最贵的返工。

---

## §7 构建矩阵与 CI（A 交付）

```
scripts/
├─ build-core.sh        # Nuitka 编 sidecar（按平台）
├─ build-web.sh         # Vue3 → 静态资源（en / cn 由 locales 决定）
├─ build:store-win      # MSIX 布局 + makeappx
├─ build:store-mac      # MAS 签名 + entitlements + pkg
├─ build:reseller-win   # exe
├─ build:reseller-mac   # Developer ID → notarytool → staple → dmg
├─ build:selfcheck-cn   # 两个内部包
└─ pack.sh / sign.sh / publish.sh
```

**feature flag**：`store` / `reseller` / `selfcheck-cn`。`store` 编译时裁掉 `apps/core/license/` 与 `updater.rs`；`selfcheck-cn` 只换 `zh-CN.json` + `build-mode.txt`，**不加语言切换按钮**。

**CI 每个 PR 必跑**：V-01…V-12（库校验）、V-10（中英文案键一致）、T-49…T-58（封装用例）、包体阈值（≤80MB）。**每周五出一个可安装包**（P-11），H 装一次跑主链路。

---

## §8 补充验收用例 T-49…T-58（并入 V2.0 §9）

| 编号 | 前置 | 步骤 | 预期 | 负责 | 级 |
|---|---|---|---|---|---|
| T-49 | MSIX 本地安装 | 安装→导出 PDF 到 Documents→卸载→看文件 | `runFullTrust` 生效；**卸载后 PDF 仍在** | A/E | P0 |
| T-50 | MAS 沙盒版 | 查 `appDataDir` 实际落点 + 尝试写容器外 | 落在 `~/Library/Containers/...`；容器外写入被拦且不弹错 | A/F | P0 |
| T-51 | MAS 沙盒版 | 点导出 | 弹系统另存为，选完目录后 PDF 成功写出 | A/E | P0 |
| T-52 | MAS 包 | `codesign -dv` 检查主 App 与 helper | helper 带 `app-sandbox` + `inherit`，签名有效 | A/G | P0 |
| T-53 | 全包扫描 | 检索「下载代码 / eval / 外部脚本加载 / delta 内可执行内容」 | 零命中；delta 仅 JSON/CSV 数据 | D/H | P0 |
| T-54 | 分销 Mac .dmg | 全新机器首次双击 | Gatekeeper 无「已损坏/未知开发者」；notary 票据已 staple | A/H | P0 |
| T-55 | Store 两个包 | 检索包内 `activate` / `license` / `updater` | 零命中（编译期已裁） | A/G | P0 |
| T-56 | 三产线产物 | 核证书族与文件名 | MAS 包不在分销目录、Developer ID 包不提交商店，命名清晰 | A/H | P0 |
| T-57 | 断网安装 | 装完拔网跑完整主链路 | 全功能可用、零出网 | H | P0 |
| T-58 | 提审材料 | 逐项核对 | 图标变体 / 四段版本号 / 隐私政策 URL / 受限功能说明 / 5 条商品页文案齐备 | H/G | P0 |

---

## §9 上架材料与节奏（H 备料，A 提包）

| 周 | 封装相关动作 |
|---|---|
| **W1** | 注册 Partner Center / Apple Developer；备 W-8BEN、CNAPS、隐私政策 URL、图标全尺寸；**跑完 S1/S2/S3**；`scripts/` 落地并出第一个可装包（哪怕功能只有骨架） |
| **W2** | 每周五出包；MSIX 与 MAS 两条流水线上 CI |
| **W3** | 真库 312 条进包；包体首次测量；entitlements 定稿 |
| **W4** | 功能冻结；T-49…T-58 首轮全跑；分销版公证流水线打通 |
| **W5** | RC1：六个构建目标全部出包；商店素材（**只用英文版截图**）定稿；提审预检 |
| **W6** | 先 Microsoft Store + Mac App Store 上架；分销平台随后（此时才启用激活码池）；灰度观察 |

**上架顺序理由**：先两个商店，验证「付费下载 → 打开即用」这个最干净的闭环；分销平台随后，因为它多一层激活码与自有更新，等主链路被真实付费用户验过再开，风险最小。

---

## §10 一个需要你拍板的小决策（不擅自改架构）

**问题**：MSIX / MAS 卸载 App 时，会清掉**包容器内**的 AppData（也就是 `state.json`、合并后的工作库、「我的点子」存档）。V2.0 里写的是「重装系统后存档丢失属预期」——但**卸载重装比重装系统常见得多**。

| 选项 | 做法 | 好处 | 代价 |
|---|---|---|---|
| A（维持 V2.0） | 存档只放 `appDataDir` | 最简单、沙盒天然允许 | 卸载/重装后「我的点子」清空 |
| **B（推荐）** | 把 `state.json` 也放 `$DOCUMENTS/BizSpark/.bizspark/`（用户导出目录旁的隐藏文件） | 卸载、重装、换版本都不丢；更贴合「买断工具一直那样」 | MAS 版需要用户先授权过该目录（首次导出时顺带授权一次）；F 的路径层要小改 |

导出 PDF 本来就在 Documents，不受影响；差别只在"我的点子"这类轻量存档。**建议 B，但这属于产品体感决策，等你点头再让 A/F 改**，我这轮不擅自动 V2.0 的 §2.5 路径表。

---

## §11 一句话收口

> **开发前选技术，看的是用户体验；封装规则倒过来规定技术怎么写。**
> Python 仍是你写引擎的语言，但**不是用户电脑上的运行时**（Nuitka 编成原生 helper）；三条产线共用一份代码、六份产物、三套签名；付费下载由商店兜底所以 Store 版不写授权码；所有路径、导出、更新包形态，从 W1 第一行代码起就按沙盒和审核规则写。

这样等 W6 功能全部做完，封装不是"再想办法装进商店"，而是**每周都在跑、已经跑了五周的流水线最后一次出包**。

---

**引用**：微软 Win32 分发与 MSIX 商业平台[citation:1] · MSIX `runFullTrust` / manifest / 版本号[citation:5] · Mac App Store 与 Developer ID 两条签名路径、MAS 免公证[citation:17] · Apple 沙盒内嵌 helper 的 entitlements 与签名[citation:7][citation:8] · 公证须用 `notarytool` + staple[citation:6][citation:14] · 2.5.2 / DPLA §3.3.1(B) 自包含与不得下载执行代码[citation:15] · Nuitka 与 PyInstaller 差异[citation:11][citation:13] · 中国开发者收款与税务材料[citation:10]
