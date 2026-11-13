# -*- coding: utf-8 -*-
"""qa/security/release_preflight.py — 发布前授权自检（G-06 / 上架前置）

检查 5 件事，任何一项 FAIL 都不许发版：

1. `apps/core/license/pool.json` 存在、能被内置公钥验过、且 **demo 必须为 false**
   （演示池的码和明文清单在仓库/文档里出现过，上架必须重新签发）；
2. `signature.py:PUBKEY_HEX` 不是全零（忘了填公钥会导致所有码都验不过）；
3. 仓库里没有**明文激活码**（`BZSP-XXXX-XXXX-XXXX`）——除了设计稿/文档里的样例与 locales；
4. 仓库里没有**私钥材料**（`*.key`、`BEGIN PRIVATE KEY`、64 hex 单行种子）；
5. `tools/`（签发工具，含私钥路径逻辑）**不参与打包**：`scripts/pack.sh` 里有排除。

用法：`python qa/security/release_preflight.py`
"""

import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
CORE = os.path.join(REPO, "apps", "core")
sys.path.insert(0, CORE)

from license import signature as sig  # noqa: E402

POOL = os.path.join(CORE, "license", "pool.json")
CODE_RE = re.compile(r"BZSP-[2-9A-HJKMNP-TV-Z]{4}-[2-9A-HJKMNP-TV-Z]{4}-[2-9A-HJKMNP-TV-Z]{4}")
SELF = "qa/security/release_preflight.py"   # 本脚本自身含正则与示例串，跳过自检
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

# 允许出现"码样例"的地方（设计稿、文档、文案资源：§3.6 明确要求激活码样例不翻译）
CODE_ALLOWED = ("ui/", "docs/", "apps/web/src/locales/", "qa/security/", "apps/core/tests/")
SKIP_DIRS = {".git", "node_modules", "__pycache__", "dist", "target", ".workbuddy", "out"}

failures, warnings = [], []
ALLOW_DEMO = "--allow-demo" in sys.argv   # 开发期跑法；发版必须不带这个开关


def scan_files():
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            yield os.path.join(root, name)


def rel(path):
    return os.path.relpath(path, REPO).replace("\\", "/")


def check_pool():
    if not os.path.isfile(POOL):
        failures.append("缺少 apps/core/license/pool.json（先跑 tools/issue.py new-pool）")
        return
    try:
        with open(POOL, encoding="utf-8") as f:
            pool = json.load(f)
    except (OSError, ValueError) as exc:
        failures.append("pool.json 读不出来：%s" % exc)
        return
    if not sig.verify_pool(pool):
        failures.append("码池验签失败（公钥与签发私钥不匹配，或文件被改过）")
    if pool.get("demo"):
        msg = ("码池 demo=true：这是演示池，上架前必须用 tools/issue.py new-pool 重新签发"
               "（并把 demo 去掉），否则演示码等同于后门")
        if ALLOW_DEMO:
            warnings.append(msg + "（本次以 --allow-demo 运行，开发期放行）")
        else:
            failures.append(msg)
    if not pool.get("count"):
        failures.append("码池为空")
    if pool.get("pool_id", "").endswith("-dev"):
        warnings.append("pool_id=%s 看起来是开发池" % pool.get("pool_id"))


def check_pubkey():
    if not re.fullmatch(r"[0-9a-f]{64}", sig.PUBKEY_HEX or ""):
        failures.append("signature.py:PUBKEY_HEX 格式不对")
    elif set(sig.PUBKEY_HEX) == {"0"}:
        failures.append("signature.py:PUBKEY_HEX 还是全零占位")


def check_plaintext_codes():
    hits = []
    for path in scan_files():
        r = rel(path)
        if r.startswith(CODE_ALLOWED) or r == SELF:
            continue
        if not r.endswith((".py", ".json", ".txt", ".yml", ".yaml", ".sh", ".vue", ".ts")):
            continue
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            continue
        for m in CODE_RE.finditer(text):
            if "XXXX" in m.group(0):   # 设计稿/文档里的格式样例（未填态）
                continue
            hits.append("%s → %s" % (r, m.group(0)))
    if hits:
        failures.extend("仓库里出现明文激活码：" + h for h in hits[:5])


def check_private_key():
    hits = []
    for path in scan_files():
        r = rel(path)
        if r == SELF:      # 脚本自身写有 PEM 头字面量
            continue
        if r.endswith(".key") or r.endswith(".pem"):
            hits.append(r)
            continue
        if not r.endswith((".py", ".txt", ".md", ".json", ".sh")):
            continue
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            continue
        if "BEGIN PRIVATE KEY" in text or "BEGIN OPENSSH PRIVATE KEY" in text:
            hits.append(r + "（含 PEM 私钥块）")
            continue
        for line in text.splitlines():
            if HEX64_RE.match(line.strip()) and len(line.strip()) == 64:
                # 只有整行 64 hex 才可能是种子/私钥；普通哈希常量都在代码行里
                hits.append(r + "（整行 64 hex，疑似种子）")
                break
    if hits:
        failures.extend("疑似私钥材料：" + h for h in hits[:5])


def check_pack_excludes_tools():
    pack = os.path.join(REPO, "scripts", "pack.sh")
    if not os.path.isfile(pack):
        warnings.append("scripts/pack.sh 未找到，无法确认 tools/ 与 license/ 的裁剪")
        return
    with open(pack, encoding="utf-8", errors="ignore") as f:
        text = f.read()
    if "tools" not in text:
        warnings.append("pack.sh 里没看到排除 tools/ —— 签发工具绝不能进包（A2）")
    if "license" not in text:
        warnings.append("pack.sh 里没看到 store 构建裁掉 license/ —— T-42 会不过（A2）")


def main():
    print("== 发布前授权自检（G）==")
    for fn in (check_pool, check_pubkey, check_plaintext_codes,
               check_private_key, check_pack_excludes_tools):
        fn()
    for w in warnings:
        print("  .. WARN %s" % w)
    if failures:
        for f in failures:
            print("  FAIL %s" % f)
        print("结果：FAIL（%d 项，禁止发版）" % len(failures))
        return 1
    print("结果：PASS（码池/公钥/明文码/私钥/打包排除 全部通过）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
