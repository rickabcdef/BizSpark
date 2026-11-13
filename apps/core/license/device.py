# -*- coding: utf-8 -*-
"""license.device — 机器指纹（负责人：G，G-01；规范见 docs/fingerprint-spec.md）

规范（§3.5 / §F10 步骤 6，写死）：

    device_hash = sha256("bizspark-fp-v1|" + os + "|" + sys_install_id
                         + "|" + cpu_id + "|" + disk_id + "|" + board_id)

**禁止**采集：IP、MAC 明文、用户名、主机名、文件路径、时区、语言。原因写进了
规范文档：海外用户常挂 VPN、换网络、改机器名，这些都会误伤合法用户（差评来源）。

只取"重装系统前不变、且与身份无关"的四类硬件/系统标识：
- `sys_install_id`：Windows MachineGuid / macOS IOPlatformUUID / Linux machine-id
- `cpu_id`：CPU 型号标识（同一批机器可能相同，仅作混淆项）
- `disk_id`：系统盘卷序列号（格式化才会变）
- `board_id`：主板型号标识（取不到时为 `-`）

任一分量取不到都不报错、不阻断激活，用 `-` 占位（少一项目标机器仍然唯一）；
整个采集失败时退化为 `unknown`，激活流程照常可用（宁可放宽也不锁死用户）。
"""

import hashlib
import os
import platform
import sys

ENV_DEVICE_HASH = "BIZSPARK_DEVICE_HASH"  # A 的 Rust 层按同一规范算好后可注入；不注入则本模块自算
FP_VERSION = "bizspark-fp-v1"
_HEX64 = set("0123456789abcdef")

_cache = {}


# --------------------------------------------------------------------------- #
# 各平台分量采集（全部 best-effort，异常一律吞掉，绝不阻断激活）
# --------------------------------------------------------------------------- #
def _win_reg(path, value):
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0,
                             winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0))
        try:
            data, _ = winreg.QueryValueEx(key, value)
            return str(data).strip()
        finally:
            winreg.CloseKey(key)
    except Exception:
        return ""


def _win_volume_serial():
    """系统盘卷序列号（GetVolumeInformationW；格式化才会变，与本机身份无关）。"""
    try:
        import ctypes
        from ctypes import wintypes
        drive = (os.environ.get("SystemDrive") or "C:") + "\\"
        serial = wintypes.DWORD(0)
        ok = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive), None, 0,
            ctypes.byref(serial), None, None, None, 0)
        return "%08X" % serial.value if ok else ""
    except Exception:
        return ""


def _unix_machine_id():
    for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            with open(path, encoding="utf-8") as f:
                v = f.read().strip()
            if v:
                return v
        except OSError:
            continue
    return ""


def _mac_platform_uuid():
    try:
        import subprocess
        out = subprocess.run(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                             capture_output=True, timeout=2, check=False)
        for line in out.stdout.decode("utf-8", "ignore").splitlines():
            if "IOPlatformUUID" in line:
                return line.split("=")[-1].strip().strip('"')
    except Exception:
        pass
    return ""


def _linux_dmi(name):
    try:
        with open("/sys/class/dmi/id/" + name, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _components():
    """四类分量 + 平台标签。键顺序固定，保证跨平台可复现。"""
    system = platform.system().lower()
    arch = (platform.machine() or "").lower()
    os_tag = "%s-%s" % (system, arch)
    if system == "windows":
        sys_install = _win_reg(r"SOFTWARE\Microsoft\Cryptography", "MachineGuid")
        cpu = _win_reg(r"HARDWARE\DESCRIPTION\System\CentralProcessor\0", "ProcessorNameString")
        board = _win_reg(r"HARDWARE\DESCRIPTION\System\BIOS", "BaseBoardProduct")
        disk = _win_volume_serial()
    elif system == "darwin":
        sys_install = _mac_platform_uuid()
        cpu = (platform.processor() or arch)
        board = "-"
        disk = "-"
    else:  # linux / 其他 unix
        sys_install = _unix_machine_id()
        cpu = (platform.processor() or arch)
        board = _linux_dmi("board_name")
        disk = "-"
    clean = lambda v: (v or "-").strip().lower().replace("|", "/") or "-"
    return {
        "os": clean(os_tag),
        "sys_install_id": clean(sys_install),
        "cpu_id": clean(cpu),
        "disk_id": clean(disk),
        "board_id": clean(board),
    }


def canonical_string():
    """规范化串（规范文档 §2 定义，A 的 Rust 实现必须与本函数逐字节一致）。"""
    c = _components()
    return "|".join([FP_VERSION, c["os"], c["sys_install_id"],
                     c["cpu_id"], c["disk_id"], c["board_id"]])


def compute_device_hash():
    """本机指纹：64 字符 hex。同一机器恒等，不含任何可反查身份的信息。"""
    if "hash" not in _cache:
        try:
            raw = canonical_string().encode("utf-8")
        except Exception:
            raw = (FP_VERSION + "|unknown").encode("utf-8")
        _cache["hash"] = hashlib.sha256(raw).hexdigest()
    return _cache["hash"]


# --------------------------------------------------------------------------- #
# 对外：取本机指纹（支持上层注入）
# --------------------------------------------------------------------------- #
def _valid_hash(value):
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    if v.startswith("sha256:"):
        v = v[7:]
    if len(v) == 64 and all(c in _HEX64 for c in v):
        return v
    return None


def device_hash(payload=None):
    """优先级：payload.device_hash > 环境变量（A 的 Rust 层注入）> 本模块自算。

    上层若按 docs/fingerprint-spec.md 算好并传入，以传入值为准（保证一处算法、多处复用）。
    """
    if isinstance(payload, dict):
        got = _valid_hash(payload.get("device_hash"))
        if got:
            return got
    got = _valid_hash(os.environ.get(ENV_DEVICE_HASH))
    if got:
        return got
    return compute_device_hash()


def reset_cache():
    """仅测试用：清空指纹缓存（模拟换机器）。"""
    _cache.clear()
