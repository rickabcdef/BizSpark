#!/usr/bin/env bash
# A-09 构建期辅助：把 Python sidecar 打成单文件可执行（负责人：A）
# 被 build-en.sh / build-cn.sh / pack.sh 调用。
# 产物: apps/desktop/src-tauri/binaries/bizspark-core(.exe)，供 tauri externalBin 随包分发。
set -euo pipefail

cd "$(dirname "$0")/../apps/core"

echo "[sidecar] 1/2 安装构建期依赖（仅 reportlab + pyinstaller，见 requirements.txt）"
python3 -m pip install -r requirements.txt --quiet

echo "[sidecar] 2/2 PyInstaller 单文件打包"
# G 审遗留修复（PM，2026-11-13）：显式排除开发/签发工具与测试目录，确保不随包分发
python3 -m PyInstaller \
    --onefile \
    --name bizspark-core \
    --distpath ../desktop/src-tauri/binaries \
    --exclude-module tkinter \
    --exclude-module unittest \
    --exclude-module tools \
    --exclude-module tests \
    --exclude-module license.tools \
    main.py

echo "[sidecar] 完成: apps/desktop/src-tauri/binaries/bizspark-core"
