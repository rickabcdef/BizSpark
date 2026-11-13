#!/usr/bin/env bash
# A-14/A-15：构建期价格注入（负责人：A，契约 K-11 / P-14）
# 六构建目标共用同一份 config/pricing.json：
#   1 build:store-win-en    2 build:store-mac-en
#   3 build:reseller-win-en 4 build:reseller-mac-en
#   5 build:selfcheck-cn-win 6 build:selfcheck-cn-mac
# 注入产物：
#   apps/web/public/pricing.js  → window.BIZSPARK_PRICING（前端唯一运行时价格源）
#   apps/web/public/build-mode.txt → 构建目标标记（A-08 双构建机制）
# 用法: bash scripts/inject-pricing.sh [target]
#   target: store-win-en | store-mac-en | reseller-win-en | reseller-mac-en
#           selfcheck-cn-win | selfcheck-cn-mac（默认 store-win-en）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/config/pricing.json"
TARGET="${1:-store-win-en}"

case "$TARGET" in
  store-win-en|store-mac-en)    MODE=store;    EDITION=en; FEATURE=store ;;
  reseller-win-en|reseller-mac-en) MODE=reseller; EDITION=en; FEATURE=reseller ;;
  selfcheck-cn-win|selfcheck-cn-mac) MODE=selfcheck; EDITION=cn; FEATURE=none ;;
  *) echo "[inject] ❌ 未知构建目标: $TARGET（六目标见脚本头部）"; exit 1 ;;
esac

# 校验配置合法（契约 K-11）
python3 - "$SRC" "$TARGET" << 'PYEOF'
import json, sys
cfg = json.load(open(sys.argv[1], encoding='utf-8'))
target = sys.argv[2]
mode = cfg.get("display_mode")
if mode not in ("hidden", "visible"):
    sys.exit("[inject] ❌ display_mode 必须是 hidden|visible")
if mode == "visible":
    if not isinstance(cfg.get("amount"), (int, float)):
        sys.exit("[inject] ❌ display_mode=visible 时 amount 必须为数字")
else:
    if cfg.get("amount") is not None:
        sys.exit("[inject] ❌ display_mode=hidden 时 amount 必须为 null（首版契约）")
if cfg.get("model") not in ("one-time", "monthly", "yearly", "seat"):
    sys.exit("[inject] ❌ model 枚举: one-time|monthly|yearly|seat")
print(f"[inject] ✓ 配置合法（display_mode={mode}, model={cfg.get('model')}, target={target}）")
PYEOF

OUT_DIR="$ROOT/apps/web/public"
mkdir -p "$OUT_DIR"

# 生成运行时价格源：渲染器零硬编码，金额全部由本文件动态提供
python3 - "$SRC" "$OUT_DIR/pricing.js" "$TARGET" << 'PYEOF'
import json, sys
cfg = json.load(open(sys.argv[1], encoding='utf-8'))
out, target = sys.argv[2], sys.argv[3]
payload = {k: cfg[k] for k in ("display_mode", "amount", "currency", "model", "billing_note")}
with open(out, "w", encoding="utf-8") as f:
    f.write("// 自动生成：构建期由 scripts/inject-pricing.sh 写入，勿手改；改价请改 config/pricing.json\n")
    f.write("// 契约 K-11 / P-14：唯一价格源，六构建目标共用同一份配置\n")
    f.write(f"window.BIZSPARK_PRICING = {json.dumps(payload, ensure_ascii=False)};\n")
    f.write(f"window.BIZSPARK_BUILD_TARGET = {json.dumps(target)};\n")
print(f"[inject] ✓ 写入 {out}")
PYEOF

printf "%s\n%s\n%s\n" "$TARGET" "$EDITION" "$FEATURE" > "$OUT_DIR/build-mode.txt"
echo "[inject] ✓ 写入 $OUT_DIR/build-mode.txt (target=$TARGET edition=$EDITION feature=$FEATURE)"
echo "[inject] 完成：改价只改 config/pricing.json 后重跑本脚本（或重跑构建），全端生效"
