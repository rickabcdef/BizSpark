# 安全与合规审查（G-06 / G-07 / G-08）

> 审查人：程序员 G　日期：2026-11-13　范围：授权链路、Tauri 权限、错误码外露、隐私、商品页文案、Store 裁剪
> 结论：**可放行**（授权链路 P0 用例 T-41…T-45 全部通过），但有 **4 项需他人跟进**（见 §8）。
> 签收：H（QA）____________　日期：______

---

## 1. 授权实现与安全模型

| 层 | 做法 | 为什么这么做 |
|---|---|---|
| 码格式 | `BZSP-XXXX-XXXX-XXXX`，12 位取自 32 字符表（去 0/O/1/I/L），60 bit | 用户手抄/口述不出错；熵够大但**不假装是密码学强度** |
| 码真伪 | 码池 `pool.json` 里每枚码带一枚 **Ed25519 背书签名**（对 `serial + seats_max`） | 16 字符放不下 64 字节签名，所以"码池"是必需的：码只是索引，签名证明它被签发过 |
| 码池完整性 | 整个池子再签一次名，客户端**只内置公钥** | 否则任何人替换 `pool.json` 就能自造码 |
| 凭证 | `license.dat` 存 `code_hash / device_hash / seats / seats_max / signed_at / sig`，`sig` 即该码的背书 | §3.5 字段齐全；`sig` 可在**没有码**的情况下离线复验 |
| 席位 | 3 席位 + 同机幂等 + 第 4 台温和引导 | T-41…T-44 |
| 启动校验 | 只读本地文件 + 内置公钥验签，**零出网** | T-45；比需求更严：需求允许"首次激活联网"，实现选择全离线 |

实现位置：`apps/core/license/{ed25519,signature,device,activate}.py`；
签发工具：`tools/issue.py`（**不进包**，私钥在 `%APPDATA%/BizSpark-issuer/issuer.key`，权限 600）。

### 1.1 密钥边界（逐条核对）

| 检查 | 结果 |
|---|---|
| 客户端包内含私钥？ | **否**。`signature.py` 只有 `PUBKEY_HEX`；`tools/` 不参与打包（§7 有校验脚本） |
| 私钥能否通过环境变量注入绕过？ | **否**。公钥只在模块常量里，代码中**不读任何环境变量改公钥**（单测用 `set_public_key()` 进程内注入，不落盘） |
| 签发工具是否可能被误打包？ | 打包脚本需显式排除 `tools/`（A 的 `pack.sh`，见 §8-A2） |

### 1.2 已知限制（写清楚，不粉饰）

1. **席位是"协同约束"不是"强防"**：产品承诺永久离线、不心跳，因此没有服务端能强制席位。
   用户若逆向 Python 包并改 `seats` 数组，本地只能靠 `local_tag`（HMAC，密钥由该码的背书签名派生）
   提高门槛——它能挡住"用记事本改文件"，挡不住"读懂代码后重算"。这是离线产品的固有代价，
   已在产品文案里用"激活不是登录"如实告知。
2. **码空间 60 bit**：能抵抗在线撞码（本来也没有在线校验），但不抵抗本地穷举 + 自建码池
   （需要一个能签名的私钥，等于不能伪造）。真正的防线是 Ed25519 签名，不是码的长度。
3. **换系统盘会掉一个席位**：卷序列号进指纹（规范如此）。已在 `docs/fingerprint-spec.md` §6
   写明用户口径：换电脑 → 占第 2、3 个位；第 4 台 → 人工释放。

---

## 2. Tauri 权限审查（`apps/desktop/src-tauri/capabilities/default.json`）

| 权限 | 必要性 | 结论 |
|---|---|---|
| `core:default` | 基础运行时 | 保留 |
| `core:window:allow-close` / `allow-minimize` | 自绘标题栏按钮 | 保留 |
| `core:window:allow-set-title` | 页面标题随路由变化 | 保留 |
| `core:event:default` | 前端 ↔ Rust 事件（sidecar 转发） | 保留 |
| `dialog:allow-save` | P-02：导出必须经系统"另存为" | **必须保留**，不许换成自拼路径 |
| `dialog:allow-open` | 选导出目录 / macOS Powerbox | 保留 |

**未申请（正确）**：`fs:*`（读写全由 sidecar 做）、`shell:*`（sidecar 由 Rust 启动，不进前端）、
`http:*` / `net:*`（前端零网络，月度 manifest 由 Rust 发一次）、`process:*`、`dialog:allow-message`
（不许弹系统弹窗——错误一律静默）。

### 2.1 发现 P2：CSP 为 `null`

`tauri.conf.json` 里 `app.security.csp = null`，等于关闭内容安全策略。当前前端零外部资源
（无 CDN、无外链字体），所以**风险可用但不该留着**。建议 A 改为：

```
"csp": "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'none'; frame-src 'none'; object-src 'none'"
```

`style-src` 保留 `'unsafe-inline'` 是因为 Vue 的 scoped style 与内联样式；`connect-src 'none'`
把"前端不许发网络请求"写进策略层（比口头约定硬）。

---

## 3. 错误码外露审查

规则（§2.6）：错误码**只在 Python/Rust 层**，前端默认不展示；只有 3 类允许温和提示
（导出目录不可写、结果不足 3 条、第 4 台设备）。

| 错误码 | 产生处 | 前端是否展示 | 本模块的文案 |
|---|---|---|---|
| `E_LICENSE_BAD_CODE` | `activate` | 否（输入框下一行温和提示由 B 决定） | "This code doesn't match any copy. Check the receipt email and try again." |
| `E_LICENSE_SEAT_FULL` | `activate` | **是**（引导 `Changed computer? Release a seat`） | 含 `Release a seat` 提示，**不含 fail/error/授权失败**（单测逐词断言） |
| `E_UNKNOWN_CMD` | Store 构建（`license` 被裁） | 否 | — |

**发现 P3**：`main.handle` 兜底把异常文本原样放进 `E_INTERNAL.message`（`str(exc)`），
`OSError` 会带**绝对路径**（如 `C:\Users\<名>\...`）。目前前端不展示错误消息，风险低；
但一旦有人把日志贴到 issue 区就泄露用户名。建议 C（`main.py` 属主）改为：

```python
"message": "internal error (code only)"   # 细节只写本地 crash 日志（F 的白名单）时也不带路径
```

G 自己的三个 handler 已核对：**不返回路径、不返回指纹原文、不返回码明文**。

---

## 4. 隐私审查

| 项 | 结论 | 依据 |
|---|---|---|
| 激活链路出网 | **0 次** | 单测 `test_no_network` 把 `socket.socket` 换成抛异常的桩，激活/查询/释放全流程照常完成；静态检查源码无 `socket/urllib/requests/http` |
| 采集的机器信息 | 平台标签 + MachineGuid/IOPlatformUUID/machine-id + CPU 型号 + 卷序列号 + 主板型号 | `docs/fingerprint-spec.md`；**无 IP / MAC / 用户名 / 主机名 / 路径** |
| 原始信息是否落盘 | **否**，只落 sha256；`device.py` 不回传原始值 | 代码审查 |
| `license.dat` 内容 | 码的哈希、设备哈希、席位时间、签名 | 无邮箱、无姓名、无支付信息（平台侧才有） |
| 崩溃日志 | 默认关；开启后只写 `ts/code/version` | F 的 `settings.py`（本次复核未发现越界字段） |
| 遥测/统计 | **无** | 全仓库无第三方 SDK |

隐私政策一页（H 备料）建议直接引用本表的三条：不收集、不出网、只留本地签名文件。

---

## 5. 商品页合规文案（§10 五条必写）

| 必写内容 | 应用内落点（已核对） | 上架素材 |
|---|---|---|
| `One-time purchase` | `side.badge`、`price.hero_trust_hidden` | **待 H 写入 listing** |
| `No subscription` | `side.badge`、`activate.f1` | 同上 |
| `No auto-renewal` | `activate.f2` | 同上 |
| `Works offline` | `welcome.offline`、`activate.h1/f4`、`settings.privacy_p` | 同上 |
| `Your data stays on this device` | `side.chip`、`welcome.never_leave`、`quiz.note1_h` | 同上 |

分销平台（Gumroad / Lemon Squeezy）额外必写**激活码交付说明**：付款后收据邮件含码、
一码 3 台、离线可用、换机人工释放（`support@bizspark.app`）。

**发现 P3**：`qa/store-assets/` 目前为空，五条与截图都还没有落地文件 → **H 补齐**（G 已给出逐条对应关系）。
另：`support@bizspark.app` 是占位邮箱，**上架前必须替换为真实可收信邮箱**（`activate.py: SUPPORT_EMAIL`）。

---

## 6. 激活页文案逐字核对（G-08）

对照 `ui/en/html/07-activate.html`，`apps/web/src/locales/en-US.json` 的 18 个 `activate.*` 键
**逐字一致**（脚本 `qa/security/copy_check.py` 可复跑）；`zh-CN.json` 键集合相同、值中文镜像，
不译白名单（BizSpark / PDF / CSV / 版本号）保持原样。

核对要点：
- eyebrow `For copies bought outside the stores` ✓
- H1 `Activate once. Use offline.` ✓
- 席位提示 `One code works on up to 3 of your own devices.` ✓
- notice 全文（`Activation is not a login. …we never check again.`）✓
- 深墨蓝卡 5 条 ✓；`Why a code at all?` 正文 ✓；主按钮 `Activate & start` ✓；释放按钮 `Changed computer? Release a seat` ✓

---

## 7. Store 构建编译期裁剪（G-07 / T-42）

**做法**：Store 构建打包 sidecar 时**整目录排除 `apps/core/license/`**；`main.py` 的导入写在
`try/except` 里 → 裁剪后三个授权 cmd 不存在（回 `E_UNKNOWN_CMD`），进程不崩、其余功能不受影响。

**可执行校验**：`python qa/security/store_strip_check.py`
- 复制 `apps/core` 到临时目录并删掉 `license/`，跑 sidecar；
- 断言：`ping`/`diagnose`/`get_state` 正常，`activate`/`license_status`/`release_seat` → `E_UNKNOWN_CMD`；
- 静态断言：`main.py` 的 `license` 导入位于 `try/except` 内；除 `license/` 外没有任何模块 import 它。

**发现 P2（需 A+B）**：前端产物里仍有 `Activate.vue` 与 `/activate` 路由。T-42 的要求是
"包内检索不到 `activate` / `license` 相关代码路径"，所以 `build:store` 还需：
1. 路由表按 `build-mode` 裁掉 `/activate`（B）；
2. `npm run build:store` 时不打包该视图（rollup 的 `define` + 动态 import 条件）；
3. A 在 `pack.sh` 里对 MSIX 产物做一次 `grep -ri "activate\|license\.dat"` 断言（失败即中止）。

---

## 8. 需他人跟进（按优先级）

| # | 事项 | 谁 | 优先级 |
|---|---|---|---|
| A1 | `fingerprint.rs` 对齐 `docs/fingerprint-spec.md`（现仅 MachineGuid）；对齐前**不要**注入 `BIZSPARK_DEVICE_HASH` | A | P1（否则同机两套指纹、席位重复占用） |
| A2 | `pack.sh` 排除 `tools/`、排除 `apps/core/license/`（Store），并对产物做 `grep` 断言 | A | P0（T-42） |
| A3 | `tauri.conf.json` 设置 CSP（§2.1 建议串） | A | P2 |
| B1 | `build:store` 裁掉 `/activate` 路由与视图 | B | P1（T-42 前端侧） |
| C1 | `E_INTERNAL.message` 去掉 `str(exc)`（含绝对路径） | C | P3 |
| H1 | 填 `qa/store-assets/`：五条必写 + 英文截图 + 隐私政策一页 | H | P0（上架阻塞） |
| 运营 | `SUPPORT_EMAIL` 换成真实邮箱；发布前重新 `keygen` + `new-pool`（正式池 demo=false） | 运营/G | P0（上架阻塞） |

## 9. 发布前 preflight（G 负责跑）

```
python qa/security/store_strip_check.py     # T-42：Store 裁剪不崩、cmd 消失
python qa/security/copy_check.py            # G-08：激活页文案逐字一致
python qa/security/release_preflight.py     # 发布池 demo=false、无明文码、无私钥、公钥非零
python tools/issue.py verify                # 码池签名与每条背书
python -m unittest discover -s apps/core/tests -p "test_*.py"
```
