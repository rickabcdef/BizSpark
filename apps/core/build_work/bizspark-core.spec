# -*- mode: python ; coding: utf-8 -*-

# PM 2026-11-27：reportlab 在 lib.utils 里懒导入 PIL，PyInstaller 静态分析抓不到，
# 产物缺 PIL 二进制 → PDF 生成即 ImportError。collect_all 强制收编全量。
from PyInstaller.utils.hooks import collect_all
_rb_d, _rb_b, _rb_h = collect_all('reportlab')
_pil_d, _pil_b, _pil_h = collect_all('PIL')

a = Analysis(
    ['D:/XiangMu/Project/BizSpark/apps/core/main.py'],
    pathex=['D:/XiangMu/Project/BizSpark/apps/core'],
    binaries=_rb_b + _pil_b,
    datas=[('D:/XiangMu/Project/BizSpark/apps/core/data', 'data'), ('D:/XiangMu/Project/BizSpark/apps/core/license/pool.json', 'license')] + _rb_d + _pil_d,
    hiddenimports=_rb_h + _pil_h,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='bizspark-core',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='bizspark-core',
)
