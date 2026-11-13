# -*- coding: utf-8 -*-
"""license.signature — 激活码 / 码池 / 凭证的签名契约（负责人：G，G-02 / G-04）

三层签名，全部 Ed25519，**客户端只内置公钥**：

1. **码池签名**（pool.json 的 `sig`）：签发工具对整个码池签名，客户端验签后才信任码池。
   没有它，任何人替换 pool.json 就能给自己造码。
2. **单码背书**（pool.codes[].sig）：签发工具对 `码序号(serial) + 席位数` 签名。
   客户端验签通过才算"真码"，并把这枚签名原样写进 `license.dat` 的 `sig` 字段（§3.5）。
3. **凭证验签**（license.dat 的 `sig`）：每次启动只用内置公钥离线验一次，
   **无网络、无心跳、无账号**（L08 / T-45）。

码格式（F10 步骤 1，写死）`BZSP-XXXX-XXXX-XXXX`：首段固定品牌前缀，后 3 段共 12 位，
每位取自 32 字符表 `23456789ABCDEFGHJKLMNPQRSTUVWXYZ`（去掉易混的 0/O/1/I/L）→ 60 bit。
码本身不携带签名（12 位放不下 64 字节签名），所以"真伪"由**码池里的单码背书**判定，
这也是任务卡 G-02 要求"离线签发工具 + 码池"的原因。

本文件同时是**码规范化与哈希的唯一实现**：签发工具（tools/issue.py）与客户端共用，
避免两边各写一份导致"签得出、验不过"。
"""

import hashlib
import json

from license import ed25519

# —— 内置公钥（只此一份；私钥在签发人手里，永不进包）——
# 发布前用 `python tools/issue.py keygen` 轮换并重新签发码池，见 docs/security-review.md §4。
PUBKEY_HEX = "a29db60b5953dae9e54cb866607076d9a57e88b6897b24a7b19b4315646057fe"

_PUBKEY_OVERRIDE = [None]  # 仅供单测注入临时密钥对；不读环境变量（防止被环境改写绕过验签）

ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # 32 字符，5 bit/位
PREFIX = "BZSP"
CODE_GROUPS = 3                                   # 前缀后 3 段
CODE_GROUP_LEN = 4                                # 每段 4 位
CODE_BODY_LEN = CODE_GROUPS * CODE_GROUP_LEN      # 12 位 = 60 bit
DEFAULT_SEATS_MAX = 3

V = 1
SCHEME_CODE = "bizspark-code-v1"
SCHEME_POOL = "bizspark-pool-v1"


def set_public_key(pub_hex):
    """**仅供测试**：注入临时公钥。返回原值，便于用完后恢复。"""
    prev = _PUBKEY_OVERRIDE[0]
    _PUBKEY_OVERRIDE[0] = str(pub_hex).strip().lower()
    return prev


def public_key():
    return _PUBKEY_OVERRIDE[0] or PUBKEY_HEX


# --------------------------------------------------------------------------- #
# 规范化（签名与验签必须逐字节一致，两端共用本实现）
# --------------------------------------------------------------------------- #
def canonical(obj):
    """确定性 JSON：键排序、无多余空白、UTF-8。跨平台/跨语言可复现。"""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def code_message(serial, seats_max):
    return ("%s|%s|%d" % (SCHEME_CODE, serial, int(seats_max))).encode("utf-8")


def pool_message(pool):
    """码池消息 = 方案前缀 + 规范化内容的 sha256（与码池条数无关，始终定长）。"""
    body = {k: v for k, v in pool.items() if k != "sig"}
    digest = hashlib.sha256(canonical(body)).hexdigest()
    return ("%s|%s" % (SCHEME_POOL, digest)).encode("utf-8")


# --------------------------------------------------------------------------- #
# 码格式化
# --------------------------------------------------------------------------- #
def normalize_code(raw):
    """把用户输入整理成 `BZSP-XXXX-XXXX-XXXX`；不合法返回 None。

    容忍：小写、空格、多余分隔符、粘贴时带引号/换行；非字母数字一律剔除。
    """
    if not isinstance(raw, str):
        return None
    body = "".join(c for c in raw.upper() if c.isalnum())
    if not body.startswith(PREFIX):
        return None
    body = body[len(PREFIX):]
    if len(body) != CODE_BODY_LEN:
        return None
    if any(c not in ALPHABET for c in body):
        return None
    groups = [body[i:i + CODE_GROUP_LEN] for i in range(0, CODE_BODY_LEN, CODE_GROUP_LEN)]
    return "-".join([PREFIX] + groups)


def is_code_like(raw):
    return normalize_code(raw) is not None


def code_hash(code):
    """码池索引：`sha256(规范化码)` 前 8 字节 hex（16 字符）。"""
    norm = normalize_code(code)
    if norm is None:
        return None
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def full_code_hash(code):
    """凭证里的 `code_hash`（§3.5）：`sha256:<64 hex>`，便于审计与对账。"""
    norm = normalize_code(code)
    if norm is None:
        return None
    return "sha256:" + hashlib.sha256(norm.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# 验签（客户端）
# --------------------------------------------------------------------------- #
def verify_pool_header(pool):
    """客户端侧验签：只验码池整体签名与结构（1 次验签 ~5ms）。

    不逐条验背书——码池可能有上千条，逐条要几秒；单码在**查到时**再验一次即可
    （见 activate.activate），安全性等价：伪造码要么池签名过不了，要么背书过不了。
    """
    if not isinstance(pool, dict) or pool.get("v") != V:
        return False
    codes = pool.get("codes")
    if not isinstance(codes, list) or pool.get("sig") in (None, ""):
        return False
    if not isinstance(pool.get("seats_max"), int):
        return False
    return ed25519.verify(pool.get("sig"), pool_message(pool), public_key())


def verify_pool(pool):
    """**签发侧全量审计**：结构 + 池签名 + 每枚码的背书逐条验。任一不过返回 False。"""
    if not verify_pool_header(pool):
        return False
    codes = pool.get("codes")
    seats_max = pool.get("seats_max")
    if seats_max != DEFAULT_SEATS_MAX:
        return False
    for entry in codes:
        if not isinstance(entry, dict):
            return False
        serial, sig = entry.get("s"), entry.get("sig")
        if not isinstance(serial, str) or not isinstance(sig, str):
            return False
        if len(serial) != 5 or any(c not in ALPHABET for c in serial):
            return False
        if not ed25519.verify(sig, code_message(serial, seats_max), public_key()):
            return False
    return True


def verify_code_attestation(serial, seats_max, sig):
    """单码背书验签（凭证只有 serial / seats_max / sig 三个字段也能独立验）。"""
    return ed25519.verify(sig, code_message(serial, seats_max), public_key())


def sign_bytes(msg, seed_hex):
    """**仅签发工具使用**：给一段 bytes 签名（私钥来自 tools/issue.py 的密钥文件）。"""
    return ed25519.sign(seed_hex, msg)
