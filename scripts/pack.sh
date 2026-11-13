#!/usr/bin/env bash
# A-09 打包（负责人：A，见 §10 打包/签名/上架清单）
# 产物：Windows MSIX/NSIS 安装包（Store 包 grep 无中文校验由 H 验收，包体 ≤80MB）
# 用法: BIZSPARK_EDITION=en bash scripts/pack.sh   （或 cn）
set -euo pipefail

EDITION="${BIZSPARK_EDITION:-en}"

echo "[pack] 1/4 金额门禁 T-59（契约 P-14：价格不进包）"
bash scripts/check-no-price.sh

echo "[pack] 2/4 价格注入（六构建目标共用 config/pricing.json）"
bash scripts/inject-pricing.sh "${BIZSPARK_TARGET:-store-win-en}"

echo "[pack] 3/4 构建双构建产物之一（edition=$EDITION）"
bash "scripts/build-${EDITION}.sh"

echo "[pack] 4/4 校验包体（≤80MB 红线）"
APP_DIR="apps/desktop/src-tauri/target/release/bundle"
BIN=$(find "$APP_DIR" -type f \( -name "*.exe" -o -name "*.msix" -o -name "*.msi" \) | head -1)
if [ -n "${BIN:-}" ]; then
  SIZE_MB=$(( $(stat -c%s "$BIN") / 1024 / 1024 ))
  echo "[pack] 产物: $BIN ($SIZE_MB MB)"
  if [ "$SIZE_MB" -gt 80 ]; then
    echo "[pack] ❌ 包体超 80MB 红线，禁止发布"; exit 1
  fi
else
  echo "[pack] ⚠️ 未找到安装包产物，请检查 tauri build 输出"
fi

echo "[pack] 签名（如已配置证书）"
bash scripts/sign.sh || true

echo "[pack] 完成"
