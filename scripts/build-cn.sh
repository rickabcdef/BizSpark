#!/usr/bin/env bash
# A-08 双构建之中文版（负责人：A，见 §2.7 双构建产物）
# 产物：中文版安装包。文案用 zh-CN.json 内部自检镜像，逐键对应、不增删键。
# 用法: bash scripts/build-cn.sh
set -euo pipefail

cd "$(dirname "$0")/../apps/desktop"

export BIZSPARK_EDITION=cn
export BIZSPARK_LOCALE=zh-CN
export BIZSPARK_HOST_URL="${BIZSPARK_HOST_URL_CN:-https://static.bizspark.example/cn}"

echo "[build-cn] 1/3 安装前端依赖（B 的 web 工程）"
(cd ../web && npm ci --no-audit --no-fund)

echo "[build-cn] 2/3 构建前端（Vite）"
(cd ../web && npm run build)

echo "[build-cn] 3/3 构建 Tauri 壳 + sidecar，产出中文版安装包"
bash scripts/_build-sidecar.sh
npx tauri build

echo "[build-cn] 完成。校验点：与英文包 9 页一致、无中式字体硬编码、版式不因中文挪动"
