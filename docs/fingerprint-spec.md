# 机器指纹规范 v1（G-01）

> 负责人：**G 定规范，A 按规范实现**（`apps/desktop/src-tauri/src/fingerprint.rs`）。
> 权威实现：`apps/core/license/device.py`（Python sidecar，激活流程实际使用）。
> 状态：**已冻结**。改版必须升版本号 `bizspark-fp-v1 → v2`，并把已激活用户的凭证全部作废——
> 所以只能在首次上架前改动。

---

## 1. 公式（写死）

```
canonical = "bizspark-fp-v1|" + os + "|" + sys_install_id + "|" + cpu_id + "|" + disk_id + "|" + board_id
fingerprint = sha256(canonical.encode("utf-8")).hexdigest()      # 64 位小写 hex
```

- 字段顺序、分隔符 `|`、前缀 `bizspark-fp-v1` **一个字符都不能变**（改了就是另一个指纹）。
- 全部字段经规范化：`trim()` → `lower()` → 内部 `|` 替换为 `/` → 空值写 `-`。
- 输出 64 字符小写 hex；比较时统一 `lower()`。

## 2. 分量来源

| 字段 | Windows | macOS | Linux |
|---|---|---|---|
| `os` | `windows-<arch>`（`platform.machine()` 小写） | `darwin-<arch>` | `linux-<arch>` |
| `sys_install_id` | `HKLM\SOFTWARE\Microsoft\Cryptography\MachineGuid` | `ioreg -rd1 -c IOPlatformExpertDevice` → `IOPlatformUUID` | `/etc/machine-id`，回退 `/var/lib/dbus/machine-id` |
| `cpu_id` | `HKLM\HARDWARE\DESCRIPTION\System\CentralProcessor\0` → `ProcessorNameString` | `platform.processor()`，回退 arch | `platform.processor()`，回退 arch |
| `disk_id` | `GetVolumeInformationW(<SystemDrive>\\)` → 卷序列号，`%08X` | `-` | `-` |
| `board_id` | `HKLM\HARDWARE\DESCRIPTION\System\BIOS` → `BaseBoardProduct` | `-` | `/sys/class/dmi/id/board_name` |

降级规则：任一分量取不到 → `-`，**不报错、不阻断激活**；整串采集异常 → `bizspark-fp-v1|unknown`。

## 3. 禁止采集（红线）

**禁止**：IP（含内网/公网）、MAC 地址明文、`USERNAME`/`USER`、主机名 `COMPUTERNAME`、
`$HOME` 或任何文件路径、时区、语言、已安装软件列表、浏览器指纹。

理由（写进代码注释，评审时逐条对照）：
- 海外用户大量使用 VPN / 换网络 / 酒店 Wi-Fi，**IP 会误伤合法用户**（换网络就掉激活＝差评）；
- 换机器名、改用户名在迁移电脑时很常见；
- 上述信息与"这份副本付过钱"无关，采集即为过度收集（隐私政策里也无法自圆其说）。

## 4. 测试向量（A 的 Rust 实现必须逐字节一致）

| canonical 串 | 期望 `fingerprint` |
|---|---|
| `bizspark-fp-v1\|windows-amd64\|4f8c1e2a-1111-2222-3333-444455556666\|intel(r) core(tm) i5-8250u cpu @ 1.60ghz\|1a2b3c4d\|b250m-d3h` | `62b7fd389676f38fee4378a81c2c9dcb05fe7561e41f5b1e7cd5d84747ebb8d9` |
| `bizspark-fp-v1\|darwin-arm64\|0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0\|arm\|-\|-` | `f073b9e17398ffdf748b802eff4a43282e7ac47b805e72b3f48c62732f1f88fc` |
| `bizspark-fp-v1\|linux-x86_64\|9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d\|xeon(r) e5-2670\|-\|super micro x9` | `6085b627710a06fbbd5424af6f835cd230dfede55a610ed4c44fc3dd3704cbd4` |

Rust 侧建议加同一个单测（`fingerprint::hash_of_canonical("...") == "62b7fd…"`），
这样"两边算得不一样"这种问题在编译期就暴露，不会等到用户第 4 台设备才发现。

## 5. 与 A 的 Rust 现状差异（需 A 修）

当前 `fingerprint.rs` 只用了 `MachineGuid` 一项、且前缀是 `bizspark-fp-v1:`（冒号），
与本规范不一致：

```
现状：sha256("bizspark-fp-v1:" + MachineGuid)                       # 只有 1 个分量
规范：sha256("bizspark-fp-v1|os|sys_install_id|cpu_id|disk_id|board_id")
```

处理方式（二选一，**必须先定下来，不能一半一半**）：

1. **A 按本规范补齐四个分量**（推荐，5 项加起来才是"换硬盘/换主板也认得出来"的粒度）；
2. 或者 A 只做采集透传：Rust 只负责把四个原始分量交给 sidecar，散列在 `device.py` 里算。

**在 A 改完之前，A 的 Rust 层不要注入 `BIZSPARK_DEVICE_HASH`**：两套算法并存会让同一台机器
出现两个指纹，席位会被重复占用。目前激活完全由 sidecar 计算，A 不注入即等价于"方案 2 未启用"。

## 6. 稳定性说明（写进用户可见文案时的口径）

| 事件 | 指纹是否变化 |
|---|---|
| 重启、系统更新、换网络、挂 VPN、改机器名、改用户名 | **不变** |
| 换系统盘 / 格式化重装系统 | **变**（会占用一个席位，可用同一码在第 2、3 台激活） |
| 换主板、换整机 | **变**（按新设备计） |
| 同一台机器重装 BizSpark | **不变** |

## 7. 变更管理

1. 任何分量或格式改动 → 版本前缀升为 `bizspark-fp-v2`。
2. 已发码的用户在旧指纹下激活过，升级后会变成"未激活"→ **只在首次上架前允许改**。
3. 改动需同步更新：`device.py`、`docs/fingerprint-spec.md`、A 的 `fingerprint.rs` 及其单测、
   本文档 §4 测试向量。
