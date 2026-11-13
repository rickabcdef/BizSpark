# 生意快启·海外买断版（BizSpark）
# 详细需求规格书 V2.0 · 开发实现级

| 项 | 内容 |
|---|---|
| 文档编号 | BZS-SPEC-V2.0 |
| 日期 | 2026-11-12 |
| 状态 | 定稿待开发 |
| 与前版关系 | 本文是 V1.0《产品需求文档》的**实现级细化**，不推翻任何既定商业约束；商业约束冲突时以 V1.0 §1 为准，实现细节冲突时以本文为准 |
| 主体 | 上海浦东 OPC 公司（一人有限责任公司） |
| 产品对外名 | **BizSpark**（英文，唯一对外版本） |
| 内部名 | 生意快启·海外买断版 |
| 形态 | Windows / macOS 桌面工具，**真实安装包**，不是网页快捷方式 |
| 定价 | **可配置，不写死**；首版一次性买断、由商店分成销售，客户端 / 文档 / UI / HTML / 商品文案均不展示金额（详见「价格配置契约」） |
| 首发货架 | Microsoft Store、Mac App Store 优先；其后 Gumroad / Lemon Squeezy 等海外软件分销平台 |
| 首发市场 | 英语区 6 国：US / CA / UK / AU / SG / PH |
| 界面语言 | 英文 = 唯一对外售卖版；中文 = 内部自检镜像版（仅文案替换，不上架、不对外分发） |
| 配套基线 | `en/html/` 9 页高保真 HTML + `en/ui/` 9 张截图；`cn/html/`、`cn/ui/` 为中文镜像；CSS 两版为同一份文件 |
| 验收依据 | 本文 §19 测试用例 + `en/html/` 逐页比对 |

---

## 目录

- 0. 怎么读这份文档 / 术语 / 主次口径
- 1. 产品定义、商业约束与红线
- 2. 全局规范（视觉、组件、文案、禁止词）
- 3. 用户、场景与两条链路
- 4. 系统架构、运行边界与文件清单
- 5. 用户操作逐步规格（S01–S32）
- 6. 页面逐页规格（P01–P09，元素级）
- 7. 功能规格（F01–F14，流程级）
- 8. 数据字典（字段级）
- 9. 匹配引擎算法规格（伪代码级）
- 10. 商机库内容规格（312 条、填充规范、月度换挡）
- 11. 存储、文件与命名规格
- 12. 导出规格（PDF / CSV 版式级）
- 13. 更新机制规格（时序、合并、失败矩阵、回滚）
- 14. 授权激活规格（码、指纹、凭证、席位）
- 15. 设置规格（6 项逐项）
- 16. 异常与降级总表
- 17. 非功能需求
- 18. 双版本纪律
- 19. 验收测试用例（TC-001 – TC-052）
- 20. 上架与渠道材料清单
- 21. 排期、人日估算与交付物
- 22. 待决事项与变更记录

---

# 0. 怎么读这份文档 / 术语 / 主次口径

## 0.1 阅读对象

| 角色 | 重点章节 |
|---|---|
| 你（产品负责人 / 唯一决策人） | §1、§3、§5、§6、§10、§18 |
| 开发 | 全文，重点 §5–§9、§11–§16、§19 |
| 内容编辑（你自己每月填库） | §8、§10 |
| 商店上架 / 素材 | §6、§20 |

## 0.2 术语表

| 术语 | 定义 |
|---|---|
| **基线库 / baseline** | 随安装包冻结、内置在客户端的 312 条商机数据文件 `baseline_v1.json`。断网也完整可用 |
| **商机 / idea** | 库里的一条结构化生意点子，含成本、7 步、定价、渠道、坑、合规等字段 |
| **诊断 / quiz** | 5 道选择题，用户答案仅在本地内存与本地缓存中使用 |
| **匹配引擎** | 打包在客户端内的纯规则打分逻辑，不是 API、不是云端服务 |
| **Top 3** | 引擎输出的最终 3 条结果，**永远只给 3 条**（不足时给 1–2 条） |
| **一页纸 / one-pager** | 导出的单页 PDF，是用户买断后拿到的核心交付物 |
| **delta 包** | 每月 1 号发布的极小 JSON 差量文件，只做 add / revise / retire |
| **静态托管** | 存放 `manifest.json` + `delta_*.json` 的对象存储/静态站点，无常驻进程、无数据库 |
| **激活码** | 仅分销版需要的字符串凭证，一码最多 3 台设备；**不是账号、不是登录** |
| **设备指纹** | 硬件 ID + 系统信息的本地哈希，用于计数席位，禁止用 IP |
| **Store 版** | Microsoft Store / Mac App Store 付费下载的版本，由平台验证购买，客户端零授权代码 |
| **分销版** | Gumroad / Lemon Squeezy 等平台售出 `.exe/.dmg` 的版本，需要轻量激活 |
| **静默跳过** | 更新/联网失败时不弹窗、不提示、不阻塞、不降级功能，用户完全无感 |
| **英文版 / 中文版** | 英文版 = 产品本身；中文版 = 自己的自检镜像。见 §18 |

## 0.3 主次口径（一句话）

> **产品只有一个，是英文版。中文版只是把英文版界面上的字换成中文，给自己看、自己用、自己练熟。**
> 任何改动先改英文版，再逐字镜像到中文版。出现分歧，以英文版为准。

## 0.4 贯穿全文的六条铁律

1. **用户端只留「小」**：答 5 题 → 出 3 条 → 存一张纸。界面上不出现"商机库""权重""版本""引擎""浪潮""算法""匹配度模型"等后台词汇（结果页的 `94% MATCH` 与一句 Why this fits you 属用户语言，允许）。
2. **复杂全部沉到看不见的一面**：312 条库、打分、差量合并、授权，做厚做全，但不占用户一秒钟注意力。
3. **核心逻辑在客户端本地**。服务器挂了、忘续费了、断网了，用户无感，功能完整。
4. **不给自己挖坑**：不接支付接口、不做账号体系、不做订阅、不依赖任何按年续费的运行时服务。
5. **好看是第一位**，且**风格已定稿不再改**：`en/html/assets/style.css` 为唯一视觉基线，开发实现逐页比对。
6. **一屏一动作**：每页只有一个强 CTA，不并列两个同等强的按钮，不弹解释、不弹教程、不弹报错。

> 文档写得厚，是给开发和你自己看的"阴面"；用户看到的那一面必须始终薄。

---

# 1. 产品定义、商业约束与红线

## 1.1 一句话产品定义

> 用户买下一个桌面图标。双击 → 答 5 道题 → 看到 3 个他用现有钱、时间、本事真能开起来的生意 → 导出一张明天能打印照着做的一页纸。全程不登录、不联网也能用、不追问、不需要学。

## 1.2 商业约束表（写死，开发不得自行突破）

| 编号 | 约束 | 具体含义 | 违反后果 |
|---|---|---|---|
| C01 | 只做海外 | 不在国内销售、不接国内支付、不做中文售卖页/落地页、不办国内经营性互联网资质 | 破坏出海口径 |
| C02 | 买断制 | 一次付费（金额由商店后台设置），永久可用；无到期、无续费提醒、无自动扣款 | 用户信任崩塌 |
| C03 | 支付归平台 | 软件内**零支付代码**，不接 Stripe / PayPal / 内购 SDK / 订单 / 退款后台 | 白做、增加合规面 |
| C04 | 无账号 | 不注册、不登录、不绑定邮箱、不云同步、不找回密码、不"欢迎回来" | 用户端变复杂 |
| C05 | 联网可用但非必需 | 联网**仅**用于：① 每月 1 号商机库差量更新 ② 分销版首次激活校验。核心诊断与导出 100% 离线 | 触碰"忘续费变砖" |
| C06 | 零后端依赖 | 静态托管几个 JSON 文件即可，**无 FastAPI 常驻服务、无数据库、无大模型 API 账单、无按年续费的运行时** | 给自己挖坑 |
| C07 | 真实桌面工具 | 交付 `.msix/.exe`（Windows）与签名 `.app/.dmg`（Mac），不是网页、不是 WebView 空壳 | 商店 4.2 拒审 |
| C08 | 渠道差异化授权 | Store 版**不做任何授权码**；分销版做轻量激活码（限 3 台设备） | 多写 1–2 天无用代码 |
| C09 | 第一版不做移动端 | Windows + macOS 双端打透后再评估 iOS / Android | 摊薄验证速度 |
| C10 | 第一版不深化 AI | 不联网调大模型；"用户填自己 API Key"属第二版可选增强 | 引入不可控账单 |

## 1.3 本期红线清单（明确不做）

```
❌ 登录 / 注册 / 账号 / 邮箱 / 云同步 / 找回密码
❌ 支付接口 / 订单状态机 / 退款后台 / 对账
❌ 订阅 / 会员 / 到期 / 续费提醒 / 连续包月包年
❌ 联网调用大模型 / 云端诊断 / 云端生成 PDF
❌ 用户上传点子 / 社区 / 评论 / 评分 / 分享
❌ 消息推送 / 每日签到 / 积分 / 成就 / 广告位
❌ 全量 200 国本地化 / 多语言切换按钮（软件内一个按钮都不许多）
❌ 手机端 / 小程序 / PWA 上架
❌ 筛选器 / 排序下拉 / 分页 / "查看更多" / 升级解锁更多
❌ 任何红色错误弹窗 / "请检查网络后重试" / 用户需要理解的报错码
```

## 1.4 商店商品页必须出现的否定式文案

`One-time purchase` · `No subscription` · `No auto-renewal` · `Works offline` · `Your data stays on this device` · `No account required`

> 允许出现 "No subscription" 这类**否定式**字样；禁止出现任何肯定式的订阅/登录/云服务描述。

---

# 2. 全局规范

## 2.1 视觉 token（唯一来源 `en/html/assets/style.css` 的 `:root`）

| Token | 值 | 用途 |
|---|---|---|
| `--bg` | `#F7F5F0` | 全站暖白背景 |
| `--surface` | `#FFFFFF` | 卡片 |
| `--surface-2` | `#FBF9F5` | 次级底、选项底 |
| `--ink` | `#101820` | 主文字 |
| `--ink-2` | `#5B6672` | 次要文字 |
| `--ink-3` | `#98A2AD` | 弱化文字、标签 |
| `--line` | `#E8E4DC` | 描边、分隔线 |
| `--deep` | `#0E2438` | 侧栏、欢迎页、深色强调块 |
| `--deep-2` | `#15344E` | 第二张结果卡顶条 |
| `--accent` | `#F2653A` | **主 CTA 专用橘** |
| `--accent-2` | `#E4542A` | 主 CTA hover |
| `--accent-soft` | `#FDEDE6` | 选中态、浅强调块 |
| `--green` | `#1F8A70` | 成功、已完成、匹配度 |
| `--green-soft` | `#E6F4EF` | 成功底、notice |
| `--gold` | `#E8B44A` | Why 引句左边条、eyebrow |
| `--r-lg / --r-md / --r-sm` | `22px / 14px / 10px` | 卡片 / 按钮 / 小控件 |
| `--sh / --sh-sm` | `0 12px 34px rgba(16,24,32,.07)` / `0 3px 12px rgba(16,24,32,.05)` | 阴影 |
| `--font` | `Inter, 'WenQuanYi Micro Hei', -apple-system, ...` | 拉丁优先，中文系统 CJK 回退 |

**用色纪律**：整站只有一颗橘色主按钮。橘色不得用于图标底色铺满、不得用于整块背景、不得用于第二按钮。绿色只表示"已完成/成功"，金色只做点缀。

## 2.2 字体与排版

| 项 | 值 |
|---|---|
| 字体族 | Inter（拉丁）；中文版由系统 CJK 字体回退，**不引入中式字体** |
| 基准字号 | `15px / line-height 1.55` |
| H1（内容页） | `34px / 1.18 / -1.1px / weight 750` |
| H1（欢迎页） | `66px / 1.06 / -3px / weight 760` |
| H2 | `21px / -0.5px / 700` |
| H3 | `15.5px / -0.2px / 700` |
| eyebrow | `10.5px / letter-spacing 2px / uppercase / 700` |
| tiny | `11.5px / --ink-3` |
| 数字统计 `.sv` | `24px / 750 / -0.8px` |
| 抗锯齿 | `-webkit-font-smoothing: antialiased` |

## 2.3 页面壳体（P02–P09 统一）

```
┌────────────── 1440×900 基准视口 ──────────────┐
│ .side 246px 固定   │ .topbar 高 70px            │
│ 深墨蓝 #0E2438     │ 半透明白 + blur(10px)      │
│ padding 30/22/22   │ 左：面包屑  右：状态 chip + avatar │
│ ├ brand (32px 方标)│────────────────────────────│
│ ├ nav-label        │ .content                   │
│ ├ nav 9 项         │ padding 40px 48px 56px    │
│ └ side-foot        │ max-width 1180px 居中      │
│    (另含径向橘光晕) │                            │
└────────────────────┴────────────────────────────┘
```

- 最小支持视口 `1100×720`；小于此值内容区允许纵向滚动，**侧栏与顶栏尺寸不变**。
- P01 欢迎页是**唯一变体**：无侧栏、无顶栏，`.hero` 深色整屏 `min-height:100vh`，含点阵背景、两个 orb、右侧倾斜结果卡 mock。
- 侧栏 `.side-foot` 常驻两行：`One-time purchase · No subscription` / `v1.0.0 · Library 2026.11 · Offline ready`。
- 顶栏常驻 chip：`All yours, on this device`（带绿点）。

## 2.4 组件库（实现必须复用，不许自造）

| 组件 | class | 规格 |
|---|---|---|
| 主按钮 | `.btn.btn-primary` | 高 44px / padding 0 20px / 圆角 12 / 字号 13.5 / 650 / 橘 / 阴影 `0 8px 20px rgba(242,101,58,.25)` / hover 上移 1px |
| 大主按钮 | `.btn.btn-primary.btn-lg` | 高 54px / padding 0 28px / 圆角 14 / 字号 15（**仅 P01**） |
| 次按钮 | `.btn.btn-ghost` | 白底 + 1px `--line` / hover 边框 `#D5CFC3` |
| 文字按钮 | `.btn.btn-quiet` | 高 38px / 无边框 / hover 浅灰底，**永远弱于主按钮** |
| 卡片 | `.card` | 白底 / 1px `--line` / 圆角 22 / `--sh-sm` |
| 卡片内边距 | `.pad` | 26px |
| 进度条 | `.stepper` | 5 点，25px 圆点；done 绿、on 橘 + 5px 柔光圈、todo 灰描边；连接线 44×1.5px |
| 选项卡 | `.opt` | padding 15/17 / 1.5px 边框 / 圆角 14 / 底 `--surface-2`；`.sel` 橘边 + 橘底；左侧 19px 圆形 radio |
| 结果卡 | `.idea-card` | min-height 266px / 顶部 3px 色条（依次橘、深蓝、绿）/ hover 上移 3px |
| Why 引句 | `.why` | `--surface-2` 底 / 左 3px 金条 / 11.8px |
| 标签 | `.tag` | 10.5px / 999 圆角 / 灰底细边 |
| 键值行 | `.kv` | 上下 9px / 虚线分隔 / 最后一行无边框 |
| 步骤列表 | `.steps` | `counter` 生成 `01–07`，26×26 深墨蓝圆角块 |
| 警示 | `.warn` | `#FFF8EC` 底 + `#F2E2BE` 边 + 12.3px 深棕字 |
| 纸片预览 | `.paper` | 白底卡片，`rotate(-1.2deg)`，内含占位线条与斜纹块 |
| 开关 | `.toggle` | 40×23 / 灰 #DCD7CD；`.on` 绿，滑块右移 17px |
| toast | `.toast` | 右下固定 / 深墨蓝 / 13px 内边距 / 圆角 13 / 带绿点，**仅 P08 使用一次** |
| 成功勾 | `.big-check` | 74px 圆 / 绿底 / 外 12px 柔光 |

## 2.5 文案语气

- **说人话，不写系统语言**。写 `Why this fits you`，不写 `基于智能算法为您推荐`。
- **给具体数字**：`$120`、`20 家`、`<10 h/wk`、`$49/month`，禁止"大概几千""适当投入""社交媒体推广"。
- **动词开头**写步骤：Pick / Write / Print / Walk in / Offer / Deliver / Ask。
- 英文版全英文；中文版只做等义替换，不润色成另一套调性。
- 任何页面禁止出现：`算法`、`权重`、`版本检测`、`同步中`、`加载中`、`服务器`、`云端`、`模型`、`API`、`数据库`、`引擎`、`配置`。

## 2.6 交互基律

1. 选项**点击即选中并 0.35s 自动进下一题**（Q4 多选例外，需点 `Done`）。
2. 页面跳转全部为本地路由，无 loading 态、无骨架屏、无转场动画超过 0.2s。
3. 所有 `.toggle` 点击即切，本地立即生效，无保存按钮。
4. **不弹确认框**，唯一例外：`Clear saved list` 需二次确认。
5. 任何网络动作失败 → **静默跳过**，不产生任何 UI 变化。

---

# 3. 用户、场景与两条链路

## 3.1 目标用户（首版 3 类 Persona）

| ID | Persona | 处境 | 掏钱的理由 | 最怕什么 |
|---|---|---|---|---|
| U1 | 副业尝试者（US/UK 上班族） | 有 $500–2k 积蓄，每周 <10h，搜过 "side hustle ideas" 全是空话 | 想要 3 条"钱够、时间够、明天能动手"的具体生意 | 又给他一堆要自己判断的清单 |
| U2 | 本地小生意人（SG/PH 店主、修理工） | 有手艺、有设备，想再加一条收入线 | 想要按自己国家写的获客渠道和成本表 | 写的是美国才有的平台 |
| U3 | 第一次创业的人（AU/CA 自由职业者） | 怕压库存、怕亏、怕复杂 | 想要一张纸，别给他一个"系统" | 要注册、要学、要联网、要订阅 |

## 3.2 首次使用链路（核心）

```
双击图标 → P01 → 点 1 次 → P02 连续 5 题 → P03 三张卡 → 点 1 张 → P04
→ 点导出 → 系统另存为 → P05 → 关掉
```
**量化目标**：首次打开到拿到 PDF ≤ 3 分钟；用户点击 ≤ 8 次；无需任何"设置/模式选择/概念理解"。

## 3.3 复访链路（买断制的"回来"）

> 不靠会员到期。靠：第一个生意做成了 → 想找第二个点子 → 桌面上那个图标还在 → 双击，还是那 5 道题、还是 3 张卡、什么都不用重新学。

- P06「我的点子」底部固定一句：`Made your first sale? Come back and run the 5 questions again with a bigger budget.`
- 复访时允许把 Q2 资金档调大，引擎自然给出不同 Top 3；**不弹"升级""解锁""新版本"**。
- **"它一直那样，没找过我麻烦"就是买断工具的「不用管了」**。

## 3.4 不上架的中文链路

同 §3.2 / §3.3，只是字换成中文，专供你自己看、自己用、自己练熟。见 §18。

---

# 4. 系统架构、运行边界与文件清单

## 4.1 架构图

```
┌──────────────────── 用户设备（核心逻辑 100% 在此） ────────────────────┐
│                                                                        │
│  [界面层]  Vue3（打包进壳，非远程网页）                                  │
│      ↓ 调用                                                             │
│  [本地引擎层] Python 编写的诊断引擎 → 打包为本地可执行模块                │
│      ├ 硬过滤 / 打分 / 降权 / 降级 / 排序                                 │
│      ├ 读 baseline_v1.json + 已合并的 delta                              │
│      └ 生成 Top 3 + Why 文案                                             │
│      ↓                                                                  │
│  [本地数据层] 商机库 / 存档 / 激活凭证 / 导出路径                          │
│      ↓                                                                  │
│  [本地导出层] PDF 单页渲染 + 可选 CSV                                     │
│                                                                        │
│  [桌面壳] Tauri（推荐，包小）或 Electron → MSIX / exe / app / dmg         │
└──────────────┬─────────────────────────────────────────────────────────┘
               │ 唯一出网（可选、月度、静默、失败无感）
               │ ① GET manifest.json  ② GET delta_YYYY-MM.json  ③ 首次激活校验
┌──────────────▼─────────────────────────────────────────────────────────┐
│ 静态托管（Cloudflare Pages / S3 / GitHub Pages）                          │
│   manifest.json + delta_2026-12.json + delta_2027-01.json + …             │
│   ❌ 无 FastAPI 常驻  ❌ 无数据库  ❌ 无大模型账单  ❌ 无用户数据          │
│   挂了 / 到期 / 忘续费 → 客户端静默跳过，用户零感知                        │
└────────────────────────────────────────────────────────────────────────┘
```

## 4.2 为什么这样切（对应已确认的技术边界）

| 判断 | 落点 |
|---|---|
| 不用 UniApp | 它不产出 Windows / macOS 桌面安装包 |
| Python 的正确位置 | 写诊断引擎与库工具，**打包进客户端**；不放在服务器让用户联网调用 |
| FastAPI 本期不使用 | 若以后做云端增值，只能作为独立可选服务，且**绝不能成为买断功能的前提** |
| 不接 Stripe / PayPal / 内购 SDK | 钱由平台收，软件内零支付代码 |
| 联网 ≠ 云端 | 联网只搬文件，不搬逻辑；服务器挂了用户无感 |

## 4.3 安装目录与用户数据目录

| 平台 | 安装目录 | 用户数据目录（可写） |
|---|---|---|
| Windows Store (MSIX) | 系统管理的应用包目录（只读） | `%LOCALAPPDATA%\BizSpark\` |
| Windows 分销版 | `%LOCALAPPDATA%\Programs\BizSpark\` | `%USERPROFILE%\Documents\BizSpark\` |
| Mac App Store（沙盒） | `/Applications/BizSpark.app`（只读） | `~/Library/Application Support/BizSpark/` |
| Mac 分销版 | `/Applications/BizSpark.app` | `~/Documents/BizSpark/` |

## 4.4 客户端文件清单（开发交付物）

```
<BizSpark 安装目录>/
├ BizSpark.exe / BizSpark.app        桌面壳主程序
├ engine/                           打包后的本地诊断引擎
├ ui/                               Vue3 构建产物（本地文件，非远程 URL）
├ data/
│   └ baseline_v1.json              312 条冻结基线库（只读）
└ assets/                           图标 / 字体子集

<用户数据目录>/
├ library.json                     当前合并后的完整库（首次启动由 baseline 复制生成）
├ library_backup.json              每次 delta 合并前的备份（回滚用）
├ library_version.txt              当前库版本，如 "2026-11"
├ saved.json                       我的点子 + 上次答案 + 导出路径
├ licence.dat                      分销版激活凭证（签名，Store 版无此文件）
└ exports/                         导出默认目录（用户可在设置改）
```

## 4.5 启动时序（冷启动 ≤1.5s）

| 序 | 动作 | 是否可失败 | 失败处理 |
|---|---|---|---|
| 1 | 加载本地 UI 资源 | 否 | — |
| 2 | 读 `library_version.txt` / `saved.json` | 是 | 静默重建空文件 |
| 3 | 校验 `licence.dat`（仅分销版） | 是 | 仅在缺失时显示 P07；已激活则跳过 |
| 4 | 渲染 P01 首屏 | 否 | — |
| 5 | **后台异步**：检查是否到每月 1 号且距上次检查 >30 天 → GET `manifest.json`（超时 3s） | 是 | 静默跳过，不做任何 UI 变化 |
| 6 | 若有新版 → 下载 delta → 备份 → 合并 → 写版本号 | 是 | 自动回滚 `library_backup.json` |
| 7 | P08 右下角展示一次轻 toast（**仅当用户恰好打开 P08**） | — | — |

> **关键**：第 5–6 步完全不阻塞第 4 步。用户点 "Find my 3 ideas" 时若后台还在下载，直接照常用当前库，不等待。

## 4.6 出网白名单（审计口径）

| 请求 | 频率 | 携带数据 | 失败后果 |
|---|---|---|---|
| `GET manifest.json` | 每月最多 1 次，或距上次 >30 天 | 仅版本号字符串 | 静默跳过 |
| `GET delta_YYYY-MM.json` | manifest 指示有新版时 | 无 | 静默跳过 + 回滚 |
| `POST /activate`（分销版首次激活） | 每码每设备 1 次 | 码哈希 + 设备指纹哈希 | 提示重试或离线人工码（不阻断试用），禁止"授权失败"红字 |

**除此之外零出网**。不含埋点、不含崩溃上报（除非用户在 P09 主动打开，且只含错误码与版本）、不含答案、不含点子、不含文件路径、不含设备名。

---

# 5. 用户操作逐步规格（S01–S32）

> 每步写清：用户动作 → 系统响应 → 界面变化 → 本地数据变化 → 耗时上限 → 异常分支。
> 英文为主，括号内为中文镜像文案。

| 步 | 用户动作 | 系统响应 | 界面变化 | 数据变化 | 上限 | 异常分支 |
|---|---|---|---|---|---|---|
| S01 | 双击桌面图标 / 在商店点「启动」 | 执行 §4.5 启动时序 1–4 | 出 P01 欢迎页 | 无（或静默重建损坏文件） | 1.5s | 存档损坏 → 静默重建 |
| S02 | 视线扫过 P01 | 无 | 静态展示：大标题、副文、1 个橘按钮、1 个文字链接、信任行、右侧倾斜卡 | 无 | — | — |
| S03 | 点 `Find my 3 ideas →`（找我的 3 个点子 →） | 初始化问卷状态，清空本轮临时答案 | 跳 P02 第 1 题，进度条第 1 点亮橘 | 内存写入 `quiz.session` | 0.2s | — |
| S04 | 看 P02 Q1 `Where are you starting?`（起步在哪个国家？） | 预选系统区域猜测值，猜不中默认 US | 6 个国家卡，选中态橘边 | 无 | — | 区域不在 6 国内 → 默认 US，不提示 |
| S05 | 点 1 个国家卡 | 记录 `country`，0.35s 后自动进下一题 | 进度条第 1 点转绿，第 2 点亮橘 | 内存 `answers.country` | 0.35s | 连点两次 → 以最后一次为准，不重复跳页 |
| S06 | 看 P02 Q2 `How much can you put in to start?`（起步能拿出多少钱？） | 无默认，主按钮置灰 | 4 个资金档卡 | 无 | — | 未选点不了下一步 |
| S07 | 点 1 个资金档（示例 `$500–$2,000`） | 记录 `capital_tier`，0.35s 自动进 Q3 | 进度条第 2 点绿、第 3 点橘 | 内存 `answers.capital` | 0.35s | — |
| S08 | 看 Q3 `Hours per week?`（每周能投入几小时？） | 无默认 | 3 个时间档 | 无 | — | — |
| S09 | 点 `<10h` | 记录 `hours`，自动进 Q4 | 进度条第 3 点绿、第 4 点橘 | 内存 `answers.hours` | 0.35s | — |
| S10 | 看 Q4 `What do you already have?`（手上已有什么？） | **多选**，可一个都不选 | 8 个资源卡 + 一个 `Done` | 无 | — | 一个都不选合法，走"什么都没有" |
| S11 | 点若干资源卡（示例 `laptop`） | 累积多选，不自动跳页 | 每张选中卡橘边 | 内存 `answers.assets[]` | — | 再点一次取消选中 |
| S12 | 点 `Done` | 记录资源数组，进 Q5 | 进度条第 4 点绿、第 5 点橘 | 内存落定 | 0.2s | — |
| S13 | 看 Q5 `How much risk is OK?`（能接受多大风险？） | 无默认 | 3 个风险档 | 无 | — | — |
| S14 | 点 1 个风险档 | **触发本地匹配引擎**（§9） | 进度条全绿，直接跳 P03 | 内存 `answers.risk`；写 `saved.json.last_answers` | ≤300ms | — |
| S15 | 引擎执行硬过滤 | 按 `capital_tier / hours / countries / legal_blocks / status` 剔除 | 无 UI | 只读 `library.json` | ≤80ms | 见 S16 |
| S16 | 硬过滤后不足 3 条 | 自动放宽 `hours_per_week` 一档，重跑一次 | 无 UI | 无 | ≤80ms | 仍不足 → 输出实际 1–2 条 + 温和一句，**绝不空白页** |
| S17 | 引擎执行 8 维打分 | 权重见 §9.3，趋势新鲜度锁 5% | 无 UI | 无 | ≤120ms | — |
| S18 | 引擎降权已看过的 `id` | 与 `saved.json.saved[]` 比对，命中降权 15% | 无 UI | 无 | ≤10ms | 无存档 → 跳过 |
| S19 | 引擎取 Top 3 并生成 Why 句 | 用答案里的具体词拼句 | 无 UI | 内存 `results[]` | ≤20ms | — |
| S20 | 渲染 P03 | 三张结果卡 + 答案复述 + 底部统计 | 出 P03 | 无落盘 | 0.2s | — |
| S21 | 看 P03 三张卡 | 无 | 每卡 7 元素（编号/匹配度/标题/说明/Why/3 标签/主按钮） | 无 | — | — |
| S22 | 点第 1 张卡的 `See the one-page plan →`（看一页方案 →） | 按 `id` 从本地库取全字段渲染 | 跳 P04 | 内存 `current_idea_id` | 0.2s | 字段缺失 → 用兜底文案，不报错 |
| S23 | 浏览 P04 左侧 6 模块 | 无 | 成本表 / 7 步 / 渠道 / 3 坑；右侧 sticky 纸片预览常驻 | 无 | — | — |
| S24 | 勾选某个步骤（本地交互） | 勾选态仅本轮有效，可勾可不勾 | 步骤前出现勾 | 内存 | — | 不落盘、不影响导出 |
| S25 | （可选）点 `Save` / 返回 P03 点 `Save all three` | 写入本地存档 | P06 出现该条 | `saved.json.saved[]` 追加 `{id, saved_at}` | ≤10ms | 重复保存 → 去重，不新增 |
| S26 | 点 `Export my plan ↓`（导出我的方案 ↓） | 本地渲染单页 PDF（§12） | 弹出系统原生「另存为」 | 无 | ≤2s | 路径不可写 → 仅提示换文件夹 |
| S27 | 在另存为里确认路径 | 写文件到 `Documents/BizSpark/`（默认），记住路径 | 跳 P05 完成页 | 写 PDF；更新 `saved.json.export_dir` | ≤2s | 磁盘满 → 提示换目录，不丢已渲染内容 |
| S28 | 看 P05 | 无 | 大绿勾 + 文件名/大小/路径 + 2 个按钮 + 否定式信任行 | 无 | — | — |
| S29 | 点 `Open folder`（打开文件夹） | 调系统文件管理器定位到该 PDF | 外部窗口 | 无 | — | 系统不支持 → 静默忽略 |
| S30 | 或点 `Find another idea`（再找一个点子） | 回到 P03，**保留本轮结果** | 跳 P03 | 无 | 0.2s | — |
| S31 | 点侧栏 `My ideas` | 读本地存档渲染 | 跳 P06 | 无 | 0.2s | 空 → 显示空态一句，不空白 |
| S32 | 关闭窗口 | 释放内存，保留所有本地文件 | — | 已落盘数据不变 | — | 强制断电不损坏：写文件用「临时文件 + 原子替换」 |

**点击次数核算**：S03(1) + S05(1) + S07(1) + S09(1) + S11(≥1) + S12(1) + S14(1) + S22(1) + S26(1) + S27(1) ≈ **10 次**，其中 S11 多选与系统另存为属用户自主动作；核心决策点击 ≤ 8 次，符合 §1 量化目标。

---

# 6. 页面逐页规格（P01–P09，元素级）

> 每页给出：布局、元素清单（含中英文案原文）、状态、跳转、异常。**文案以 `en/html/` 现有内容为准，中文以 `cn/html/` 为准，开发不得自行改写。**

## P01 · 欢迎 / 启动页 `01-welcome.html`

**布局**：`.hero` 深色整屏 `min-height:100vh`；背景 = 深墨蓝底 + 右上径向深蓝 + 左下径向暗棕 + 点阵（`26px` 网格，`rgba(255,255,255,.5) .7px`，opacity .16）；`.orb.a` 340px 描边圆、`orb.b` 220px 橘径向光晕；顶部 `.hero-top` padding `30px 48px`；主体 `.hero-body` padding `20px 48px 60px`；右侧 `.hero-mock` 330px 宽、`translateY(-50%) rotate(-4deg)`。

| # | 元素 | 类型 | 英文文案 | 中文文案 | 状态 / 行为 |
|---|---|---|---|---|---|
| 1 | brand | 文字块 | `BizSpark` / `One idea away` | `BizSpark` / `一个点子就够了` | 32px 橘方标含字母 B |
| 2 | 顶部链接 | 4 个纯文字 | `How it works` `What you get` `Privacy` `v1.0.0` | `怎么用` `你会拿到什么` `隐私` `v1.0.0` | 无跳转（首版占位，不做弹窗） |
| 3 | eyebrow | 标签 | `A one-time desktop tool · No account · No subscription` | `一次性买断的桌面工具 · 无需账号 · 无订阅` | 金色 |
| 4 | H1 | 标题（3 行） | `You don't need / a business plan. / You need one idea.` | `你不需要 / 商业计划书。 / 你只要一个点子。` | `one idea` / `一个点子` 用橘色 `<em>` |
| 5 | 副文 | 段落 | `Answer 5 short questions. Get 3 businesses you can actually start with the money, time and skills you already have — plus a one-page plan you can print and follow tomorrow.` | `回答 5 道小题。拿到 3 个用你手上的钱、时间和本事真能开起来的生意——外加一张明天就能打印、照着做的一页纸。` | 17px / `#B7C6D3` / 最大宽 530 |
| 6 | **主 CTA** | `.btn-primary.btn-lg` | `Find my 3 ideas →` | `找我的 3 个点子 →` | 跳 P02；**全页唯一强按钮** |
| 7 | 次链接 | `.btn-quiet.btn-lg` | `Open my saved ideas` | `打开我存的点子` | 跳 P06；弱化为文字按钮 |
| 8 | 信任行 | 3 段 | `One-time purchase · Yours forever` / `✓ Works offline` / `✓ Your answers never leave this device` | `一次买断，永久归你` / `✓ 离线可用` / `✓ 你的答案绝不离开这台设备` | 12px 灰 · **不含金额**，由价格配置渲染 |
| 9 | 右侧 mock 卡 | 静态卡 | `Top match for you` / `01 / 03 · 94% MATCH` / `Local shop review-reply desk` / 说明 / 3 标签 | `最匹配你的一个` / `01 / 03 · 94% 匹配` / `街边小店评论代回` / 说明 / 3 标签 | 倾斜 -4°，纯展示不可点 |
| 10 | footer | 两行 | `Built for people who want to start small and start today.` / `Microsoft Store · Mac App Store · One-time purchase` | `给想从小处着手、今天就动手的人。` / `Microsoft Store · Mac App Store · 一次买断` | 11px / 顶边 1px 半透明白 · **不含金额** |

**异常**：无。首屏不请求权限、不弹联网确认、不放启动广告、不显示"上次使用"、不显示版本更新提示。

## P02 · 诊断问卷 `02-quiz.html`

**布局**：标准壳体；`.page-head` + `.stepper` + `.quiz-wrap`（左 `minmax(0,1fr)` 右 `268px`）；左 `.q-card` padding `34px 36px`；右两张 `.aside-note`。

| # | 元素 | 英文 | 中文 | 说明 |
|---|---|---|---|---|
| 1 | eyebrow | `Step 2 of 5` | `第 2 步 / 共 5 步` | 随题号变 |
| 2 | H1 | `Five questions. That's all.` | `5 道题。就这些。` | 全 5 题不变 |
| 3 | lead | `No sign-up, no typing an essay. Everything stays on this computer.` | `不用注册，不用写小作文。一切都留在这台电脑里。` | — |
| 4 | 进度条 | `About you / Money / Time / Resources / Ready` | `关于你 / 钱 / 时间 / 手上的资源 / 好了` | 5 点，done 绿 / on 橘 / todo 灰 |
| 5 | 题号 | `Question 02 — Money` | `第 02 题 — 钱` | — |
| 6 | 题干 | `How much can you put in to start?` | `起步你能拿出多少钱？` | 26px / 730 |
| 7 | 辅助说明 | `Pick the amount you'd be OK losing if it doesn't work out. We'll only show ideas that fit.` | `选一个万一没做成、你也扛得住的数目。我们只给你看配得上的点子。` | 11.5px 弱化 |
| 8 | 选项 ×4 | 见 §7 F02 题目表 | 同左中文 | 每卡 = radio + emoji + 标题 + 一行解释 |
| 9 | 右卡 1 | `🔒 Nothing leaves this device` / `Your answers are used locally to pick ideas and are never uploaded. No account, no email, no tracking.` | `🔒 什么都不离开这台设备` / `你的答案只在本地用来挑点子，绝不上传。没有账号、没有邮箱、没有追踪。` | 白卡 |
| 10 | 右卡 2 | `✦ Why only 3 ideas?` / `Because 30 ideas is just homework. Three that actually fit you is a decision.` | `✦ 为什么只给 3 个？` / `因为 30 个是作业，3 个真合适的才是决定。` | 深墨蓝反白卡 |
| 11 | 底部 | `← Back` / `Next question →` / `Takes about 40 seconds` | `← 返回` / `下一题 →` / `大约 40 秒` | 实际交互为"选中即自动进下一题"，按钮保留作可视锚点 |

**5 题定义（写死，不许加题、不许改顺序）**

| # | 英文题干 | 中文题干 | 控件 | 选项（英 / 中） | 默认 |
|---|---|---|---|---|---|
| Q1 | `Where are you starting?` | `起步在哪个国家？` | 单选 | US / CA / UK / AU / SG / PH（中文：美国 / 加拿大 / 英国 / 澳大利亚 / 新加坡 / 菲律宾） | 系统区域猜测，猜不中 US |
| Q2 | `How much can you put in to start?` | `起步你能拿出多少钱？` | 单选 | `Almost nothing — under $500` / `$500 – $2,000` / `$2,000 – $10,000` / `$10,000+`（中文对应 4 档） | 无，必须选 |
| Q3 | `Hours per week?` | `每周能投入几小时？` | 单选 | `<10h` / `10–25h` / `Full-time` | 无 |
| Q4 | `What do you already have?` | `手上已有什么？` | **多选** | 车 / 厨房 / 电脑 / 设计 / 写代码 / 闲置房间 / 本地人脉 / 什么都没有 | 可空 |
| Q5 | `How much risk is OK?` | `能接受多大风险？` | 单选 | 亏了不能影响生活 / 可接受小亏 / 能扛一次全亏 | 无 |

**约束**：无键盘输入、无自由文本、无必填弹窗；`← Back` 不丢答案；Q4 是唯一需要 `Done` 的一屏；断网完全无影响。

## P03 · 结果页 `03-results.html`

**布局**：`.page-head` + `.grid.g3`（3 等列，gap 16）+ 分隔线 + 操作行 + `.stat` 三数。

| # | 元素 | 英文 | 中文 |
|---|---|---|---|
| 1 | eyebrow | `Ready in 40 seconds` | `40 秒出结果` |
| 2 | H1 | `Three businesses you can actually start.` | `3 个你真能开起来的生意。` |
| 3 | lead | `Based on $500–$2,000, under 10 hours a week, a laptop, and United States. Nothing was sent anywhere.` | `按 $500–$2,000、每周不到 10 小时、一台电脑、美国来算。什么都没传出去过。` |
| 4 | 卡 1 | `01 / 03 · 94% MATCH` / `Local shop review-reply desk` / 说明 / `Why this fits you: Low money, laptop only, repeat monthly income — matches your budget and time.` / `From $120` `<10 h/wk` `Monthly` / `See the one-page plan →` | `01 / 03 · 94% 匹配` / `街边小店评论代回` / … / `为什么适合你：钱少、只要一台电脑、按月收钱——正好对上你的预算和时间。` / `$120 起步` `每周 <10 小时` `按月收钱` / `看一页方案 →` |
| 5 | 卡 2 | `02 / 03 · 89% MATCH` / `AI-assisted product photo cleanup` / `From $80` `Online` `New wave` | `02 / 03 · 89% 匹配` / `AI 辅助商品图精修` / `$80 起步` `线上` `新趋势` |
| 6 | 卡 3 | `03 / 03 · 85% MATCH` / `Weekend mobile notary & form helper` / `From $260` `Local` `Weekend` | `03 / 03 · 85% 匹配` / `周末上门填表与见证` / `$260 起步` `本地` `周末` |
| 7 | 操作行 | `← Change my answers` / `Save all three` / `Older, saturated ideas are kept in the library but never pushed to the top.` | `← 改我的答案` / `三个都存起来` / `过时、已经卷透的点子仍留在库里，但绝不会被推到前面。` |
| 8 | 统计 | `312 ideas checked locally` / `309 ruled out by your money & time` / `3 worth your Monday` | `312 本地筛过的点子` / `309 被你的钱和时间筛掉` / `3 值得你周一动手` |

**结果卡固定 7 元素，不得增减**：编号+匹配度 / 标题 / 一句话说明 / Why 引句 / 3 个标签 / 主按钮。三卡顶部 3px 色条依次 `#F2653A`、`#15344E`、`#1F8A70`，`:nth-child` 实现。

**禁止**：筛选器、排序、分页、"查看更多"、对比勾选、广告位、升级解锁。

## P04 · 点子详情页 `04-detail.html`

**布局**：`.detail-wrap` = 左 `minmax(0,1fr)` + 右 `300px`；右侧 `.sticky` `top:24px`；左侧 4 张 `.sec` 卡，每张 margin-bottom 16px。

| 区块 | 标题（英 / 中） | 必须内容 |
|---|---|---|
| page-head eyebrow | `Idea 01 / 03 · 94% match` / `点子 01 / 03 · 94% 匹配` | — |
| H1 | `Local shop review-reply desk` / `街边小店评论代回` | — |
| lead | 一句话讲清谁付钱、为什么现在有人买 | — |
| M1 | `$ What it costs to start` / `$ 起步要花多少钱` | 5 行 `.kv`：域名 $12/年、模板 $0、20 封信 $8、邮件工具 $0–15、**合计 $120（橘色）** |
| M2 | `1 Your first 7 steps` / `1 前 7 步` | `.steps` 01–07，动词开头，可勾选 |
| M3 | `↗ Where the first customers come from` / `↗ 第一批客户从哪来` | 4 个 `.pill`，按国家不同 |
| M4 | `! Three ways people get this wrong` / `! 最容易踩的 3 个坑` | 3 条 `.warn` + 1 句合并在第 3 条里 |
| 右卡 eyebrow | `Your one-page plan` / `你的一页纸方案` | — |
| 纸片 | `BizSpark · One-page plan` / `BizSpark · 一页纸方案` + 标题 + 占位线 + 斜纹块 | 倾斜 -1.2° |
| 右卡说明 | `A printable PDF with the cost table, 7 steps, pricing and first-customer channels. Generated on this device, saved wherever you choose.` | 中文等义 |
| 主 CTA | `Export my plan ↓` / `导出我的方案 ↓` | 跳 P05（触发另存为） |
| 次按钮 | `← Back to 3 ideas` / `← 回到 3 个点子` | 跳 P03 |
| 脚注 | `🔒 Nothing is uploaded. Ever.` / `🔒 什么都不会上传。永远。` | — |

**7 步原文（英）**：Pick one street / Write 10 reply templates / Print 20 letters / Walk in on a Tuesday morning / Offer $49/month / Deliver in 24 h / Ask shop #1 for one introduction。

**3 坑原文（英）**：`Don't sell "AI writing" — sell "your reviews get answered by tomorrow"` / `Don't take more than 25 clients before you have templates` / `Check local rules on soliciting businesses in person`。

**字段兜底**：任一内容字段缺失 → 用一句通用兜底文案渲染，**绝不报错、绝不空白卡片**。

**UI 与 PDF 的口径差异（开发别混）**：P04 页面**只有 4 张卡**，不单独设"定价卡"和"合规卡"——`pricing_hint` 只在导出的 PDF 第 6 块输出，`compliance_note` 合并进第 3 条 `.warn` 里作为一句话提醒。V1.0 曾把二者单列为 6 模块，**实现以本规格书的 4 卡 + PDF 10 块（§12.2）为准**。页面少两块，正是"用户端只留小"的落地。

## P05 · 导出完成页 `05-export.html`

**布局**：`.center-card` 最大宽 620px 居中，padding `46px 40px`，居中对齐；下方再一张同宽说明卡。

| # | 元素 | 英文 | 中文 |
|---|---|---|---|
| 1 | 成功勾 | 74px 绿圆 `✓` | 同 |
| 2 | eyebrow | `Done, on your computer` | `好了，就在你电脑里` |
| 3 | H1 | `Your plan is ready.` | `你的方案好了。` |
| 4 | lead | `One PDF, one page, no watermark. It's a file on your disk — not a link, not an account, not something that can expire.` | `一张 PDF，一页，无水印。它是你硬盘上的一个文件——不是链接、不是账号、也不是会过期的东西。` |
| 5 | 文件行 | `BizSpark-Plan-local-review-desk.pdf` / `Saved to Documents / BizSpark · 214 KB · 1 page` / `✓ Saved` | 文件名不译 / `已存到 文档 / BizSpark · 214 KB · 1 页` / `✓ 已保存` |
| 6 | 按钮 | `Open folder` / `Find another idea` | `打开文件夹` / `再找一个点子` |
| 7 | 信任行 | `No subscription. No auto-renew. Buy once, use it as long as you like — even with the internet off.` | `无订阅、不自动续费。买一次，想用多久用多久——就算断网也一样。` | **不含金额** |
| 8 | 下卡 | `What's inside the PDF` / `Optional extras`（CSV 说明） | `PDF 里有什么` / `可选附带` |

## P06 · 我的点子 `06-saved.html`

**布局**：`.page-head` + 3 张 `.mini` 列表（gap 12）+ 操作行 + 底部提示。

| # | 元素 | 英文 | 中文 |
|---|---|---|---|
| 1 | H1 / lead | `My ideas` / `Saved locally. No cloud, no sync, no login — open the app six months later and they're still here.` | `我的点子` / `本地保存。不上传、不同步、不登录——半年后再打开，它们还在这儿。` |
| 2 | 3 条 mini | 标题 + `Saved 12 Nov 2026 · From $120 · 94% match` + `Open` | `2026-11-12 保存 · $120 起步 · 94% 匹配` + `打开` |
| 3 | 操作 | `Find new ideas →` / `Compare two ideas` / `Clear saved list` | `找新点子 →` / `两个点子对照` / `清空已存` |
| 4 | 提示 | `💡 Made your first sale? Come back and run the 5 questions again with a bigger budget. Same button, same 3 cards.` | `💡 第一单做成了？回来把预算调大，再答一遍那 5 道题。还是那个按钮，还是 3 张卡。` |
| 5 | 空态 | `Double-click Find my 3 ideas. It takes 40 seconds.` | `点一下"找我的 3 个点子"，40 秒就好。` |

`Compare two ideas` 仅并排显示 3 项：起步成本 / 每周时间 / 回本天数，不加第四项。`Clear saved list` 是**全系统唯一二次确认**。

## P07 · 激活页 `07-activate.html`（**仅分销版可见**）

| # | 元素 | 英文 | 中文 |
|---|---|---|---|
| 1 | eyebrow | `For copies bought outside the stores` | `给在商店之外购买的版本` |
| 2 | H1 / lead | `Activate once. Use offline.` / `Store downloads are already activated — you'll never see this screen…` | `激活一次，之后离线用。` / `商店下载的版本已经激活过，你根本不会看到这一页……` |
| 3 | 输入区 | `Enter your code` / `It arrived in your receipt email right after payment.` | `输入激活码` / `付款后它就躺在你的收据邮件里。` |
| 4 | 码框 ×4 | `BZSP` `K7Q2` `M9XA` `••••` | 同（不译） |
| 5 | 说明 | `One code works on up to 3 of your own devices.` | `一个码最多用于你自己的 3 台设备。` |
| 6 | 设备位 | 2 个绿勾设备 + 1 个 `＋` + `2 of 3 devices used` | `已用 2 / 3 台` |
| 7 | 绿 notice | `Activation is not a login. Once verified, a small signed file is kept on this device. After that the tool works with the internet off — we never check again.` | `激活不是登录。校验通过后，本机只留一个很小的签名文件；此后软件断网也能用，我们不会再查第二次。` |
| 8 | 按钮 | `Activate & start →` / `Changed computer? Release a seat` | `激活并开始 →` / `换电脑了？释放一个名额` |
| 9 | 右深色卡 | `One-time purchase` / `Buy once. Own it forever.` + 5 条 ✓ | `一次买断` / `买一次。用一辈子。` + 5 条 ✓ | **不含金额** |
| 10 | 右下卡 | `Why a code at all?` / `An installer file can be copied. The code simply proves this copy was paid for…` | `为什么还要一个码？` / `安装包文件是可以被复制转发的……` |

**Store 版此页不编译进包**（或永不触发），用户一辈子看不到。

## P08 · 点子库 / 月度换挡 `08-update.html`

| # | 元素 | 英文 | 中文 |
|---|---|---|---|
| 1 | eyebrow / H1 / lead | `Quiet, optional, free` / `Your idea library` / `The tool checks once a month for new ideas. If it can't reach the internet, nothing happens…` | `安静、可选、免费` / `你的点子库` / `工具每月查一次有没有新点子。连不上就什么都不发生……` |
| 2 | 当前库 | `2026.11 · 312 ideas · 26 industries · 6 countries` + `✓ Up to date` | `2026.11 · 312 条点子 · 26 个行业 · 6 个国家` + `✓ 已是最新` |
| 3 | 时间线 4 节点 | `1 Dec 2026 · Next` `Agent-era small services` (+14) / `1 Nov 2026 · Installed` `AI-assisted service ideas` (+18) / `1 Oct 2026` `Local service pack` (+11, 3 retired) / `Baseline · v1.0` `312 ideas shipped inside the installer` | 对应中文：`2026-12-01 · 下一次` `智能体时代的小服务` / `2026-11-01 · 已装` `AI 辅助服务类点子` / `2026-10-01` `本地服务包` / `内置基线 · v1.0` `安装包里自带 312 条点子` |
| 4 | 右卡 | `How the monthly swap works` + 3 行 kv：`Update fails / no Wi-Fi → Silently skipped` `Your saved ideas → Untouched` `Cost to you → Static files only` | `每月换挡怎么跑` + `静默跳过` / `原样不动` / `只有几个静态文件` |
| 5 | 橘软卡 | `Why new ideas keep showing up` / 一段解释季节换挡、老点子下沉不消失 | `为什么点子要一直换新` |
| 6 | toast | `Library checked · you're up to date. No action needed.` | `点子库已检查 · 已是最新，不用管。` |

**注意**：P08 是后台页，普通用户不必访问；界面**没有"立即检查更新"按钮**（该按钮只放在 P09 About 区）。

## P09 · 设置 `09-settings.html`

| # | 元素 | 英文 | 中文 |
|---|---|---|---|
| 1 | eyebrow / H1 / lead | `Six knobs, that's it` / `Settings` / `Everything here is local. No profile, no password, nothing to sync.` | `就 6 个旋钮，没了` / `设置` / `这里每一项都是本地的。没有资料、没有密码、没有同步。` |
| 2 | 6 行开关/选择 | 见 §15 | 见 §15 |
| 3 | 隐私卡 | `Privacy, in one sentence` / `Your answers, your saved ideas and your exported plans never leave this device.` + 说明唯一出网请求 | `一句话讲清隐私` / 中文等义 |
| 4 | About | `Version 1.0.0` / `Library 2026.11 (312 ideas)` / `Licence One-time · activated` / `Account None` + `Check for updates` `View licence` | 对应中文 |

---

# 7. 功能规格（F01–F14，流程级）

## F01 启动与首屏（P0）

**目的**：0.8s 出首屏，用户第一眼只看到一个橘按钮。
**触发**：进程启动。
**前置**：无。
**流程**：§4.5 步骤 1–4 → 渲染 P01。
**输出**：P01 完整可点。
**异常表**：

| 异常 | 处理 |
|---|---|
| `saved.json` 损坏 / 非法 JSON | 静默重建 `{"saved":[],"last_answers":{},...}`，不弹窗、不影响其他文件 |
| `library.json` 缺失 | 从 `baseline_v1.json` 复制一份 |
| `licence.dat` 缺失（Store 版） | 正常，不检查 |
| `licence.dat` 缺失（分销版且未激活） | 显示 P07 |
| 系统区域不在 6 国 | 默认 US，不提示、不询问 |
| 首次启动无网络 | 一切正常 |

**验收**：冷启动到可点击 ≤1.5s；1440×900 一屏装下首屏无滚动；无权限弹窗、无广告、无教程、无"是否允许联网"。

## F02 诊断问卷（P0）

**目的**：用最少点击收集 5 组可用于硬过滤与打分的答案。
**触发**：P01 主 CTA。
**输入**：5 题，定义见 §6 P02 表。
**流程逐步**：S03 → S14；每题「点击 → 0.35s → 下一题」，Q4 例外。
**状态**：`quiz.session {step:1..5, answers:{country,capital,hours,assets[],risk}}`。
**输出**：完整 `answers` 对象，交 F03。
**异常表**：

| 异常 | 处理 |
|---|---|
| 未选就点下一步 | 主按钮置灰，无校验弹窗 |
| 快速连点两个选项 | 以最后一次为准，只跳一次页 |
| 点 `← Back` | 回上一题，已选答案保留并高亮 |
| Q4 一个都不选 | 合法，按 `assets=[]`（"什么都没有"）处理 |
| 中途退出再打开 | 不恢复半截问卷；`last_answers` 只用于预填，不强制 |
| 断网 | 完全无影响 |

**验收**：全程点击 ≤6 次（Q4 多算 1）；无键盘输入；无自由文本；无必填弹窗。

## F03 本地匹配引擎（P0，核心逻辑，客户端内）

**目的**：把 312 条收敛成 3 条"他做得成的"生意。
**触发**：Q5 选中。
**输入**：`answers` + `library.json`。
**流程**：S15 → S19，算法见 §9。
**输出**：`results[3]`，每条含 `id / title / one_liner / match_pct / why / tags[3]`。
**异常**：硬过滤不足 3 条 → 放宽时间档一次 → 仍不足给 1–2 条 + 温和一句；禁止空白页与"无结果"。
**验收**：312 条、最低配笔记本，从 Q5 到出结果 ≤300ms；**全程零网络请求**；重复跑同一答案结果稳定（同分按 `id` 字典序，保证确定性）。

## F04 结果页（P0）

**目的**：让用户 3 秒内确认"这软件懂我"。
**触发**：F03 完成。
**输出**：P03 三卡 + 答案复述 + 底部统计。
**约束**：只给 3 条；`saturated` 不进 Top 3；已看过 `id` 降权 15%；每卡固定 7 元素。
**异常**：结果 1–2 条时，第三张卡位置留空但**不显示占位卡**，底部统计数字同步改为实际值。
**验收**：无筛选器、无排序、无分页、无"查看更多"。

## F05 点子详情页（P0，产品价值全在这页）

**目的**：把一条商机渲染成"明天早上第一步干什么"都写清的一页。
**触发**：P03 任一张卡主按钮。
**输入**：`id` → 本地库全字段。
**输出**：左侧 M1–M4 四张卡（成本 / 7 步 / 渠道 / 3 坑）+ 右侧 sticky 纸片预览；`pricing_hint` 与 `compliance_note` 不单列成卡，分别进 PDF 第 6 块与第 3 条坑（见 §6 P04 口径说明）。
**内容要求**：成本逐项列钱并给合计；7 步动词开头可勾选；渠道按国家不同且写具体平台名；3 个坑写具体动作；合规只一句提醒，不写成法律意见。
**异常**：字段缺失 → 兜底文案；`first_customers` 无该国变体 → 用该条默认渠道，不报错。
**验收**：滚动时右侧预览常驻可见；100% 本地渲染，断网正常。

## F06 启动包生成与导出（P0）

**目的**：交付"一张纸"，且是磁盘上的文件、不是链接。
**触发**：P04 `Export my plan`。
**流程**：本地渲染单页 PDF（§12）→ 系统原生另存为 → 写文件 → 跳 P05。
**产物 A（必须）**：单页 PDF，命名 `BizSpark-Plan-{slug}.pdf`，无水印/无二维码/无分享。
**产物 B（P1）**：可选成本表 CSV，同目录。
**保存**：默认 `Documents/BizSpark/`，记住路径（F11）。
**异常**：路径不可写 / 磁盘满 → **仅**提示换一个文件夹，不丢已渲染内容。
**验收**：导出 ≤2s；断网导出成功；PDF 恰好 1 页可直接打印；文件不在云端生成。

## F07 我的点子（P0，本地留存）

**目的**：让复访零成本。
**触发**：P03 `Save all three` / P04 `Save` / 侧栏 `My ideas`。
**存储**：`saved.json.saved[] = [{id, saved_at}]`，单文件、无账号、无云端副本。
**支持**：并排对比（仅 3 项：成本 / 时间 / 回本）、清空（唯一二次确认）。
**空态**：一句提示，不空白。
**边界**：重装系统后丢失属预期行为，需在隐私说明里写明；`saved_at` 用本地日期 `YYYY-MM-DD`。
**验收**：去重保存不新增；断网可用；关闭再打开仍在。

## F08 商机库（P0，护城河本体）

详见 §8 数据字典、§10 内容规格。要点：312 条 / 26 行业 / 6 国 / 4 资金档；老商机不删只降权；`baseline_v1.json` 随包冻结，纯文本可手工编辑。

## F09 月度增量更新（P1，联网的唯一理由）

详见 §13。要点：每月 1 号发布 delta；客户端启动后台静默检查；`add / revise / retire` 三操作；失败静默跳过；合并前备份、失败回滚；买断用户不额外付费。

## F10 授权激活（P0，分渠道，绝不做成登录）

详见 §14。要点：Store 版零授权代码；分销版一码 3 台设备、机器指纹、首次联网校验一次后永久离线。

## F11 设置（P1，六个旋钮封顶）

详见 §15。

## F12 客户端自动更新（P1）

- Store 版：完全交给商店，客户端**不写 updater**。
- 分销版：静默检查新安装包 → 提示"新版本可用，下次启动时更新"，**不强制、不阻断当前使用**。
- **与 F09 分离**：库更新 ≠ 程序更新，两者互不依赖，任一失败不影响另一。

## F13 空态、异常与边界（P0，统一口径）

详见 §16。全局禁令：任何红色错误弹窗、任何"请检查网络后重试"、任何需要用户理解的报错码。

## F14 非功能需求（P0）

详见 §17。

---

# 8. 数据字典（字段级）

## 8.1 商机条目 `idea`（`library.json` 的数组元素）

| 字段 | 类型 | 必填 | 取值域 / 格式 | 默认 | 示例 | 校验规则 | 用途 |
|---|---|---|---|---|---|---|---|
| `id` | string | ✔ | `^[a-z]{2}-[a-z0-9-]{2,20}-\d{3}$`（两位国家码 + 中间段可含连字符 + 三位序号） | — | `us-svc-ai-014` | 全局唯一；delta 靠它覆盖；中间段允许 `svc-ai`、`legacy` 等长度 | 身份 |
| `title` | string | ✔ | ≤60 字符，英文标题式 | — | `Local shop review-reply desk` | 非空；不许含 emoji | 结果卡/详情/PDF 标题 |
| `one_liner` | string | ✔ | ≤120 字符，一句话讲清谁付钱 | — | `Help 20 local shops reply to…` | 必须以动词或名词短语开头，禁止"做自媒体""开网店"类空话 | 结果卡说明 |
| `min_capital` | number | ✔ | ≥0，单位 USD（各国变体换算见 §8.3） | — | `120` | 整数；≤ `capital_tier` 上限 | 硬过滤展示 |
| `capital_tier` | enum | ✔ | `0-500` / `500-2k` / `2k-10k` / `10k+` | — | `0-500` | 必须匹配 Q2 四档之一 | **硬过滤** |
| `hours_per_week` | enum | ✔ | `<10` / `10-25` / `full` | — | `<10` | 必须匹配 Q3 三档之一 | **硬过滤** |
| `countries` | string[] | ✔ | `US,CA,UK,AU,SG,PH` 子集 | — | `["US","CA","UK","AU","SG","PH"]` | 至少 1 个；不得含表外值 | **硬过滤** |
| `online_or_offline` | enum | ✔ | `online` / `offline` / `hybrid` | — | `online` | — | 标签 |
| `legal_blocks` | string[] | ✔ | 国家码数组（该条在该国不可做） | `[]` | `[]` | 不得与 `countries` 重叠 | **硬过滤** |
| `skills_needed` | string[] | ✔ | 受控词表：`writing,design,coding,sales,driving,cooking,repair,basic_english,organizing` | `[]` | `["writing","basic_english"]` | 只用词表内值 | 打分 20% |
| `assets_needed` | string[] | ✔ | 受控词表：`car,kitchen,laptop,spare_room,local_network,tools,none` | `[]` | `["laptop"]` | 只用词表内值；与 Q4 多选一一对应 | 打分 20% |
| `risk_level` | enum | ✔ | `low` / `medium` / `high` | — | `low` | — | 打分 15% |
| `payback_days` | number | ✔ | 1–365 | — | `30` | 整数 | 打分 10% + 对比第 3 项 |
| `recurring` | boolean | ✔ | true/false | — | `true` | — | 打分 5% + 标签 |
| `channel_ids` | string[] | ✔ | 受控词表：`google-maps,nextdoor,thumbtack,etsy,shopify,facebook,whatsapp,walk-in,chamber,referral` | `[]` | `["google-maps","nextdoor","walk-in"]` | 只用词表内值 | 打分 10% |
| `cost_breakdown` | object[] | ✔ | `[{item:string, amount:number}]`，2–6 项 | — | `[{"item":"Domain…","amount":12},…]` | `amount≥0`；末项不自动合计，合计由引擎求和 | **M1 成本表** |
| `steps` | string[] | ✔ | **长度必须 = 7** | — | `["Pick one street",…]` | 长度≠7 校验失败；每步 ≤80 字符、动词开头 | **M2 前 7 步** |
| `pricing_hint` | string | ✔ | ≤80 字符，含具体数字 | — | `$49/month for up to 15 replies` | 必须含 `$` 或数字 | M4 定价 |
| `first_customers` | object | ✔ | `{ "default": string[], "US":[], "CA":[], "UK":[], "AU":[], "SG":[], "PH":[] }`，至少 `default` | — | 见 §8.3 | 按国家取，缺则回退 `default` | **M3 渠道** |
| `pitfalls` | string[] | ✔ | **长度必须 = 3** | — | `["Sell the outcome, not AI",…]` | 长度≠3 校验失败；每条 ≤120 字符、写具体动作 | **M4 三个坑** |
| `compliance_note` | object | ✔ | `{ "default": string, "<CC>": string }` | — | `{"default":"Check local business-name rules.","US":"…"}` | 一句话；禁止写成法律意见 | M4 合规 |
| `wave` | enum | ✔ | `mobile-internet` / `ai-llm` / `ai-agent` / `bi-agent` / `future` | — | `ai-llm` | 可累加，不按年份硬编码 | 趋势新鲜度 5% |
| `trend_tags` | string[] | ✔ | 自由标签 ≤5 个 | `[]` | `["ai","local-service","retainer"]` | 小写连字符 | 内容编辑用，不展示给用户 |
| `first_seen` | string | ✔ | `YYYY-MM` | — | `2026-11` | 合法年月 | 换挡记录 |
| `maturity` | enum | ✔ | `emerging` / `growing` / `mature` / `saturated` | — | `growing` | `saturated` 不进 Top 3 | 打分 + 换挡 |
| `version` | integer | ✔ | ≥1 | `1` | `3` | 每次 revise +1 | delta 合并 |
| `updated_at` | string | ✔ | `YYYY-MM-DD` | — | `2026-11-01` | 合法日期 | 时间线 |
| `status` | enum | ✔ | `active` / `retired` | `active` | `active` | `retired` 不参与打分、**不从磁盘删除** | 硬过滤 |

> **强校验**：`steps.length===7`、`pitfalls.length===3`、`id` 唯一、`capital_tier` 与 `hours_per_week` 属于枚举。建库脚本必须在打 `baseline_v1.json` 前跑一遍校验，不合格的条目不许入库。

## 8.2 完整样例（可直接作为第 1 条基线数据）

```json
{
  "id": "us-svc-ai-014",
  "title": "Local shop review-reply desk",
  "one_liner": "Help 20 local shops reply to Google/Yelp reviews with a fixed template pack",
  "min_capital": 120,
  "capital_tier": "0-500",
  "hours_per_week": "<10",
  "countries": ["US","CA","UK","AU","SG","PH"],
  "online_or_offline": "online",
  "legal_blocks": [],
  "skills_needed": ["writing","basic_english"],
  "assets_needed": ["laptop"],
  "risk_level": "low",
  "payback_days": 30,
  "recurring": true,
  "channel_ids": ["google-maps","nextdoor","walk-in"],
  "cost_breakdown": [
    {"item":"Domain + simple one-page site","amount":12},
    {"item":"Template pack (you write it once)","amount":0},
    {"item":"20 printed intro letters","amount":8},
    {"item":"First month of a mail tool","amount":15}
  ],
  "steps": [
    "Pick one street with 20+ independent shops",
    "Write 10 reply templates: thank-you, late order, bad review, wrong item",
    "Print 20 letters with one free sample reply each",
    "Walk in on a Tuesday morning, leave the letter, don't pitch",
    "Offer $49/month for up to 15 replies, first month free",
    "Deliver in 24 h by email — the whole job is 20 minutes",
    "Ask shop #1 for one introduction after week three"
  ],
  "pricing_hint": "$49/month for up to 15 replies",
  "first_customers": {
    "default": ["Google Maps 4-star shops with unanswered reviews"],
    "US": ["Google Maps 4-star shops with unanswered reviews","Nextdoor local business posts","Your own street, in person","Chamber of commerce newsletter"],
    "UK": ["Google Maps","Nextdoor","Local high street, in person"],
    "SG": ["Google Maps","Facebook local business groups","WhatsApp"],
    "PH": ["Google Maps","Facebook Marketplace groups","WhatsApp","Walk-in"]
  },
  "pitfalls": [
    "Don't sell AI writing — sell 'your reviews get answered by tomorrow'",
    "Don't take more than 25 clients before the template pack is done",
    "Check local rules on soliciting businesses in person"
  ],
  "compliance_note": {
    "default": "Check local business-name registration before invoicing.",
    "US": "US: check local business-name registration and sales-tax rules.",
    "UK": "UK: check HMRC self-registration before invoicing.",
    "SG": "SG: check ACRA registration requirements.",
    "PH": "PH: check BIR / barangay permit requirements."
  },
  "wave": "ai-llm",
  "trend_tags": ["ai","local-service","retainer"],
  "first_seen": "2026-11",
  "maturity": "growing",
  "version": 3,
  "updated_at": "2026-11-01",
  "status": "active"
}
```

## 8.3 按国家适配（同一 `id` 不复制整条，只挂变体）

| 国家 | 币种 | 典型 `first_customers` | 合规一句要点 | `legal_blocks` 常见原因 |
|---|---|---|---|---|
| US | USD `$` | Thumbtack / Etsy / Nextdoor / Google Maps / walk-in | sales tax、business name、上门揽客许可 | 部分州上门揽客许可 |
| CA | CAD `C$` | Google Maps / Kijiji / 本地商会 | GST/HST 注册 | — |
| UK | GBP `£` | Google Maps / Nextdoor / 高街当面 | HMRC self-registration | — |
| AU | AUD `A$` | Google Maps / Gumtree / 本地 Facebook 群 | ABN 注册 | — |
| SG | SGD `S$` | Google Maps / Facebook 商家群 / WhatsApp | ACRA 注册 | 部分需牌照的门类 |
| PH | PHP `₱` | Google Maps / Facebook Marketplace / WhatsApp / 上门 | BIR / barangay permit | 部分需 barangay 许可 |

- `min_capital` 以 USD 为基准存，渲染时按内置固定汇率表换算显示（汇率表随 baseline 冻结，不联网取）。
- 币种符号只影响 `cost_breakdown` 与 `pricing_hint` 展示，不影响打分。

## 8.4 `saved.json`

```json
{
  "schema": 1,
  "saved": [{"id":"us-svc-ai-014","saved_at":"2026-11-12"}],
  "last_answers": {
    "country":"US","capital":"500-2k","hours":"<10",
    "assets":["laptop"],"risk":"low"
  },
  "export_dir": "Documents/BizSpark",
  "library_version": "2026-11",
  "settings": {
    "country":"US","language":"en","monthly_check":true,
    "follow_system_theme":true,"crash_notes":false
  }
}
```

| 字段 | 校验 |
|---|---|
| `schema` | 整数，本期固定 1；读到更大值 → 只读不改、静默降级 |
| `saved[].id` | 必须存在于当前库；不存在则保留但不渲染卡片（库可能被 retire，不删用户记录） |
| `last_answers` | 允许部分缺失；只用于预填，不强制 |
| `export_dir` | 用户可改；每次写前检查可写性 |
| 写盘方式 | **临时文件 + 原子替换**，防止断电损坏 |

## 8.5 `manifest.json`（静态托管唯一入口）

```json
{ "latest": "2026-12", "files": ["delta_2026-12.json"], "size_kb": 18 }
```

| 字段 | 校验 |
|---|---|
| `latest` | `YYYY-MM`，必须 ≥ 本地 `library_version.txt` |
| `files` | 数组，只允许 `delta_YYYY-MM.json` 命名；不得含路径穿越字符 |
| `size_kb` | 仅用于展示，客户端下载后自行校验实际大小与 JSON 合法性 |

## 8.6 `delta_YYYY-MM.json`

```json
{
  "target_baseline": "v1",
  "release": "2026-12-01",
  "add":    [ { "id": "us-svc-bi-021", "wave": "bi-agent", "maturity": "emerging", "...": "..." } ],
  "revise": [ { "id": "us-svc-ai-014", "maturity": "growing", "version": 4 } ],
  "retire": [ "xx-legacy-003" ]
}
```

| 字段 | 规则 |
|---|---|
| `target_baseline` | 固定 `v1`；不匹配则拒绝合并并静默跳过 |
| `release` | 必须是当月 1 号 `YYYY-MM-01` |
| `add` | 完整 idea 对象，跑 §8.1 全量校验；`id` 不得与现有重复 |
| `revise` | 只含 `id` + 要改的字段；`version` 必须 +1；不允许改 `id` |
| `retire` | 只给 `id` 数组；**只把 `status` 置 `retired`，不从磁盘删除** |
| 缺失键 | 允许省略 `add/revise/retire` 任一，视为空数组 |
| 单包体积 | 建议 ≤100 KB；超过则拆月，不拆功能 |

## 8.7 `licence.dat`（分销版本地凭证，签名）

```json
{
  "code_hash": "sha256(…)",
  "device_hash": "sha256(hw_id + os_build)",
  "seats_used": 2,
  "seats_max": 3,
  "activated_at": "2026-11-12T21:40:00",
  "signature": "ed25519(…)"
}
```

- 本地校验签名，不回连；`seats_used` 由激活服务端在首次校验时返回并写入。
- 无用户名、无邮箱、无密码、无"欢迎回来"。

---

# 9. 匹配引擎算法规格（伪代码级）

## 9.1 输入 / 输出

```
INPUT  answers {country, capital, hours, assets[], risk}
       library : idea[]（本地 library.json，含已合并 delta）
       saved_ids : string[]（来自 saved.json）
OUTPUT results : [{id,title,one_liner,match_pct,why,tags[3]}]  // len ≤3
```

## 9.2 ① 硬过滤（不满足直接剔除，不参与打分）

```
function hard_filter(idea, a):
    if idea.status != "active":                       return DROP
    if a.country in idea.legal_blocks:                return DROP
    if a.country not in idea.countries:               return DROP
    if tier_rank(idea.capital_tier) > tier_rank(a.capital): return DROP
        // 用户资金档必须 >= 商机所需档；rank: 0-500<500-2k<2k-10k<10k+
    if hours_rank(idea.hours_per_week) > hours_rank(a.hours): return DROP
        // 所需时间不能超过用户可投入时间；rank: <10 < 10-25 < full
    if idea.maturity == "saturated":                  return DROP_FROM_TOP3  // 仍保留在库，见 9.5
    return KEEP
```

> `saturated` 的处理：不参与 Top 3 竞争，但**不删除、不报错**，可在 P08 时间线与库里存在。

## 9.3 ② 软打分（权重写死在客户端配置，不给用户调）

| # | 维度 | 权重 | 计算方式 |
|---|---|---|---|
| 1 | 资金贴合度 | **20%** | `1 - abs(idea.min_capital - tier_mid(a.capital)) / tier_mid(a.capital)`，截断到 [0,1] |
| 2 | 技能 / 资源匹配 | **20%** | `Jaccard(idea.assets_needed ∪ idea.skills_needed, a.assets ∪ inferred_skills)` |
| 3 | 时间匹配 | **15%** | `1 - abs(hours_rank(idea)-hours_rank(a.hours))/2` |
| 4 | 风险承受匹配 | **15%** | `1 - abs(risk_rank(idea.risk_level)-risk_rank(a.risk))/2` |
| 5 | 回本速度 | **10%** | `clamp(1 - idea.payback_days/180, 0, 1)` |
| 6 | 本地渠道可得性 | **10%** | `idea.first_customers[a.country]` 存在且非空 → 1；否则回退 `default` → 0.6 |
| 7 | **趋势新鲜度** | **5%** | `wave_rank(idea.wave)` 归一化 × `maturity_bonus`：emerging 1.0 / growing 0.8 / mature 0.5 |
| 8 | 复购型偏好 | **5%** | `idea.recurring ? 1 : 0.6` |

**两个辅助口径（写死，避免实现时各自发挥）：**

```
tier_mid(capital):  0-500 → 250 | 500-2k → 1250 | 2k-10k → 6000 | 10k+ → 15000
                    // 10k+ 无上限，固定取 15000 作代表值，不联网取汇率

inferred_skills(assets):  // 由 Q4 资源推断，映射表随客户端冻结
    car          → [driving, organizing]
    kitchen      → [cooking, organizing]
    laptop       → [writing, basic_english]
    spare_room   → [organizing]
    local_network→ [sales]
    tools        → [repair]
    none / []    → []
// 维度 2 的 Jaccard 集合 = idea.assets_needed ∪ idea.skills_needed
//                     对 a.assets ∪ inferred_skills(a.assets)
```

```
score(idea,a) = Σ(weight_i × normalized_i) × 100
match_pct     = clamp(round(score), 60, 97)   // 展示值，避免出现 100% 或过低难看值
```

> **趋势新鲜度只给 5%，锁死。** 用户要的是"他做得成的生意"，不是"最酷的技术"。禁止为了追 AI 浪潮把 Uber 司机硬塞 5 条 Agent 创业。`wave_rank`: mobile-internet 0.2 / ai-llm 0.6 / ai-agent 0.8 / bi-agent 1.0 / future 1.0。

## 9.4 ③ 降权与排序

```
for idea in kept:
    if idea.id in saved_ids: idea.score -= 15        // 已看过，别每次推同样三条
    idea.match_pct = clamp(round(idea.score), 60, 97)

kept.sort(key = (-score, id))                        // 同分按 id 字典序 → 结果确定性
results = kept[0:3]
```

## 9.5 ④ 降级（不足 3 条）

```
if len(results) < 3:
    relax hours_rank by +1 on hard_filter, recompute once
if len(results) still < 3:
    results = 实际 1–2 条
    P03.lead 追加一句 "Try a slightly bigger budget next time."
    // 绝不空白页、绝不"无结果"、绝不弹错
```

## 9.6 ⑤ Why 句生成（用户语言，不是系统语言）

```
why = "Why this fits you: " + join_nonempty([
    money_phrase(a.capital),        // "Low money" / "Fits $500–$2,000"
    asset_phrase(a.assets),         // "laptop only" / "you already have a car"
    time_phrase(a.hours),           // "under 10 hours a week"
    recurring_phrase(idea),         // "repeat monthly income"
]) + " — matches your budget and time."
```

- 只允许用**用户自己选过的具体词**拼句，不许出现 `算法 / 权重 / 推荐指数 / 智能匹配 / 模型`。
- 中文镜像等义替换，不另写一套修辞。

## 9.7 ⑥ tags[3] 固定规则

```
tags = [
  "From " + currency(a.country) + idea.min_capital,   // From $120
  hours_label(idea.hours_per_week),                    // <10 h/wk
  idea.recurring ? "Monthly" : (online ? "Online" : "Local")
]
```
> 第三标签在 P03 示例卡里允许按内容替换（如 `New wave` / `Weekend`），但**每卡必须恰好 3 个**。

## 9.8 性能与确定性

| 项 | 要求 |
|---|---|
| 硬过滤 | ≤80ms（312 条） |
| 打分 | ≤120ms |
| 降权 + 排序 + Why | ≤30ms |
| 端到端 Q5 → P03 | **≤300ms** |
| 确定性 | 同答案 + 同库 → 结果完全一致（同分按 `id`） |
| 网络 | **零请求** |
| 副作用 | 只写 `saved.json.last_answers`，不改库 |

## 9.9 算法禁止项

```
❌ 调用任何外部 API / 大模型
❌ 把用户答案序列化后出网
❌ 让用户调权重、看维度、选模式
❌ 输出 >3 条、给"查看更多"
❌ 因 trend 权重把低门槛本地生意挤出 Top 3
❌ 同分时结果随机漂移
```

---

# 10. 商机库内容规格

## 10.1 规模与分布（baseline v1.0 随包冻结）

| 项 | 值 |
|---|---|
| 总量 | **312 条**（在你定的 150–300 档上略放量，便于按 26 行业均分） |
| 行业 | **26 个** |
| 国家 | 6 国（US/CA/UK/AU/SG/PH） |
| 资金档 | 4 档（0-500 / 500-2k / 2k-10k / 10k+） |
| 时间档 | 3 档（<10 / 10-25 / full） |

**行业分布（避免全是 AI）**

| 大类 | 占比 | 条数（约） | 说明 |
|---|---|---|---|
| 本地服务 | 28% | 87 | 上门、代劳、清洁、维修、代办 |
| 线上副业 | 24% | 75 | 远程小服务、模板、精修、代运营 |
| B2B 小外包 | 18% | 56 | 给小店做账/图/评论/表单/预约 |
| 内容与数字产品 | 14% | 44 | 模板包、清单、小册、素材 |
| 手作与线下小生意 | 10% | 31 | 摊位、周末市集、本地食品 |
| **AI 与智能体相关** | **6%** | **19** | 用现成 AI 工具的低成本服务 |

> **纪律**：低门槛能上手的本地小生意永远占大头；AI 类是"跟上时代"，不是把库写成 AI 专区。

**资金档分布**（保证任何 Q2 答案都至少有 3 条可选）：`0-500` 40% / `500-2k` 32% / `2k-10k` 20% / `10k+` 8%。

## 10.2 26 个行业清单（建库索引）

```
01 家庭清洁   02 上门维修   03 宠物照看   04 园艺与庭院   05 洗车与车辆美容
06 搬运与跑腿 07 餐饮小摊   08 烘焙与家庭厨房 09 咖啡与饮品  10 手作与市集
11 二手转售   12 摄影与修图 13 商品图精修   14 短视频剪辑   15 文案与评论代回
16 表单与代办 17 预约与排班 18 记账与开票   19 店铺代运营   20 模板与清单包
21 素材与小册 22 在线小课   23 本地向导   24 设备租赁    25 AI 辅助服务
26 智能体照看/维护
```

## 10.3 内容质量红线（写不出就不入库）

每条商机必须能回答 **"明天早上第一步干什么"**。以下写法一律驳回：

```
❌ "做自媒体"      → 太空，不写第一步
❌ "开个网店"      → 没有具体品类与获客渠道
❌ "社交媒体推广"  → 不是渠道，是废话
❌ "适当投入"      → 必须逐项列钱
❌ "大概几千"      → 必须给 min_capital 与 cost_breakdown
❌ "注意合规"      → 必须给一句具体国家提示
❌ "利用 AI 赋能"  → 必须写清用哪个现成工具、交付什么
```

**合格判定**：`steps[0]` 必须是一个当天可执行的物理动作（Pick one street / Print 20 letters / Walk in Tuesday…）。

## 10.4 时代标签与换挡（对应你举的例子）

`wave` 枚举可累加、不按年份硬编码：

```
mobile-internet  →  ai-llm  →  ai-agent  →  bi-agent  →  future（留空位）
```

- **1 号是发布窗口，不是商机自动长出来**：2025 年 3 月 1 号库里出现 AI 商机，前提是你在 2 月把它们写进 3 月包，标 `wave: ai-llm, first_seen: 2025-03`；7 月 1 号出现商业智能体商机，标 `wave: bi-agent`。
- **换挡不是替换，是加权迁移**：新条目往上浮，老条目把 `maturity` 从 `emerging → growing → mature → saturated` 慢慢沉下去，**永不删除**。用户每次打开都觉得"这软件还活着、还跟得上"，但老点子仍在库里。
- **日历校准**：你用 2024→2025 打比方说明换挡，逻辑成立；按真实日历现在已是 **2026 年 11 月**，AI / 智能体商机是**当下存量而非未来**。所以 `baseline_v1.json` 必须**自带**那 19 条 `ai-llm / ai-agent / bi-agent` 条目，再从 **2026-12-01** 起按月换血。否则用户一打开就觉得工具落后两年。
- **趋势权重锁 5%**（§9.3），防止追浪潮追太狠。

## 10.5 每月你唯一的固定活儿（半天到一天）

```
① 挑 10–20 条新商机（跟当月技术/平台/季节变化）
② 按 §8.1 字段表填完，跑建库校验脚本
③ 把几条老条目标 maturity/version 修订，个别 status=retired
④ 打一次 delta_YYYY-MM.json + 更新 manifest.json
⑤ 传静态托管 → 完事
```

- 不额外向老用户收钱（买断制，说话算话）。
- 这是桌面图标不被删掉、用户做成第一单后还愿意回来找第二个点子的**唯一原因**，也是"代码能被抄、库抄不走"的那道墙。
- **两条纪律别破**：更新只做增强、绝不阻塞使用；别为了追浪潮把库写成 AI 专区。

## 10.6 建库校验脚本（开发需交付）

```
validate_library(baseline_v1.json)
  ✔ id 正则 + 全局唯一
  ✔ steps.length == 7、pitfalls.length == 3
  ✔ 枚举字段全部合法、受控词表无越界
  ✔ first_customers.default 非空、compliance_note.default 非空
  ✔ min_capital ≤ capital_tier 上限
  ✔ 每个 (country × capital_tier × hours) 组合至少有 3 条 active 且非 saturated
  ✔ steps[0] 是具体动作（人工抽检）
  ✘ 任一失败 → 拒绝打包，不进安装包
```

---

# 11. 存储、文件与命名规格

| 项 | 规则 |
|---|---|
| 编码 | 全部 UTF-8（无 BOM） |
| 格式 | JSON，2 空格缩进，便于你手工编辑 |
| 商机库文件 | `baseline_v1.json`（只读，随包）/ `library.json`（可写，首次启动复制生成） |
| 备份 | 每次 delta 合并前把 `library.json` 复制为 `library_backup.json`；合并失败自动回滚 |
| 写盘原子性 | 所有本地 JSON 写入采用「写 `.tmp` → fsync → 原子 rename」，禁止直接覆盖 |
| 版本文件 | `library_version.txt` 单行 `YYYY-MM` |
| 导出命名 | `BizSpark-Plan-{slug}.pdf`；`slug` = `title` 小写、非字母数字转 `-`、截断 40 字符、去尾连字符 |
| CSV 命名 | `BizSpark-Cost-{slug}.csv` |
| 默认导出目录 | `Documents/BizSpark/`（Mac/Win 各自用户文档目录） |
| 文件名不译 | 中文版导出的文件名**仍用英文 slug**，与英文版一致（便于你自己对照） |
| 日志 | 无常规日志；仅 `crash_notes=true` 时写 `crash.log`，内容只允许错误码 + 版本号，不含答案/点子/路径/设备名 |
| 清理 | 不自动删除任何用户文件；`retire` 只改状态不删数据 |
| 重装系统 | 用户数据丢失属预期，P09 隐私说明里写明；不提供云恢复 |

---

# 12. 导出规格（PDF / CSV 版式级）

## 12.1 PDF 单页版式

| 项 | 规格 |
|---|---|
| 页面 | A4（210×297mm）/ US Letter（216×279mm）自适应，按 `country` 选：US/CA 用 Letter，其余 A4 |
| 页边距 | 上下 16mm，左右 16mm |
| 字体 | Inter（或系统无衬线回退），正文 9.5pt，标题 17pt，区块标题 10.5pt 半粗 |
| 配色 | 纯黑白灰 + 一条 2pt 橘 `#F2653A` 顶部细线；**不印彩色大块**（省墨、可打印） |
| 页数 | **恰好 1 页**，内容溢出时按 §12.3 压缩，绝不自动翻第 2 页 |

## 12.2 块顺序（自上而下，写死）

```
1  顶部橘细线 + 右上角 "BizSpark · One-page plan"（9pt 灰）
2  标题：idea.title（17pt 粗）
3  one_liner（10pt 灰，1–2 行）
4  ── START-UP COST ──   cost_breakdown 逐行 + 合计（右对齐、合计加粗）
5  ── FIRST 7 STEPS ──   01–07 编号列表，每步 1 行
6  ── PRICING ──         pricing_hint + "Est. payback: {payback_days} days"
7  ── FIRST CUSTOMERS ── 按 country 取 first_customers，最多 4 条
8  ── WATCH OUT ──       3 条 pitfalls
9  ── LOCAL NOTE ──      compliance_note[country] 一句话
10 页脚： "BizSpark · one-time purchase · generated on this device"（8pt 灰）
```

## 12.3 溢出压缩顺序（保证恰好 1 页）

```
① 先压缩行距 1.35 → 1.2
② 再压缩渠道列表 4 条 → 3 条
③ 再把 steps 每步截断到 60 字符
④ 仍溢出 → 正文字号 9.5 → 9pt
⑤ 禁止：删区块、翻第 2 页、缩放成看不清
```

## 12.4 禁止出现在 PDF 里

```
❌ 水印 / 二维码 / 分享链接 / "分享给朋友"
❌ "升级解锁" / 订阅 / 续费 / 账号提示
❌ 用户答案原文（只输出方案，不输出问卷）
❌ 匹配度百分比 / 算法说明 / 权重
❌ 任何在线链接（它是磁盘文件，不是入口）
```

## 12.5 CSV（P1，可选）

| 列 | 来源 |
|---|---|
| `Item` | `cost_breakdown[].item` |
| `Amount` | `cost_breakdown[].amount` |
| `Currency` | 按 country 固定汇率表 |
| 末行 | `TOTAL` + 求和 |

UTF-8 + BOM（方便 Excel 直接打开）；文件名 `BizSpark-Cost-{slug}.csv`。

## 12.6 导出路径与异常

| 场景 | 处理 |
|---|---|
| 默认目录不存在 | 自动创建 |
| 目录不可写 / 磁盘满 | **仅**提示换一个文件夹，保留已渲染内容，不丢步骤 |
| 用户取消另存为 | 回到 P04，不跳 P05，不产生空文件 |
| 同名文件已存在 | 追加 `-2`、`-3`，不覆盖用户旧文件 |
| 断网 | 正常导出 |
| 中文版 | PDF 内文案随中文版，但文件名 slug 仍英文 |

---

# 13. 更新机制规格（时序、合并、失败矩阵、回滚）

## 13.1 触发条件

```
on_app_start (后台异步，不阻塞首屏):
    if 分销版未激活: 跳过更新检查（先走 P07）
    if 距上次检查 < 30 天: 跳过
    if 当月尚未发布过新版: 跳过
    GET manifest.json  (timeout 3s, 重试 0 次)
```

> **每月 1 号是发布窗口，不是检查窗口**：客户端是"启动距上次 >30 天就查一次"，不要求用户 1 号开机。

## 13.2 时序

```
T0   渲染 P01（用户此刻已可点）
T0+b GET manifest.json
T1   比对 latest > library_version ?
        ├ 否 → 结束，零 UI 变化
        └ 是 → GET delta_YYYY-MM.json（timeout 5s）
T2   校验 delta：JSON 合法 / target_baseline==v1 / release 是当月 1 号 / add 条目跑 §8.1 全校验
        └ 任一失败 → 静默跳过，记 last_check，不回滚（还没动过库）
T3   copy library.json → library_backup.json
T4   在内存副本上按顺序执行：add → revise → retire
T5   校验合并结果：id 唯一、总数合理、无非法枚举
        ├ 失败 → 丢弃内存副本，保留原库（备份可删），静默跳过
        └ 成功 → 原子写 library.json + 写 library_version.txt = latest
T6   若用户此刻恰好打开 P08 → 右下角展示一次轻 toast；否则零提示
```

## 13.3 合并算法（顺序写死）

```
for item in delta.add:
    assert item.id not in library
    assert validate(item)                        // §8.1 全量校验
    library.append(item)

for patch in delta.revise:
    target = find(patch.id)
    assert target and patch.version == target.version + 1
    assert "id" not in patch or patch.id == target.id
    target.update(patch)                         // 浅合并，只改给的字段

for rid in delta.retire:
    find(rid).status = "retired"                 // 只标状态，不删对象
```

## 13.4 失败矩阵（**全部静默**）

| # | 场景 | 客户端行为 | 用户感知 |
|---|---|---|---|
| E01 | 无网络 | 跳过 | 无 |
| E02 | manifest 3s 超时 | 跳过，记 last_check | 无 |
| E03 | manifest 404 / 托管到期 / **你忘续费** | 跳过 | 无 |
| E04 | manifest JSON 非法 | 跳过 | 无 |
| E05 | delta 下载 5s 超时 | 跳过 | 无 |
| E06 | delta 校验失败（字段不合法 / 基线不匹配） | 跳过 | 无 |
| E07 | 合并中崩溃 / 断电 | 下次启动从 `library_backup.json` 回滚 | 无 |
| E08 | 合并后校验失败 | 丢弃内存副本，原库不动 | 无 |
| E09 | 磁盘只读 | 跳过 | 无 |
| E10 | 用户断网一个月 | 完全无感；回来后一次性合并缺失的 delta | 无 |

> **统一禁令**：以上任何一项都**不弹窗、不 toast（除 P08 成功态）、不降级功能、不阻塞启动、不写红色日志**。

## 13.5 回滚

- 合并前必有 `library_backup.json`；合并成功后保留备份直到**下一次成功合并**才覆盖。
- 启动时若发现 `library.json` 非法而备份合法 → 自动用备份恢复，静默。
- 回滚不触碰 `saved.json`、不触碰已导出的 PDF。

## 13.6 换挡内容示例（对应 P08 时间线）

| 发布日 | add | revise | retire |
|---|---|---|---|
| baseline 2026-11 | 312 条（含 19 条 ai-llm/ai-agent/bi-agent） | — | — |
| 2026-12-01 | +14 条 `bi-agent`（本地小店智能体搭建/月维护/零代码照看） | 把 3 月那批 `ai-llm` 从 `emerging`→`growing` | 0–2 条平台关停的 |
| 2027-01-01 | +10–20 条当月新机会 | 老移动互联条目 `mature`→`saturated` | 政策变化条目 |

`saturated` 条目仍留在 `library.json`，只是不再进 Top 3。

## 13.7 与 F12 程序更新的隔离

| 项 | 库更新 F09 | 程序更新 F12 |
|---|---|---|
| 内容 | JSON 差量 | 新安装包 |
| Store 版 | 有 | 交给商店，客户端不写 |
| 分销版 | 有 | 静默提示"下次启动更新"，不强制 |
| 失败影响 | 只影响库新鲜度 | 只影响版本 |
| 互相依赖 | **无** | **无** |

---

# 14. 授权激活规格（码、指纹、凭证、席位）

## 14.1 渠道分流（写死）

| 渠道 | 客户端授权代码 | 用户看到 P07 吗 |
|---|---|---|
| Microsoft Store（付费下载） | **零** | 永不 |
| Mac App Store（付费下载） | **零**（StoreKit 由系统处理） | 永不 |
| Gumroad / Lemon Squeezy 等分销 | 轻量激活 | 仅未激活时一次 |

## 14.2 激活码格式

```
BZSP-K7Q2-M9XA-XXXX   （4 段 × 4 位，大写字母数字，去掉易混字符 0/O/1/I）
校验：本地先做格式正则 + 校验位，再联网一次做服务端核销
来源：分销平台付款成功页 / 收据邮件自动发放
```

## 14.3 设备指纹（禁止用 IP）

```
device_hash = sha256( platform_uuid OR machine_id
                    + os_build_major
                    + disk_serial_hash )
```

- 不含用户名、不含设备名、不含 MAC 明文、不含 IP。
- **禁止用 IP 绑定**：海外用户移动网络 / VPN / 换 Wi-Fi 是常态，用 IP 会误伤。
- 同一台机器重装系统若指纹变化 → 走"释放一个名额"人工处理，不判为盗版。

## 14.4 首次激活流程

```
S1 用户在 P07 输入码 → 本地格式校验
S2 POST /activate { code_hash, device_hash }   （唯一一次出网，timeout 8s）
S3 服务端：码是否存在 / 是否停用 / seats_used < seats_max
     ├ 是 → seats_used +=1，返回 {ok, seats_used, seats_max, signature}
     └ 否 → 返回 {ok:false, reason}
S4 客户端写 licence.dat（签名凭证）→ 跳 P01，此后不再回连
S5 失败 → 温和提示重试 / 联系支持，**禁止"授权失败"红字、禁止锁定软件**
```

## 14.5 离线保证

| 场景 | 行为 |
|---|---|
| 已激活后拔网线重启 | 校验本地签名 → 功能 100% 可用 |
| 已激活后服务器永久关停 | 用户一辈子无感 |
| 第 4 台设备 | 提示 `Changed computer? Release a seat`，引导释放，不报失败 |
| 换电脑 / 重装 | `Release a seat` 手动处理（首版邮件即可，**不做后台、不做账号**） |
| 激活码泄露被多人用 | 到 3 台上限后温和拒绝；Store 版不受影响 |

## 14.6 激活 ≠ 登录（UI 硬要求）

```
❌ 用户名 / 密码 / 邮箱 / "欢迎回来" / 头像 / 个人中心
❌ "登录以继续使用" / "会话已过期"
✅ 只有：4 格码框 + 设备位 + 一段绿 notice + 一个主按钮
```

P07 必须原样展示 5 条：`No subscription` / `No auto-renewal` / `No account, no email` / `Core features work offline` / `Library updates are free & optional`。

## 14.7 为什么还要码（文案口径）

> 安装包文件是可以被复制转发的。这个码只用来证明这份副本付过钱。**不是不信任用户，是文件本身能被转发。**

---

# 15. 设置规格（6 项逐项，封顶）

| # | 项 | 控件 | 取值 | 默认 | 影响范围 | 落盘 |
|---|---|---|---|---|---|---|
| 1 | `Country` | 下拉 | US/CA/UK/AU/SG/PH | 系统猜测或 US | 币种、`first_customers`、`compliance_note`、PDF 纸张 | `saved.json.settings.country` |
| 2 | `Language` | 下拉 | `en`（v1.0 仅英文；中文镜像是独立构建，不在软件内切换） | `en` | 无（占位展示） | `settings.language` |
| 3 | `Where plans are saved` | 路径选择 | 任意可写目录 | `Documents/BizSpark` | 导出默认路径 | `export_dir` |
| 4 | `Monthly library check` | 开关 | on/off | **on** | F09 是否执行 | `settings.monthly_check` |
| 5 | `Follow system appearance` | 开关 | on/off | **on** | 深浅色跟随，不闪白 | `settings.follow_system_theme` |
| 6 | `Anonymous crash notes` | 开关 | on/off | **off** | 仅写错误码+版本 | `settings.crash_notes` |

**规则**：
- 点击即生效，无"保存"按钮。
- 第 2 项**不是语言切换器**：软件内绝不许多出一个按钮；中文是独立构建产物。
- About 区固定 4 行：`Version 1.0.0` / `Library 2026.11 (312 ideas)` / `Licence One-time · activated` / `Account None`，加 `Check for updates` 与 `View licence` 两个弱按钮。
- 隐私卡一句话写死：`Your answers, your saved ideas and your exported plans never leave this device.`
- **禁止新增**：账号、通知、主题商店、高级设置、实验功能、数据上传开关、云同步开关。

---

# 16. 异常与降级总表

| # | 场景 | 行为 | 禁止 |
|---|---|---|---|
| X01 | 首次启动 / 无网 | 一切正常，用 baseline 库 | 联网提示 |
| X02 | 更新失败 / 托管挂了 / 忘续费 | 静默跳过，界面无任何变化 | 报错弹窗 |
| X03 | 匹配结果不足 3 条 | 放宽时间档一次 → 展示 1–2 条 + 温和一句 | 空白页 / "无结果" |
| X04 | `saved.json` 损坏 | 静默重建，不弹窗 | 数据恢复向导 |
| X05 | `library.json` 损坏 | 从备份或 baseline 恢复，静默 | 红色报错 |
| X06 | 商机字段缺失 | 兜底文案渲染 | 空白卡片 / 崩溃 |
| X07 | 导出路径不可写 / 磁盘满 | 仅提示换文件夹 | 丢已渲染内容 |
| X08 | 用户取消另存为 | 回 P04，不产生空文件 | 跳 P05 |
| X09 | 第 4 台设备激活 | 引导释放席位 | "授权失败"红字 |
| X10 | 系统深浅色切换 | 跟随，不闪白 | 重绘闪烁 |
| X11 | 断网一个月 | 完全无感，回来一次合并 | 补更提示 |
| X12 | 同名导出文件已存在 | 追加 `-2` | 覆盖用户旧文件 |
| X13 | 国家不在 6 国 | 默认 US | 询问 / 报错 |
| X14 | Q4 一个都不选 | 按"什么都没有"正常跑 | 必填校验 |
| X15 | 强制断电 | 原子写保证文件不损坏 | 半截 JSON |
| X16 | P08 恰好打开且合并成功 | 一次轻 toast | 弹窗 / 音效 |

**全局禁令（再强调）**：任何红色错误弹窗、任何"请检查网络后重试"、任何用户需要理解的报错码、任何阻断当前使用的强制动作。

---

# 17. 非功能需求

| 类别 | 指标 |
|---|---|
| 冷启动 | ≤1.5s 到可点击首屏 |
| 诊断 | Q5 → P03 ≤300ms（312 条、最低配笔记本） |
| 导出 | ≤2s 生成单页 PDF |
| 内存 | 常驻 ≤300MB |
| 包体 | Windows ≤120MB / Mac ≤120MB（Tauri 可压到 40MB 内） |
| 离线 | 飞行模式可完整跑通「答题 → 3 条 → PDF」 |
| 出网 | 白名单 3 项（§4.6），零用户数据 |
| 隐私 | 答案 / 点子 / 导出文件 / 文件路径不出设备 |
| 崩溃日志 | 默认关；开启后仅错误码 + 版本号 |
| 可访问性 | 键盘可操作、文字对比度 ≥4.5:1、系统字号跟随 |
| 确定性 | 同答案 + 同库 → 同结果 |
| 原子性 | 所有本地 JSON 写盘用临时文件 + 原子替换 |
| 兼容性 | Windows 10 1809+ / macOS 11+；不要求用户装 Python 或任何运行时 |
| 沙盒 | Mac App Store 版需声明文件读写（用户选定目录）与网络出站权限 |

---

# 18. 双版本纪律（英文为主，中文为镜）

## 18.1 主次

**产品只有一个版本，就是英文版。** 它直接面对海外用户，上架 Microsoft Store / Mac App Store / 分销平台，商品页、截图、评论、收据全是英文。

中文版存在的唯一理由：**自己先看得明白、用得熟练，才讲得清楚、才卖得动。** 连自己都没跑通那 5 道题、没导出过那张纸，就没法判断海外用户会在哪一步犹豫。中文版是给自己用的自检副本，不是第二条产品线，也不是"国内版"。

> 与 C01「只做海外、不做中文售卖页」不冲突：中文版**不对外分发、不上架、不出现在任何商品页素材里**，只在自己电脑上跑。

## 18.2 施工口径（已按此完成）

| 项 | 处理 |
|---|---|
| 页面 / 文件 | 9 个，文件名与英文版完全一致，一一对应 |
| 结构 | HTML 标签、class、id、层级、栅格 **100% 不动** |
| 样式 | `assets/style.css` 是英文版那一份的**原样拷贝**，一个字节都不改 |
| 视觉 | 配色、留白、圆角、阴影、字号、深色欢迎页、橘色主 CTA、倾斜纸片预览，全部不变 |
| 字体 | 拉丁仍走 Inter，中文由系统 CJK 回退；**不换中式字体、不加中国红/金/纹样/印章** |
| 交互 | 选中即进下一题、卡片跳转、开关、toast，全部一致 |
| 内容 | **只替换界面上可见的文字**（导航、面包屑、按钮、标签、提示、时间线、隐私说明） |
| 不译 | `BizSpark`、`Microsoft Store`、`Mac App Store`、`PDF`、`CSV`、Google Maps / Yelp / Etsy / Shopify / Nextdoor、激活码样例 `BZSP-K7Q2-M9XA`、文件名、版本号、`AI` |

> 中文版要长得像**"英文版换了行字"**，不能长得像"一个中国软件"。因为你要练的，正是海外用户将来看到的那个东西。

## 18.3 同步纪律

1. 任何改动——文案、字段、按钮、页面、配色——**先改英文版**。
2. 再把同一处改动**逐字镜像**到中文版，只换字，不换结构。
3. 两版同时重新出 9 张截图与总览图，逐页比对。
4. **中文版禁止**：单独加功能、单独调布局、单独改按钮位置、单独加"切换语言"入口、单独做第三语言、单独先进化到 v1.1。
5. 出现分歧，**以英文版为准**。

## 18.4 中文版明确不做

```
❌ 语种切换按钮（软件里一个按钮都不许多）
❌ 中文商品页 / 中文落地页 / 国内售卖入口
❌ 中文截图进商店素材
❌ 因中文改字体风格、加中式装饰
❌ 中文版单独打包对外发
❌ 因"中文看起来字少"就顺手挪版式
```

## 18.5 交付物

```
en/html/   9 页英文售卖版（唯一验收基线）
en/ui/     9 张英文界面截图
cn/html/   9 页中文自检镜像版（仅文案替换）
cn/ui/     9 张中文界面截图
UI总览图_英文版.png / UI总览图_中文版.png
```

---

# 19. 验收测试用例（TC-001 – TC-052）

## A. 启动与首屏

| ID | 步骤 | 预期 |
|---|---|---|
| TC-001 | 冷启动 | ≤1.5s 出 P01，且 1440×900 一屏无滚动 |
| TC-002 | 冷启动 | 无权限弹窗、无联网确认、无广告、无教程 |
| TC-003 | 删除 `saved.json` 后启动 | 静默重建，功能正常，无弹窗 |
| TC-004 | 把 `saved.json` 写成非法 JSON 后启动 | 静默重建，不崩溃 |
| TC-005 | 系统区域设为 `FR` 后启动 | 问卷默认 US，不询问、不报错 |
| TC-006 | 飞行模式冷启动 | 与联网状态完全一致 |

## B. 问卷

| ID | 步骤 | 预期 |
|---|---|---|
| TC-007 | 点 P01 主 CTA | 进 Q1，进度第 1 点亮橘 |
| TC-008 | Q1 选 UK | 0.35s 自动进 Q2，第 1 点转绿 |
| TC-009 | Q2 未选直接看主按钮 | 主按钮置灰，无校验弹窗 |
| TC-010 | Q2 连点两档 | 以最后一次为准，只跳一次页 |
| TC-011 | Q3 选 `<10h` | 自动进 Q4 |
| TC-012 | Q4 一个都不选点 Done | 按 `assets=[]` 正常进 Q5 |
| TC-013 | Q4 选 3 项再取消 1 项 | 最终记录 2 项 |
| TC-014 | 任意题点 `← Back` | 回上一题且已选答案高亮保留 |
| TC-015 | 全程计数 | 核心决策点击 ≤8 次，无键盘输入 |
| TC-016 | 断网跑完 5 题 | 与联网完全一致 |

## C. 匹配引擎

| ID | 步骤 | 预期 |
|---|---|---|
| TC-017 | 标准答案跑完 Q5 | ≤300ms 出 P03，恰好 3 张卡 |
| TC-018 | 抓包 | 全流程**零网络请求** |
| TC-019 | 同一答案连跑 3 次 | 3 次结果完全一致（确定性） |
| TC-020 | 构造资金档 `10k+` 但库里该档仅 2 条 | 放宽时间档一次后仍不足 → 显示实际条数 + 温和一句，**无空白页** |
| TC-021 | 把某条标 `saturated` | 不进 Top 3，但仍在库、不删除 |
| TC-022 | 先保存 3 条再重跑同答案 | 已看过 `id` 降权，Top 3 发生变化 |
| TC-023 | 检查趋势权重 | 固定 5%，低门槛本地生意仍占 Top 3 多数 |
| TC-024 | `first_customers` 无 SG 变体 | 回退 `default`，不报错 |

## D. 结果 / 详情

| ID | 步骤 | 预期 |
|---|---|---|
| TC-025 | 看 P03 | 每卡恰好 7 元素、3 个标签、只有 1 个主按钮 |
| TC-026 | 找筛选器 / 排序 / 分页 / "查看更多" | 全部不存在 |
| TC-027 | 点第 1 张卡 | 进 P04，右侧纸片预览 sticky 常驻 |
| TC-028 | 滚动 P04 到中部 | 右侧预览仍可见 |
| TC-029 | 把某条 `steps` 改成 6 项后打包 | 建库校验拒绝打包 |
| TC-030 | 把某条 `pitfalls` 改成 2 项后打包 | 建库校验拒绝打包 |
| TC-031 | 删除某条 `compliance_note` 后运行 | 兜底文案渲染，不空白、不崩溃 |
| TC-032 | 全页搜索 | 无 `算法/权重/版本检测/同步中/服务器/云端/模型/API` 字样 |

## E. 导出

| ID | 步骤 | 预期 |
|---|---|---|
| TC-033 | 点导出 | 弹系统原生另存为，默认 `Documents/BizSpark` |
| TC-034 | 确认保存 | ≤2s 生成 PDF，跳 P05，文件名符合 slug 规则 |
| TC-035 | 打开 PDF | **恰好 1 页**，A4/Letter 按国家正确，块顺序符合 §12.2 |
| TC-036 | 检查 PDF | 无水印 / 无二维码 / 无链接 / 无订阅字样 / 无用户答案原文 |
| TC-037 | 长内容条目导出 | 按 §12.3 压缩，仍恰好 1 页，不删区块 |
| TC-038 | 目标目录设为只读 | 仅提示换文件夹，已渲染内容不丢 |
| TC-039 | 在另存为点取消 | 回 P04，不产生空文件、不跳 P05 |
| TC-040 | 同名文件已存在再导一次 | 生成 `-2`，不覆盖旧文件 |
| TC-041 | 飞行模式导出 | 成功 |
| TC-042 | 点 `Open folder` | 系统文件管理器定位到该 PDF |

## F. 存档 / 设置 / 激活 / 更新

| ID | 步骤 | 预期 |
|---|---|---|
| TC-043 | 保存 → 关闭 → 重开 → 看 P06 | 3 条仍在，日期正确，重复保存不新增 |
| TC-044 | 点 `Clear saved list` | 出现**全系统唯一**二次确认；确认后清空 |
| TC-045 | P09 数旋钮 | 恰好 6 项，无"保存"按钮，无语言切换器 |
| TC-046 | 分销版首次输入正确码 | 一次联网校验 → 写 `licence.dat` → 跳 P01 |
| TC-047 | 已激活后拔网线重启 | 功能 100% 可用，零回连 |
| TC-048 | 关掉静态托管一整天 / 构造 §13.4 E01–E10 | 启动与功能**无任何变化**，无弹窗、无 toast、无降级 |

## G. 双版与上架

| ID | 步骤 | 预期 |
|---|---|---|
| TC-049 | 比对两版 CSS | 字节级完全一致 |
| TC-050 | 比对两版 9 个文件名 / 结构 / 控件 | 一一对应，中文版无界面英文残留（专有名词除外） |
| TC-051 | 商品页与软件内全文搜索 | 找不到肯定式的订阅/自动续费/登录/云服务字样 |
| TC-052 | 商店审核模拟 | 交付真实安装包 + 本地引擎 + 离线能力，非 WebView 空壳 |

---

# 20. 上架与渠道材料清单

| 项 | Microsoft Store | Mac App Store | Gumroad / Lemon Squeezy |
|---|---|---|---|
| 产物 | MSIX（Win32/打包应用） | 签名 `.app` | `.exe` / `.dmg` 安装包 |
| 收款 | 平台 | 平台 | 平台 |
| 软件内授权码 | **不做** | **不做** | 做，限 3 台 |
| 退款 | 平台规则 | 平台规则 | 平台规则 |
| 开发者账号 | 个人/公司开发者账号 | Apple Developer Program | 平台卖家账号 |
| 商品页文案 | `One-time purchase` / `No subscription` / `No auto-renewal` / `Works offline` / `Your data stays on this device` / `No account required` | 同左 | 同左 + 激活码交付说明 |
| 截图 | 直接用 `en/ui/` 那 9 张（挑 5–6 张） | 同左 | 同左 |
| 隐私政策 | 一页（照 §15 隐私卡扩写） | 同左 + 沙盒权限说明 | 同左 |
| 支持邮箱 | 必填 | 必填 | 必填 |
| 年龄分级 / 分类 | 工具 / 商务 | 工具 / 商务 | 自行填 |
| 激活码交付 | 无 | 无 | 平台自动发码（收据邮件） |

**资质口径（起步阶段）**：只卖海外、服务器在境外、无国内售卖页与国内支付 → 不办国内 ICP 经营性许可、不做国内 App 备案、不接微信/支付宝商户号；公司正常记账报税，跨境软件收入**单独建账**，让代账会计按"软件出口/跨境服务"处理增值税口径；软著后续想办再补，不阻塞上架。海外侧准备：隐私政策一页、符合平台规则的退款说明、Apple / Microsoft 商店条款确认。

---

# 21. 排期、人日估算与交付物

## 21.1 六周 MVP（一个人可完成）

| 周 | 交付 | 人日 |
|---|---|---|
| W1 | 定稿 312 条字段与 baseline 数据（含建库校验脚本）；搭 Tauri/Electron 壳；9 页 UI 静态实现对齐 `en/html/` | 6 |
| W2 | F02 问卷（5 题 + 自动进题 + Back）+ F03 本地引擎（硬过滤/打分/降权/降级）+ F04 结果页 | 6 |
| W3 | F05 详情页（6 模块 + sticky 预览）+ F06 本地 PDF/CSV 导出 + F07 本地存档 | 6 |
| W4 | F09 静默更新（manifest/delta/备份/回滚）+ F10 分销版激活 + F13 全部降级路径 | 5 |
| W5 | 双端打包、签名、商店材料、隐私政策、中文镜像版逐页校对 | 5 |
| W6 | 上架 + 首批真实付费观察 + 按 §19 跑一遍全量测试用例 | 4 |
| **合计** | | **约 32 人日** |

## 21.2 开发必须交付的文件

```
① Windows MSIX + exe、Mac 签名 app/dmg
② 源码（Vue3 前端 + 本地引擎 + 打包脚本）
③ baseline_v1.json（312 条，已过校验）
④ validate_library 脚本（§10.6）
⑤ manifest.json + delta_2026-12.json（模板）
⑥ 隐私政策一页（英）
⑦ 商品页文案（英）
⑧ 中文镜像构建产物（cn/html、cn/ui）
⑨ 本规格书 §19 测试执行记录
```

## 21.3 上线验收（一条链路定生死）

1. 飞行模式下：双击 → 5 题 → 3 条 → 导出 PDF → 关闭，全程无报错、无联网请求。
2. 把静态托管关掉一整天：软件启动与功能无任何变化。
3. 首次到 PDF ≤3 分钟，核心决策点击 ≤8 次。
4. UI 与 `en/html/` 逐页比对，偏差 ≤2px 级别观感；中文版逐页核对无溢出、无方块字。
5. 商品页与软件内找不到肯定式的"订阅/自动续费/登录/云服务"字样。

**验证关**：首批 ≥30 个真实付费用户、商品页→购买转化率 ≥3%，再考虑第二端与增值。

---

# 22. 待决事项与变更记录

## 22.1 待决（不阻塞开发，上架前定即可）

| # | 事项 | 建议默认值 |
|---|---|---|
| D01 | 产品最终定名（BizSpark 是否做商标检索） | 暂用 BizSpark，上架前查目标国商标 |
| D02 | 6 国之外何时扩 | 验证关过了再扩，每次 +3–5 国 |
| D03 | PDF 内固定汇率表数值 | 随 baseline 冻结，标注"估算" |
| D04 | 分销平台优先选哪家 | 先用抽成低、能自动发码的 |
| D05 | 第二版"用户自带 API Key"是否做 | 本期一行不做，验证后再评估 |

## 22.2 变更记录

| 版本 | 日期 | 变更 |
|---|---|---|
| V1.0 | 2026-11-12 | 首版产品需求文档；14 组功能、数据结构、上架、排期 |
| V1.1 | 2026-11-12 | 新增 §11 双版本纪律（英文为主、中文为镜）；更新头部语言与交付口径 |
| **V2.0** | **2026-11-12** | **重写为开发实现级规格书**：新增 §5 逐步链路 S01–S32、§6 九页元素级清单（含中英文案原文）、§8 全字段数据字典与校验、§9 匹配引擎伪代码、§10 内容质量红线与建库校验、§11 存储原子性、§12 PDF 版式与溢出压缩、§13 更新时序/失败矩阵/回滚、§14 激活码与设备指纹、§15 六项设置逐项、§16 异常总表、§19 52 条测试用例、§21 人日估算。商业约束一字未改 |

---

## 附：一句话总纲

---

## 价格配置契约（价格写活，不写死）

> 商品价格随行就市，**是发布参数，不是产品属性**。当前那个定价只是想法，**不得写进任何文件、UI 图、HTML 页面、需求文档或商品文案**。第一版只讲功能，不出现金额。

### 一、第一版：分成销售，客户端不出现价格

Microsoft Store / Mac App Store 付费下载的**售价在 Partner Center / App Store Connect 后台设置**，改价即时生效、不需要重新发版。客户端、静态页、需求文档、UI 截图、商品页文案**只讲功能与购买模式**（`One-time purchase` / `No subscription` / `No auto-renewal`），**一律不出现金额**。

> 这正好是「价格可设置」最省事的形态：**价格本来就不在软件里，在商店后台。**

### 二、唯一价格源

| 层 | 文件 | 说明 |
|---|---|---|
| 静态 HTML 交付 | `assets/pricing.js` | `window.BIZSPARK_PRICING`，改一处、中英两版 18 页全生效 |
| 工程客户端 | `config/pricing.json` + `locales` 的 `price.*` 键 | 构建期注入，运行时只读 |
| 商店售价 | Partner Center / App Store Connect 后台 | 分成销售的实际价格，**不进客户端** |

```json
{
  "display_mode": "hidden",
  "amount": null,
  "currency": "USD",
  "model": "one-time",
  "billing_note": null
}
```

| 字段 | 取值 | 首版 |
|---|---|---|
| `display_mode` | `hidden` / `visible` | `hidden` |
| `amount` | 数字，仅 `visible` 时填写 | `null` |
| `currency` | ISO 4217 | `USD` |
| `model` | `one-time` / `monthly` / `yearly` / `seat` | `one-time` |
| `billing_note` | 可选，如 `per month` | `null` |

**首版配置里没有任何金额；渲染器里也没有写死任何数字——`visible` 时的金额完全由 `amount` 动态生成。**

### 三、三条硬规矩

1. **零硬编码**：全项目（md / docx / HTML / CSS / JS / 截图 / 商品文案）不得出现任何商品售价数字；价格只能由配置渲染。CI 加金额门禁（T-59）。
2. **首版 hidden**：价格占位渲染为纯功能 / 模式文案（如 `One-time purchase · Yours forever`），不渲染数字、不渲染空价格框、**不新增任何用户可见控件**。
3. **后期显示只改配置**：做授权码、包月、包年、订阅制时，把 `display_mode` 改为 `visible`、填 `amount` 与 `model`，一处改动，客户端 / 静态页 / 商品文案同时生效；**仍不加「改价」界面**，界面永远做小。

### 四、边界说明（别误删内容）

商机库里的**起步成本、定价建议、回本金额**（如 `From $120`、`$49/month`）是**内容数据**，不是本商品售价，不受本契约约束，必须保留。门禁只扫描商品售价，不扫描商机内容。

### 五、谁负责

| 人 | 任务 |
|---|---|
| A | `config/pricing.json` 落库、构建期注入、CI 金额门禁脚本、六构建目标共用同一配置 |
| B | `[data-price-slot]` 占位 + `price-render.js` 渲染器；`locales` 增 `price.*` 键（键名不含金额） |
| H | T-59：全项目零金额扫描 + 改 `display_mode` 后两版 9 屏回归 |
| G | 审商品页文案：只写功能与购买模式，不写金额 |

---

> **界面做小，后台做厚；用户那头越轻，你这头越值钱。卖的不是功能，是"我替你想完了"。**
