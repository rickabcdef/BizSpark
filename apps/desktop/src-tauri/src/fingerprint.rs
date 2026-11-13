//! A-06 机器指纹采集原语（负责人：A 写壳，G 定规范并审核）
//!
//! 约束（§6.2 A-06 验收：G 验签通过、无 IP/MAC）：
//! - 只采集稳定、非联网、不含 IP/MAC 的本机标识
//! - 输出为 SHA-256 单向散列，原始信息不出 Rust 层
//! - 本文件只提供"采集原语"，授权校验逻辑归 G（license/）

use sha2::{Digest, Sha256};

/// 采集本机稳定标识并散列。Windows 取注册表 MachineGuid；
/// 其他平台取 /etc/machine-id。任一失败返回占位串（不 panic，激活流程由 G 决定降级）。
fn raw_machine_id() -> String {
    #[cfg(target_os = "windows")]
    {
        // HKLM\SOFTWARE\Microsoft\Cryptography\MachineGuid（安装系统时生成，稳定且不含网络信息）
        if let Ok(output) = std::process::Command::new("reg")
            .args(["query", r"HKLM\SOFTWARE\Microsoft\Cryptography", "/v", "MachineGuid"])
            .creation_flags(0x0800_0000) // CREATE_NO_WINDOW
            .output()
        {
            let text = String::from_utf8_lossy(&output.stdout);
            if let Some(guid) = text
                .lines()
                .find(|l| l.contains("MachineGuid"))
                .and_then(|l| l.rsplit(char::is_whitespace).next())
            {
                let guid = guid.trim().to_string();
                if !guid.is_empty() {
                    return guid;
                }
            }
        }
        std::env::var("COMPUTERNAME").unwrap_or_else(|_| "unknown-windows".into())
    }
    #[cfg(not(target_os = "windows"))]
    {
        for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"] {
            if let Ok(id) = std::fs::read_to_string(path) {
                let id = id.trim().to_string();
                if !id.is_empty() {
                    return id;
                }
            }
        }
        "unknown-unix".into()
    }
}

/// 返回机器指纹（SHA-256 hex，64 字符）。G 的激活流程只拿散列，拿不到原始 ID。
pub fn fingerprint_hex() -> String {
    let mut hasher = Sha256::new();
    hasher.update(b"bizspark-fp-v1:");
    hasher.update(raw_machine_id().as_bytes());
    let out = hasher.finalize();
    out.iter().map(|b| format!("{:02x}", b)).collect()
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
