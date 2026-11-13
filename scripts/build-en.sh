#!/usr/bin/env bash
# A-08 双构建之英文版（负责人：A，见 §2.7 双构建产物）
# 产物：英文版安装包。两包 9 页一致；文案唯一来源 en-US.json。
# 用法: bash scripts/build-en.sh
set -euo pipefail

cd "$(dirname "$0")/../apps/desktop"

export BIZSPARK_EDITION=en
export BIZSPARK_LOCALE=en-US
export BIZSPARK_HOST_URL="${BIZSPARK_HOST_URL_EN:-https://static.bizspark.example/en}"

echo "[build-en] 1/3 安装前端依赖（B 的 web 工程）"
(cd ../web && npm ci --no-audit --no-fund)

echo "[build-en] 2/3 构建前端（Vite，9 页面与稿零偏差，由 B 保证）"
(cd ../web && npm run build)

echo "[build-en] 3/3 构建 Tauri 壳 + sidecar，产出英文版安装包"
bash scripts/_build-sidecar.sh
npx tauri build

echo "[build-en] 完成。校验点：安装包内 9 页均为 en 文案、baseline_v1.json 内置"
