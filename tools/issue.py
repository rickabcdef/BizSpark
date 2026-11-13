# -*- coding: utf-8 -*-
"""tools/issue.py — 离线签发工具（负责人：G，G-02）

**这个文件不进客户端包**（也永远不要打进 PyInstaller/MSIX）。它持有私钥，只有你能跑。

用法
----
    # 1) 首次：生成签发密钥（默认落在 %APPDATA%/BizSpark-issuer/issuer.key，权限 600）
    python tools/issue.py keygen
    #    → 打印公钥；把它填进 apps/core/license/signature.py 的 PUBKEY_HEX

    # 2) 生成码池：N 枚码，写入客户端要打包的 pool.json；明文码写到私有文件里备售
    python tools/issue.py new-pool --count 500 --pool-id 2026-12
    #    → apps/core/license/pool.json（可提交/可打包）
    #    → %APPDATA%/BizSpark-issuer/codes-2026-12.txt（**不要提交、不要进包**）

    # 3) 审计：逐条验池签名与每枚码的背书
    python tools/issue.py verify

    # 4) 查某枚码是否属于某池（客服核对用，不泄露其它码）
    python tools/issue.py check --pool apps/core/license/pool.json BZSP-XXXX-XXXX-XXXX

密钥安全
--------
- 私钥文件权限 600；建议离线机器/加密盘保存，并单独备份（丢了只能重新签发，旧码全废）。
- 轮换流程：`keygen` → 改 `signature.py:PUBKEY_HEX` → `new-pool` → 重新打包；
  旧池作废（旧码激活会走 `E_LICENSE_BAD_CODE`，故轮换只在上架前做）。
"""

import argparse
import json
import os
import secrets
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE = os.path.join(os.path.dirname(_HERE), "apps", "core")
sys.path.insert(0, _CORE)

from license import ed25519, signature as sig  # noqa: E402

DEFAULT_KEY_DIR = os.path.join(
    os.environ.get("APPDATA") or os.path.expanduser("~"), "BizSpark-issuer")
DEFAULT_KEY = os.path.join(DEFAULT_KEY_DIR, "issuer.key")
DEFAULT_POOL = os.path.join(_CORE, "license", "pool.json")


# --------------------------------------------------------------------------- #
# 密钥
# --------------------------------------------------------------------------- #
def _write_private(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def load_key(path=DEFAULT_KEY):
    with open(path, encoding="utf-8") as f:
        seed = f.read().strip()
    if len(seed) != 64:
        raise SystemExit("issuer key looks broken: %s" % path)
    return seed


def cmd_keygen(args):
    path = args.key or DEFAULT_KEY
    if os.path.exists(path) and not args.force:
        raise SystemExit("key already exists: %s（确需覆盖请加 --force，旧码将全部失效）" % path)
    seed = secrets.token_hex(32)
    pub = ed25519.public_key(seed)
    _write_private(path, seed + "\n")
    print("private key : %s  (mode 600, never ship)" % path)
    print("public key  : %s" % pub)
    print("→ 把它填进 apps/core/license/signature.py 的 PUBKEY_HEX，再跑 new-pool")
    return 0


# --------------------------------------------------------------------------- #
# 码池
# --------------------------------------------------------------------------- #
def _random_code():
    """12 位随机体 + 品牌前缀，4 段展示。serial 另取 5 位（只进背书消息）。"""
    body = "".join(secrets.choice(sig.ALPHABET) for _ in range(sig.CODE_BODY_LEN))
    serial = "".join(secrets.choice(sig.ALPHABET) for _ in range(5))
    groups = [body[i:i + 4] for i in range(0, sig.CODE_BODY_LEN, 4)]
    return "-".join([sig.PREFIX] + groups), serial


def build_pool(count, seats_max, seed, pool_id, demo=False):
    codes, entries, seen = [], [], set()
    for _ in range(count):
        while True:
            code, serial = _random_code()
            h = sig.code_hash(code)
            if h and h not in seen:
                seen.add(h)
                break
        attest = ed25519.sign(seed, sig.code_message(serial, seats_max))
        entries.append({"h": h, "s": serial, "sig": attest})
        codes.append(code)
    pool = {
        "v": sig.V,
        "pool_id": pool_id,
        "demo": bool(demo),
        "alg": "ed25519+sha256-8",
        "seats_max": seats_max,
        "count": len(entries),
        "issued_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "codes": sorted(entries, key=lambda e: e["h"]),
    }
    pool["sig"] = ed25519.sign(seed, sig.pool_message(pool))
    return pool, codes


def cmd_new_pool(args):
    seed = load_key(args.key or DEFAULT_KEY)
    pub = ed25519.public_key(seed)
    if args.pubkey and args.pubkey.strip().lower() != pub:
        raise SystemExit("给定的公钥与私钥不匹配；先更新 signature.py 的 PUBKEY_HEX")
    count = max(1, int(args.count))
    pool, codes = build_pool(count, sig.DEFAULT_SEATS_MAX, seed, args.pool_id, args.demo)

    out = args.out or DEFAULT_POOL
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pool, f, ensure_ascii=False, sort_keys=True, indent=1)
        f.write("\n")

    codes_out = args.codes_out or os.path.join(
        os.path.dirname(args.key or DEFAULT_KEY), "codes-%s.txt" % args.pool_id)
    _write_private(codes_out, "\n".join(codes) + "\n")

    # 自检：写出去的池必须能被内置公钥验过（否则就是签发/验签两边跑偏了）
    with open(out, encoding="utf-8") as f:
        reloaded = json.load(f)
    prev = sig.set_public_key(pub)
    try:
        ok = sig.verify_pool(reloaded)
    finally:
        sig.set_public_key(prev)
    print("pool        : %s  (%d codes, seats_max=%d)" % (out, len(codes), sig.DEFAULT_SEATS_MAX))
    print("codes file  : %s  (private — do NOT commit / do NOT ship)" % codes_out)
    print("self-check  : %s" % ("OK" if ok else "FAILED — 公钥没填对？"))
    if args.demo:
        print("demo pool   : 这是演示池（pool.json 里 demo=true）；发布前必须重新签发正式池")
    return 0 if ok else 1


def cmd_verify(args):
    path = args.pool or DEFAULT_POOL
    with open(path, encoding="utf-8") as f:
        pool = json.load(f)
    ok = sig.verify_pool(pool)
    print("pool     : %s" % path)
    print("pool_id  : %s | codes: %s | seats_max: %s | demo: %s"
          % (pool.get("pool_id"), pool.get("count"), pool.get("seats_max"), pool.get("demo")))
    print("verify   : %s" % ("OK（池签名 + 每枚码背书全部通过）" if ok else "FAILED"))
    return 0 if ok else 1


def cmd_check(args):
    path = args.pool or DEFAULT_POOL
    with open(path, encoding="utf-8") as f:
        pool = json.load(f)
    if not sig.verify_pool(pool):
        raise SystemExit("pool signature invalid: %s" % path)
    h = sig.code_hash(args.code)
    hit = next((e for e in pool.get("codes") or [] if e.get("h") == h), None)
    print("code     : %s" % (sig.normalize_code(args.code) or "(format invalid)"))
    print("in pool  : %s" % ("yes — serial " + hit["s"] if hit else "no"))
    return 0 if hit else 2


def main(argv=None):
    p = argparse.ArgumentParser(description="BizSpark 离线签发工具（私钥不进客户端包）")
    sub = p.add_subparsers(dest="cmd", required=True)

    k = sub.add_parser("keygen", help="生成签发密钥对（私钥落盘，公钥填进 signature.py）")
    k.add_argument("--key", help="私钥路径（默认 %s）" % DEFAULT_KEY)
    k.add_argument("--force", action="store_true")
    k.set_defaults(func=cmd_keygen)

    n = sub.add_parser("new-pool", help="签发码池 + 明文码清单")
    n.add_argument("--count", default=200)
    n.add_argument("--pool-id", default=time.strftime("%Y-%m"))
    n.add_argument("--key", help="私钥路径")
    n.add_argument("--out", help="pool.json 输出路径（默认 apps/core/license/pool.json）")
    n.add_argument("--codes-out", help="明文码输出路径（默认与私钥同目录）")
    n.add_argument("--pubkey", help="顺带校验 signature.py 里的公钥是否匹配私钥")
    n.add_argument("--demo", action="store_true", help="标记为演示池（发布构建不允许）")
    n.set_defaults(func=cmd_new_pool)

    v = sub.add_parser("verify", help="审计码池签名与每条背书")
    v.add_argument("--pool")
    v.set_defaults(func=cmd_verify)

    c = sub.add_parser("check", help="查单码是否属于某池（客服核对）")
    c.add_argument("code")
    c.add_argument("--pool")
    c.set_defaults(func=cmd_check)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
