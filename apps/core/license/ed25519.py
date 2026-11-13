# -*- coding: utf-8 -*-
"""license.ed25519 — Ed25519（RFC 8032）纯 Python 实现（负责人：G，G-02/G-04）

为什么不用第三方库：客户端包要小、离线要稳、构建期不加依赖。本文件只用 hashlib
与整数运算，`verify()` 单次 ~40-70ms，激活与启动各一次（且有进程内缓存，见
activate.py），对 800ms 的 IPC 预算无压力。

本文件提供两个能力：

| 函数 | 谁用 | 说明 |
|---|---|---|
| `sign(seed_hex, msg)` | **仅离线签发工具** `tools/issue.py` | 需要私钥；私钥永不进客户端包 |
| `verify(sig_hex, msg, pub_hex)` | 客户端 | 只做验签，拿不到私钥 |

安全边界（见 docs/security-review.md）：
- 客户端只内置**公钥**（`signature.PUBKEY_HEX`），包内 grep 不到任何私钥材料；
- 验签失败一律静默（返回 False），由调用方决定温和降级，绝不弹错。

正确性：`tests/test_license.py` 用 RFC 8032 §7.1 的 TEST 1/2/3 官方向量逐字节比对。
"""

import hashlib

_P = 2 ** 255 - 19
_Q = 2 ** 252 + 27742317777372353535851937790883648493  # 曲线子群阶 L


def _inv(x):
    return pow(x, _P - 2, _P)


_D = (-121665 * _inv(121666)) % _P
_I = pow(2, (_P - 1) // 4, _P)


def _xrecover(y):
    xx = (y * y - 1) * _inv(_D * y * y + 1)
    x = pow(xx, (_P + 3) // 8, _P)
    if (x * x - xx) % _P != 0:
        x = (x * _I) % _P
    if x % 2 != 0:
        x = _P - x
    return x


_BY = (4 * _inv(5)) % _P
_BX = _xrecover(_BY)
# 扩展坐标 (x, y, z, t)，t = x*y/z
_B = (_BX % _P, _BY % _P, 1, (_BX * _BY) % _P)
_IDENTITY = (0, 1, 1, 0)


def _add(P, Q):
    """扩展坐标点加（RFC 8032 §5.1.4）。"""
    x1, y1, z1, t1 = P
    x2, y2, z2, t2 = Q
    a = ((y1 - x1) * (y2 - x2)) % _P
    b = ((y1 + x1) * (y2 + x2)) % _P
    c = (t1 * 2 * _D * t2) % _P
    d = (z1 * 2 * z2) % _P
    e = b - a
    f = d - c
    g = d + c
    h = b + a
    return ((e * f) % _P, (g * h) % _P, (f * g) % _P, (e * h) % _P)


def _mul(P, e):
    """标量乘（倍加，递归）。e=0 返回单位元。"""
    if e == 0:
        return _IDENTITY
    if e == 1:
        return P
    half = _mul(P, e // 2)
    out = _add(half, half)
    if e & 1:
        out = _add(out, P)
    return out


def _encode_point(P):
    x, y, z, _t = P
    zi = _inv(z)
    x = (x * zi) % _P
    y = (y * zi) % _P
    bits = [(y >> i) & 1 for i in range(255)] + [x & 1]
    return bytes(sum(bits[i * 8 + j] << j for j in range(8)) for i in range(32))


def _decode_point(s):
    """解压 32 字节点；非法编码返回 None（不抛异常）。"""
    if not isinstance(s, (bytes, bytearray)) or len(s) != 32:
        return None
    y = int.from_bytes(s, "little") & ((1 << 255) - 1)
    sign = s[31] >> 7
    if y >= _P:
        return None
    x = _xrecover(y)
    if (x & 1) != sign:
        x = _P - x
    P = (x, y, 1, (x * y) % _P)
    # 曲线方程校验：-x^2 + y^2 = 1 + d*x^2*y^2
    xx = (x * x) % _P
    yy = (y * y) % _P
    if (yy - xx - 1 - _D * xx * yy) % _P != 0:
        return None
    return P


def _clamp(h32):
    """RFC 8032 §5.1.5 私钥标量钳位。"""
    a = int.from_bytes(h32, "little")
    a &= (1 << 254) - 8   # 清低 3 位
    a |= 1 << 254         # 清最高位、置次高位
    return a


def _seed_bytes(seed_hex):
    if isinstance(seed_hex, (bytes, bytearray)):
        raw = bytes(seed_hex)
    else:
        raw = bytes.fromhex(str(seed_hex).strip())
    if len(raw) != 32:
        raise ValueError("ed25519 seed must be 32 bytes")
    return raw


def public_key(seed_hex):
    """由私钥种子导出公钥（32 字节 hex）。仅签发工具使用。"""
    seed = _seed_bytes(seed_hex)
    h = hashlib.sha512(seed).digest()
    a = _clamp(h[:32])
    return _encode_point(_mul(_B, a)).hex()


def sign(seed_hex, msg):
    """签名，返回 128 字符 hex（64 字节 R||S）。msg 为 bytes。"""
    if not isinstance(msg, (bytes, bytearray)):
        raise TypeError("msg must be bytes")
    seed = _seed_bytes(seed_hex)
    h = hashlib.sha512(seed).digest()
    a = _clamp(h[:32])
    prefix = h[32:]
    A = _encode_point(_mul(_B, a))
    r = int.from_bytes(hashlib.sha512(prefix + bytes(msg)).digest(), "little") % _Q
    R = _encode_point(_mul(_B, r))
    k = int.from_bytes(hashlib.sha512(R + A + bytes(msg)).digest(), "little") % _Q
    S = (r + k * a) % _Q
    return (R + S.to_bytes(32, "little")).hex()


def verify(sig_hex, msg, pub_hex):
    """验签。任何异常/格式问题都返回 False（调用方据此静默降级）。"""
    try:
        if not isinstance(msg, (bytes, bytearray)):
            return False
        sig = bytes.fromhex(str(sig_hex).strip())
        pub = bytes.fromhex(str(pub_hex).strip())
    except (TypeError, ValueError):
        return False
    if len(sig) != 64 or len(pub) != 32:
        return False
    A = _decode_point(pub)
    if A is None:
        return False
    R = _decode_point(sig[:32])
    if R is None:
        return False
    S = int.from_bytes(sig[32:], "little")
    if S >= _Q:  # 拒绝可延展签名
        return False
    k = int.from_bytes(hashlib.sha512(sig[:32] + pub + bytes(msg)).digest(),
                       "little") % _Q
    left = _mul(_B, S)
    right = _add(R, _mul(A, k))
    return _encode_point(left) == _encode_point(right)
