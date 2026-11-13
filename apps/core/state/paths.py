# -*- coding: utf-8 -*-
"""state.paths — F-01 统一路径封装（§2.5，负责人：F）

§2.5 规定所有本地文件相对 `appDataDir/com.bizspark.desktop/`，本模块是**唯一**路径来源：
其他模块禁止自己拼路径（A 的 Rust 层通过 get_state.paths 或启动参数取同一份）。

| 用途 | 路径 |
|---|---|
| 全局状态 | state.json |
| 内置库（只读） | resources/baseline_v1.json（随包）/ 开发期仓库 apps/core/data |
| 合并后工作库 | library/current.json |
| delta 备份与日志 | library/deltas/、library/rollback/ |
| 授权凭证 | license.dat |
| 导出默认目录 | $DOCUMENTS/BizSpark/ |
| 崩溃日志（默认关） | logs/crash.log |

铁律：不联网、不写用户数据到日志、不硬删磁盘条目；`baseline_v1.json` 只读。
"""

import os
import sys

APP_DIR_NAME = "com.bizspark.desktop"

# 环境变量覆盖（A 的打包壳 / 开发期 / 测试注入；正常安装版不设置）
ENV_APP_DATA = "BIZSPARK_APP_DATA"
ENV_BASELINE = "BIZSPARK_BASELINE_PATH"
ENV_FALLBACK = "BIZSPARK_FALLBACK_PATH"

_CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # apps/core


def _repo_root():
    p = _CORE_DIR
    while p != os.path.dirname(p):
        if os.path.isdir(os.path.join(p, "apps", "core")):
            return p
        p = os.path.dirname(p)
    return os.getcwd()


def app_data_dir(create=False):
    """§2.5 appDataDir/com.bizspark.desktop/。Windows=%APPDATA%，macOS=Application Support。"""
    override = os.environ.get(ENV_APP_DATA)
    if override:
        base = override
    elif sys.platform.startswith("win"):
        base = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"),
                            APP_DIR_NAME)
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support",
                            APP_DIR_NAME)
    else:
        base = os.path.join(os.environ.get("XDG_DATA_HOME") or
                            os.path.join(os.path.expanduser("~"), ".local", "share"),
                            APP_DIR_NAME)
    if create:
        os.makedirs(base, exist_ok=True)
    return base


def state_path():
    return os.path.join(app_data_dir(), "state.json")


def library_dir(create=False):
    return _sub("library", create)


def current_library_path():
    """合并后工作库（唯一可写库；C 的 load_library 通过 env 指向这里）。"""
    return os.path.join(library_dir(), "current.json")


def deltas_dir(create=False):
    return _sub(os.path.join("library", "deltas"), create)


def rollback_dir(create=False):
    return _sub(os.path.join("library", "rollback"), create)


def license_path():
    """G 的授权凭证（F 只读存在性，不解析、不验签）。"""
    return os.path.join(app_data_dir(), "license.dat")


def logs_dir(create=False):
    return _sub("logs", create)


def crash_log_path():
    return os.path.join(logs_dir(True), "crash.log")


def documents_dir():
    """§2.5 导出默认目录 $DOCUMENTS/BizSpark/。"""
    home = os.path.expanduser("~")
    docs = os.path.join(home, "Documents")
    if not os.path.isdir(docs):
        docs = os.path.join(home, "文档") if os.path.isdir(os.path.join(home, "文档")) else home
    return os.path.join(docs, "BizSpark")


def default_export_dir():
    return documents_dir()


def baseline_readonly_path():
    """内置库只读副本：env > 安装包 resources/ > 开发期仓库 data/。永不写入。"""
    env = os.environ.get(ENV_BASELINE)
    if env and os.path.isfile(env):
        return env
    candidates = [
        os.path.join(app_data_dir(), "resources", "baseline_v1.json"),
        os.path.join(_CORE_DIR, "data", "baseline_v1.json"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return candidates[-1]


def fallback_ideas_path():
    env = os.environ.get(ENV_FALLBACK)
    if env and os.path.isfile(env):
        return env
    packaged = os.path.join(app_data_dir(), "resources", "fallback_ideas.json")
    if os.path.isfile(packaged):
        return packaged
    return os.path.join(_CORE_DIR, "data", "fallback_ideas.json")


def build_mode():
    """A+B：build-mode.txt = cn-selfcheck（未打包默认 en 售卖版）。"""
    for p in (os.path.join(app_data_dir(), "build-mode.txt"),
              os.path.join(_repo_root(), "apps", "web", "public", "build-mode.txt")):
        try:
            with open(p, encoding="utf-8") as f:
                return f.read().strip() or "en"
        except OSError:
            continue
    return "en"


def app_version():
    """从 tauri.conf.json 取版本（唯一来源），失败回退常量。"""
    conf = os.path.join(_repo_root(), "apps", "desktop", "src-tauri", "tauri.conf.json")
    try:
        import json
        with open(conf, encoding="utf-8") as f:
            return str(json.load(f).get("version") or "1.0.0")
    except (OSError, ValueError):
        return "1.0.0"


def _sub(name, create=False):
    p = os.path.join(app_data_dir(create=create), name)
    if create:
        os.makedirs(p, exist_ok=True)
    return p


def ensure_app_dirs():
    """首次启动创建全部目录（§2.5）；已存在则无操作。"""
    app_data_dir(create=True)
    for maker in (library_dir, deltas_dir, rollback_dir, logs_dir):
        maker(create=True)
    return app_data_dir()


def all_paths():
    """供 get_state 回报（A 的 Rust 层/设置页显示用；不含用户内容）。"""
    ensure_app_dirs()
    return {
        "app_data": app_data_dir(),
        "state": state_path(),
        "current_library": current_library_path(),
        "baseline": baseline_readonly_path(),
        "export_dir": default_export_dir(),
        "crash_log": crash_log_path(),
        "build_mode": build_mode(),
        "version": app_version(),
    }
