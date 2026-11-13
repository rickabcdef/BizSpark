# -*- coding: utf-8 -*-
"""license.activate — F10 授权激活 / 凭证 / 席位（负责人：G，G-03 / G-04 / G-05）

三条铁律（需求 §F10 / L08，违反任一条就是差评来源）：

1. **激活 ≠ 登录**：不建账号、不要邮箱、不发心跳、不问"欢迎回来"。
2. **一次性写入、永久离线**：`activate` 成功后一切判断只读本地 `license.dat`，
   验签只用内置公钥，**零出网**（T-45 抓包为空）。
3. **失败一律温和**：码不对 → 输入框下一行提示（`E_LICENSE_BAD_CODE`）；
   第 4 台设备 → 引导释放席位（`E_LICENSE_SEAT_FULL`），**绝不出现"授权失败"字样**。

席位模型（§F10 步骤 5）：
- `license.dat` 不存在 → 新建 `{seats:[本机], seats_max:3}`；
- 存在且本机已在 `seats` → **幂等成功**，不占第 2 个位（T-43）；
- 存在、本机不在、且已满 3 → `E_LICENSE_SEAT_FULL`（T-44）；
- 凭证损坏 → 改名留档后允许重新激活（**不锁死用户**）。

Store 版：`apps/core/license/` 整个目录在打包时被裁掉（P-08 / T-42），
`main.py` 用 try/except 挂载，裁剪后这三个 cmd 自然不存在。
"""

import hashlib
import hmac
import json
import os
import subprocess
import sys
import time

from license import device as device_mod
from license import signature as sig_mod
from state import paths

# 运营替换为真实支持邮箱（G-05：首版无后台，人工处理释放席位）
SUPPORT_EMAIL = "support@bizspark.app"

POOL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pool.json")
LICENSE_VERSION = 1

# 错误码（附录 D）：message 是给内部日志/调试看的，前端默认不展示；
# 但措辞仍然不含"失败/failed/error"，避免被日志工具直接抛到界面上时伤到用户。
E_BAD_CODE = {
    "code": "E_LICENSE_BAD_CODE",
    "message": "This code doesn't match any copy. Check the receipt email and try again.",
    "recoverable": True,
}
E_SEAT_FULL = {
    "code": "E_LICENSE_SEAT_FULL",
    "message": "This code is already in use on 3 devices. Choose \"Changed computer? Release a seat\" and we'll help.",
    "recoverable": True,
}

_pool_cache = {"pool": None, "index": None, "mtime": None}


# --------------------------------------------------------------------------- #
# 码池
# --------------------------------------------------------------------------- #
def load_pool(force=False):
    """读取并验签码池；失败返回 None（激活一律回 E_LICENSE_BAD_CODE，不崩、不锁死）。"""
    try:
        mtime = os.path.getmtime(POOL_PATH)
    except OSError:
        return None
    if not force and _pool_cache["pool"] is not None and _pool_cache["mtime"] == mtime:
        return _pool_cache["pool"]
    try:
        with open(POOL_PATH, encoding="utf-8") as f:
            pool = json.load(f)
    except (OSError, ValueError):
        return None
    if not sig_mod.verify_pool_header(pool):
        return None
    index = {}
    for entry in pool.get("codes") or []:
        if isinstance(entry, dict) and isinstance(entry.get("h"), str):
            index[entry["h"].lower()] = entry
    _pool_cache.update(pool=pool, index=index, mtime=mtime)
    return pool


def _pool_index():
    pool = load_pool()
    if pool is None:
        return None
    return _pool_cache["index"] or {}


# --------------------------------------------------------------------------- #
# 凭证读写
# --------------------------------------------------------------------------- #
def _license_path():
    return paths.license_path()


def _iso_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _dh(value):
    """统一 `sha256:<64hex>` 形态（§3.5）。"""
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    if v.startswith("sha256:"):
        v = v[7:]
    if len(v) == 64 and all(c in "0123456789abcdef" for c in v):
        return "sha256:" + v
    return None


def _local_tag(rec):
    """本地完整性标记：防止手工改 `seats` 数组（尽力而为，见 security-review §5）。

    密钥由凭据自身的背书签名派生——只有拿到**真码**的人才算得出，改文件的人若不知道
    这套派生规则就会破坏标记。产品本身承诺离线、无回连，因此这是"提高门槛"而非"强防"。
    """
    key = hashlib.sha256(("bizspark-local-v2|" + str(rec.get("sig"))).encode("utf-8")).digest()
    body = sig_mod.canonical({k: v for k, v in rec.items() if k != "local_tag"})
    return "hmac-sha256:" + hmac.new(key, body, hashlib.sha256).hexdigest()


def _restrict_permissions(path):
    """凭证权限 600 语义：POSIX 用 chmod；Windows 用 icacls 去掉继承、只留当前用户。"""
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    if sys.platform.startswith("win"):
        user = os.environ.get("USERNAME")
        if not user:
            return
        try:
            subprocess.run(
                ["icacls", path, "/inheritance:r", "/grant:r", user + ":F"],
                capture_output=True, timeout=5, check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception:
            pass  # 权限收紧失败不影响可用性（文件本身只在用户 profile 下）


def _write_license(rec):
    path = _license_path()
    try:
        paths.app_data_dir(create=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(rec, f, ensure_ascii=False, sort_keys=True)
        os.replace(tmp, path)   # 原子替换：断电也不会留下半个凭证
        _restrict_permissions(path)
        return True
    except OSError:
        return False


def _archive_corrupt(path):
    """损坏凭证改名留档（不硬删，便于支持排查），只保留最近 2 份。"""
    try:
        stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
        os.replace(path, "%s.corrupt-%s" % (path, stamp))
    except OSError:
        try:
            os.remove(path)
        except OSError:
            pass
        return
    try:
        base = os.path.dirname(path)
        olds = sorted(n for n in os.listdir(base) if n.startswith("license.dat.corrupt-"))
        for name in olds[:-2]:
            os.remove(os.path.join(base, name))
    except OSError:
        pass


def read_license():
    """读凭证并验签。返回 (rec|None, reason)：

    reason ∈ `missing`（没激活过）/ `unreadable`（坏了或被改过）/ `ok`。
    """
    path = _license_path()
    if not os.path.isfile(path):
        return None, "missing"
    try:
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
    except (OSError, ValueError):
        return None, "unreadable"
    ok, _why = verify_license(rec)
    if not ok:
        return None, "unreadable"
    return rec, "ok"


def verify_license(rec):
    """凭证验签（纯离线）：返回 (ok, reason)。"""
    if not isinstance(rec, dict) or rec.get("v") != LICENSE_VERSION:
        return False, "version"
    seats_max = rec.get("seats_max")
    seats = rec.get("seats")
    if seats_max != sig_mod.DEFAULT_SEATS_MAX or not isinstance(seats, list):
        return False, "seats_max"
    if len(seats) > seats_max:
        return False, "seats_overflow"
    serial = rec.get("serial")
    if not isinstance(serial, str) or len(serial) != 5 or \
            any(c not in sig_mod.ALPHABET for c in serial):
        return False, "serial"
    if not _dh(rec.get("code_hash")) or not _dh(rec.get("device_hash")):
        return False, "hash_shape"
    for seat in seats:
        if not isinstance(seat, dict) or not _dh(seat.get("device_hash")):
            return False, "seat_shape"
        if not isinstance(seat.get("activated_at"), str):
            return False, "seat_time"
    sig = rec.get("sig")
    if not isinstance(sig, str) or not sig.startswith("ed25519:"):
        return False, "sig_shape"
    if not sig_mod.verify_code_attestation(serial, seats_max, sig.split(":", 1)[1]):
        return False, "sig"
    tag = rec.get("local_tag")
    if not isinstance(tag, str) or tag != _local_tag(rec):
        return False, "local_tag"
    return True, "ok"


def license_state():
    """给 `get_state.license_state` 用的真实状态（覆盖 F 的"文件存在即已激活"）。

    取值：`activated`（本机在席位内）/ `unseated`（凭证合法但本机不在席位，多为拷来的文件）
    / `invalid`（损坏或被改）/ `none`（从未激活）。
    """
    rec, reason = read_license()
    if reason == "missing":
        return "none"
    if reason != "ok":
        return "invalid"
    return "activated" if _has_seat(rec, device_mod.device_hash()) else "unseated"


# --------------------------------------------------------------------------- #
# 席位
# --------------------------------------------------------------------------- #
def _has_seat(rec, dev):
    target = _dh(dev)
    return any(_dh(s.get("device_hash")) == target for s in rec.get("seats") or [])


def _seats_used(rec):
    return len(rec.get("seats") or []) if isinstance(rec, dict) else 0


def _new_record(code_display, entry, dev):
    rec = {
        "v": LICENSE_VERSION,
        "pool_id": (load_pool() or {}).get("pool_id") or "unknown",
        "code_hash": sig_mod.full_code_hash(code_display),
        "serial": entry["s"],
        "device_hash": _dh(dev),
        "seats": [{"device_hash": _dh(dev), "activated_at": _iso_now()}],
        "seats_max": sig_mod.DEFAULT_SEATS_MAX,
        "signed_at": _iso_now(),
        "sig": "ed25519:" + entry["sig"],
    }
    rec["local_tag"] = _local_tag(rec)
    return rec


def _success(rec, extra=None):
    data = {
        "activated": True,
        "state": "activated",
        "seats_used": _seats_used(rec),
        "seats_max": rec.get("seats_max") or sig_mod.DEFAULT_SEATS_MAX,
    }
    if extra:
        data.update(extra)
    return data


# --------------------------------------------------------------------------- #
# §2.4 cmd：activate / license_status / release_seat
# --------------------------------------------------------------------------- #
def activate(payload):
    """`activate {code, device_hash?}` → `{activated, state, seats_used, seats_max}`。"""
    payload = payload if isinstance(payload, dict) else {}
    raw = payload.get("code")
    code = sig_mod.normalize_code(raw)
    if code is None:
        return None, dict(E_BAD_CODE)

    index = _pool_index()
    if not index:
        return None, dict(E_BAD_CODE)
    entry = index.get((sig_mod.code_hash(code) or "").lower())
    if not entry:
        return None, dict(E_BAD_CODE)
    seats_max = sig_mod.DEFAULT_SEATS_MAX
    if not sig_mod.verify_code_attestation(entry.get("s"), seats_max, entry.get("sig")):
        return None, dict(E_BAD_CODE)   # 码池条目被改过

    dev = device_mod.device_hash(payload)
    rec, reason = read_license()

    if reason == "ok":
        if _has_seat(rec, dev):
            # T-43 幂等：同一台机器再激活不占新位、不改文件、不报错
            return _success(rec, {"idempotent": True}), None
        if (rec.get("code_hash") or "") != sig_mod.full_code_hash(code):
            # 这份副本已经用另一个码激活过；本机又不在席位里 → 按"码不匹配"温和处理
            return None, dict(E_BAD_CODE)
        if _seats_used(rec) >= seats_max:
            # T-44：第 4 台设备 → 引导释放席位，不说"授权失败"
            return None, dict(E_SEAT_FULL)
        rec["seats"] = list(rec.get("seats") or []) + [
            {"device_hash": _dh(dev), "activated_at": _iso_now()}]
        rec["device_hash"] = _dh(dev)
        rec["signed_at"] = _iso_now()
        rec.pop("local_tag", None)
        rec["local_tag"] = _local_tag(rec)
        if not _write_license(rec):
            return _success(rec, {"persisted": False}), None
        return _success(rec), None

    if reason == "unreadable":
        # 凭证损坏/被改：留档后重建，允许重新输入同一码（不锁死）
        _archive_corrupt(_license_path())

    rec = _new_record(code, entry, dev)
    if not _write_license(rec):
        # 写不进去（磁盘满/权限异常）：内存里给出成功语义但不假装已持久化，避免"激活了但下次还要输"
        return None, {"code": "E_LICENSE_BAD_CODE", "recoverable": True,
                      "message": "This device didn't accept the activation file. Try again from your user folder."}
    return _success(rec), None


def license_status(payload):
    """`license_status {}` → 席位数与凭证状态（激活页首屏用；读不到就给 null，让 UI 走空态）。"""
    dev = device_mod.device_hash(payload)
    rec, reason = read_license()
    if reason == "ok":
        return {
            "activated": _has_seat(rec, dev),
            "state": "activated" if _has_seat(rec, dev) else "unseated",
            "seats_used": _seats_used(rec),
            "seats_max": rec.get("seats_max") or sig_mod.DEFAULT_SEATS_MAX,
        }, None
    return {
        "activated": False,
        "state": "none" if reason == "missing" else "invalid",
        "seats_used": None,
        "seats_max": sig_mod.DEFAULT_SEATS_MAX,
    }, None


def release_seat(payload):
    """G-05 首版**无后台**：不删席位、不做账号、不做找回，只给说明 + 支持邮箱。

    席位必须由人处理（防止"点一下就无限换机"），所以这里返回 `manual: true`，
    前端只展示一段说明，不改变任何本地状态。
    """
    rec, reason = read_license()
    return {
        "released": False,
        "manual": True,
        "support_email": SUPPORT_EMAIL,
        "seats_used": _seats_used(rec) if reason == "ok" else None,
        "seats_max": sig_mod.DEFAULT_SEATS_MAX,
        "message": ("Write to %s from the email you bought with. Tell us the last 6 characters "
                    "of the code and which computer to free. We'll do it by hand — no account, "
                    "no password, usually within one working day." % SUPPORT_EMAIL),
    }, None
