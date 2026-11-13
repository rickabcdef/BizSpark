//! A-06 机器指纹采集原语（负责人：A 写壳，G 定规范并审核）
//!
//! 按 docs/fingerprint-spec.md v1 冻结版实现（PM 2026-11-13 修复 G 审遗留项 1）：
//!
//! ```text
//! canonical   = "bizspark-fp-v1|" + os + "|" + sys_install_id + "|" + cpu_id + "|" + disk_id + "|" + board_id
//! fingerprint = sha256(canonical.encode("utf-8")).hexdigest()   // 64 位小写 hex
//! ```
//!
//! 约束（§3 红线，逐条对照过）：
//! - 只采集稳定、非联网、不含 IP/MAC/用户名/主机名/路径 的本机标识
//! - 全部字段规范化：trim → lower → 内部 `|` 换 `/` → 空值写 `-`
//! - 输出 SHA-256 单向散列，原始信息不出 Rust 层；授权校验逻辑归 G（license/）
//! - 权威实现对齐 `apps/core/license/device.py::canonical_string`（单测含规范 §4 的 3 条测试向量）
//! - 整串采集异常 → `bizspark-fp-v1|unknown`（不 panic、不阻断激活）

use sha2::{Digest, Sha256};

pub const FP_VERSION: &str = "bizspark-fp-v1";

#[cfg(windows)]
use std::os::windows::process::CommandExt;

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x0800_0000;

/// 规范化单字段：trim → lower → 内部 `|` 换 `/` → 空值写 `-`（规范 §1）。
fn clean(v: &str) -> String {
    let t = v.trim().to_lowercase().replace('|', "/");
    if t.is_empty() { "-".to_string() } else { t }
}

fn sha256_hex(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hasher.finalize().iter().map(|b| format!("{:02x}", b)).collect()
}

/// 规范文档 §4：Rust 与 Python（device.py）必须逐字节一致，编译期即可发现两边算法漂移。
pub fn hash_of_canonical(canonical: &str) -> String {
    sha256_hex(canonical.as_bytes())
}

#[cfg(windows)]
fn reg_query(path: &str, value: &str) -> String {
    if let Ok(output) = std::process::Command::new("reg")
        .args(["query", path, "/v", value])
        .creation_flags(CREATE_NO_WINDOW)
        .output()
    {
        let text = String::from_utf8_lossy(&output.stdout);
        if let Some(line) = text.lines().find(|l| l.contains(value)) {
            if let Some(v) = line.rsplit(char::is_whitespace).next() {
                let v = v.trim().trim_matches('\u{0}').to_string();
                if !v.is_empty() {
                    return v;
                }
            }
        }
    }
    String::new()
}

#[cfg(windows)]
fn system_drive() -> String {
    // SystemDrive 形如 "C:"；取不到默认 C:
    std::env::var("SystemDrive").unwrap_or_else(|_| "C:".into())
}

#[cfg(windows)]
fn volume_serial() -> String {
    // GetVolumeInformationW 的等效只读采集：`vol C:` → "Volume Serial Number is 1A2B-3C4D"，
    // 规范要求 %08X（无连字符）。
    let drive = system_drive();
    if let Ok(output) = std::process::Command::new("cmd")
        .args(["/c", "vol", &drive])
        .creation_flags(CREATE_NO_WINDOW)
        .output()
    {
        let text = String::from_utf8_lossy(&output.stdout);
        for line in text.lines() {
            if let Some(idx) = line.find("Volume Serial Number is") {
                let tail = line[idx + "Volume Serial Number is".len()..].trim();
                let hex: String = tail.chars().filter(|c| c.is_ascii_hexdigit()).collect();
                if let Ok(n) = u32::from_str_radix(&hex, 16) {
                    return format!("{:08X}", n);
                }
            }
        }
    }
    String::new()
}

/// 规范 §2：os = windows-<arch>（Python platform.machine() 口径：PROCESSOR_ARCHITECTURE）。
/// darwin 的 Python machine() 是 arm64 而 Rust ARCH 是 aarch64，此处做等值映射保证一致。
fn arch_python_style() -> String {
    #[cfg(windows)]
    {
        let a = std::env::var("PROCESSOR_ARCHITECTURE").unwrap_or_default();
        let a = a.trim().to_lowercase();
        if !a.is_empty() {
            return a;
        }
        // 无 env 时按 Rust ARCH 映射（x86_64→amd64 / aarch64→arm64）
        return match std::env::consts::ARCH {
            "x86_64" => "amd64".into(),
            "aarch64" => "arm64".into(),
            other => other.into(),
        };
    }
    #[cfg(target_os = "macos")]
    {
        return match std::env::consts::ARCH {
            "aarch64" => "arm64".into(),
            other => other.into(),
        };
    }
    #[cfg(all(unix, not(target_os = "macos")))]
    {
        std::env::consts::ARCH.into()
    }
}

#[cfg(target_os = "macos")]
fn mac_platform_uuid() -> String {
    if let Ok(output) = std::process::Command::new("ioreg")
        .args(["-rd1", "-c", "IOPlatformExpertDevice"])
        .output()
    {
        let text = String::from_utf8_lossy(&output.stdout);
        for line in text.lines() {
            if let Some(eq) = line.find('=') {
                if line.contains("IOPlatformUUID") {
                    return line[eq + 1..].trim().trim_matches('"').to_string();
                }
            }
        }
    }
    String::new()
}

#[cfg(all(unix, not(target_os = "macos")))]
fn unix_machine_id() -> String {
    for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"] {
        if let Ok(id) = std::fs::read_to_string(path) {
            let id = id.trim().to_string();
            if !id.is_empty() {
                return id;
            }
        }
    }
    String::new()
}

/// 采集四类分量 + 平台标签（对齐 device.py::_components；任一取不到 → "-"，不报错）。
fn components() -> [String; 5] {
    let arch = arch_python_style();

    #[cfg(windows)]
    {
        let sys_install = reg_query(r"SOFTWARE\Microsoft\Cryptography", "MachineGuid");
        let cpu = reg_query(r"HARDWARE\DESCRIPTION\System\CentralProcessor\0", "ProcessorNameString");
        let board = reg_query(r"HARDWARE\DESCRIPTION\System\BIOS", "BaseBoardProduct");
        let disk = volume_serial();
        return [
            format!("windows-{}", arch),
            sys_install, cpu, disk, board,
        ];
    }

    #[cfg(target_os = "macos")]
    {
        let cpu_arch = if std::env::consts::ARCH == "aarch64" { "arm" } else { std::env::consts::ARCH };
        return [
            format!("darwin-{}", arch),
            mac_platform_uuid(),
            cpu_arch.to_string(),
            "-".to_string(),
            "-".to_string(),
        ];
    }

    #[cfg(all(unix, not(target_os = "macos")))]
    {
        let board = std::fs::read_to_string("/sys/class/dmi/id/board_name")
            .map(|s| s.trim().to_string())
            .unwrap_or_default();
        [
            format!("linux-{}", arch),
            unix_machine_id(),
            arch.clone(),
            "-".to_string(),
            board,
        ]
    }
}

/// 规范 §1 公式：canonical 串（与 device.py::canonical_string 逐字节一致）。
pub fn canonical_string() -> String {
    match std::panic::catch_unwind(components) {
        Ok(parts) => {
            let c: Vec<String> = parts.iter().map(|p| clean(p)).collect();
            format!(
                "{}|{}|{}|{}|{}|{}",
                FP_VERSION, c[0], c[1], c[2], c[3], c[4]
            )
        }
        Err(_) => format!("{}|unknown", FP_VERSION),
    }
}

/// 返回机器指纹（SHA-256 hex，64 字符）。G 的激活流程只拿散列，拿不到原始 ID。
/// 注意：规范 §5——激活完全由 sidecar（device.py）计算，本函数仅作诊断输出（main.rs），
/// 与 sidecar 同算法后两端口径一致；仍不注入 BIZSPARK_DEVICE_HASH。
pub fn fingerprint_hex() -> String {
    hash_of_canonical(&canonical_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fingerprint_is_stable_and_sha256_hex() {
        let a = fingerprint_hex();
        let b = fingerprint_hex();
        assert_eq!(a, b, "同一机器两次采集应一致");
        assert_eq!(a.len(), 64, "应为 SHA-256 hex");
        assert!(a.chars().all(|c| c.is_ascii_hexdigit()));
        assert!(c_lower_hex(&a), "应为小写 hex");
    }

    fn c_lower_hex(s: &str) -> bool {
        s.chars().all(|c| c.is_ascii_digit() || c.is_ascii_lowercase())
    }

    #[test]
    fn canonical_uses_pipe_separator_and_six_fields() {
        let c = canonical_string();
        let fields: Vec<&str> = c.split('|').collect();
        assert_eq!(fields.len(), 6, "prefix + 5 分量，实际：{}", c);
        assert_eq!(fields[0], "bizspark-fp-v1");
        assert!(!c.contains(':'), "规范用 | 分隔，不允许旧版冒号形式");
    }

    #[test]
    fn no_forbidden_fields_collected() {
        // 规范 §3 红线：用户名/主机名/盘符路径不得进入 canonical（'/' 是规范化替换符，允许）
        let c = canonical_string().to_lowercase();
        for banned in ["computername", "username", "\\\\", "c:\\"] {
            assert!(!c.contains(banned), "红线字段 {} 出现在指纹串中", banned);
        }
    }

    /// 规范 §4 测试向量：Rust 实现必须与期望指纹逐字节一致（权威：device.py）。
    #[test]
    fn spec_test_vectors() {
        let cases: [(&str, &str); 3] = [
            (
                "bizspark-fp-v1|windows-amd64|4f8c1e2a-1111-2222-3333-444455556666|intel(r) core(tm) i5-8250u cpu @ 1.60ghz|1a2b3c4d|b250m-d3h",
                "62b7fd389676f38fee4378a81c2c9dcb05fe7561e41f5b1e7cd5d84747ebb8d9",
            ),
            (
                "bizspark-fp-v1|darwin-arm64|0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0|arm|-|-",
                "f073b9e17398ffdf748b802eff4a43282e7ac47b805e72b3f48c62732f1f88fc",
            ),
            (
                "bizspark-fp-v1|linux-x86_64|9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d|xeon(r) e5-2670|-|super micro x9",
                "6085b627710a06fbbd5424af6f835cd230dfede55a610ed4c44fc3dd3704cbd4",
            ),
        ];
        for (canonical, expected) in cases {
            assert_eq!(hash_of_canonical(canonical), expected, "向量不一致：{}", canonical);
        }
    }

    #[test]
    fn clean_normalizes() {
        assert_eq!(clean("  Intel|Core "), "intel/core");
        assert_eq!(clean(""), "-");
        assert_eq!(clean("  "), "-");
    }
}

#[cfg(windows)]
trait CreationFlagsExt {
    fn creation_flags(&mut self, flags: u32) -> &mut Self;
}
#[cfg(windows)]
impl CreationFlagsExt for std::process::Command {
    fn creation_flags(&mut self, flags: u32) -> &mut Self {
        std::os::windows::process::CommandExt::creation_flags(self, flags)
    }
}
