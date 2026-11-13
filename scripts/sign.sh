#!/usr/bin/env bash
# A-09/A-10 签名（负责人：A，见 §10；W5 签名任务 A-09 签名阶段启用）
# 需要环境变量（由发布机注入，不入库）：
#   BIZSPARK_SIGN_PFX     证书文件路径
#   BIZSPARK_SIGN_PWD     证书密码
set -euo pipefail

if [ -z "${BIZSPARK_SIGN_PFX:-}" ] || [ -z "${BIZSPARK_SIGN_PWD:-}" ]; then
  echo "[sign] 未配置签名证书（BIZSPARK_SIGN_PFX / BIZSPARK_SIGN_PWD），跳过签名（开发构建允许）"
  exit 0
fi

APP_DIR="apps/desktop/src-tauri/target/release/bundle"
for BIN in $(find "$APP_DIR" -type f \( -name "*.exe" -o -name "*.msix" \)); do
  echo "[sign] signtool: $BIN"
  signtool sign //fd SHA256 //f "$BIZSPARK_SIGN_PFX" //p "$BIZSPARK_SIGN_PWD" //tr http://timestamp.digicert.com //td SHA256 "$BIN"
done

echo "[sign] 完成"
