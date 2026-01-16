# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file para Wsi Break Time.
Execute com: pyinstaller build.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Caminhos
ROOT_DIR = Path(SPECPATH)
SRC_DIR = ROOT_DIR / 'src'
RESOURCES_DIR = ROOT_DIR / 'resources'

a = Analysis(
    [str(SRC_DIR / 'main.py')],
    pathex=[str(ROOT_DIR), str(SRC_DIR)],
    binaries=[],
    datas=[
        (str(RESOURCES_DIR / 'icons'), 'resources/icons'),
        (str(RESOURCES_DIR / 'sounds'), 'resources/sounds'),
        (str(SRC_DIR / 'app.py'), '.'),
        (str(SRC_DIR / 'settings.py'), '.'),
        (str(SRC_DIR / 'timer_manager.py'), '.'),
        (str(SRC_DIR / 'tray_icon.py'), '.'),
        (str(SRC_DIR / 'overlay.py'), '.'),
    ],
    hiddenimports=[
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'app',
        'settings',
        'timer_manager',
        'tray_icon',
        'overlay',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WsiBreakTime',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sem janela de console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(RESOURCES_DIR / 'icons' / 'app_icon.ico') if (RESOURCES_DIR / 'icons' / 'app_icon.ico').exists() else None,
)
