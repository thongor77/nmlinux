# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for NMLinux AppImage build."""

import sys
from pathlib import Path

PROJECT = Path(SPECPATH).parent

a = Analysis(
    [str(PROJECT / 'nmlinux' / 'main.py')],
    pathex=[str(PROJECT)],
    binaries=[],
    datas=[
        (str(PROJECT / 'nmlinux' / 'assets'), 'nmlinux/assets'),
        (str(PROJECT / 'data' / 'nmlinux.desktop'), 'data'),
    ],
    hiddenimports=[
        'ptyprocess',
        'ptyprocess.ptyprocess',
        'tftpy',
        'tftpy.TftpClient',
        'tftpy.TftpServer',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
        'PySide6.QtPrintSupport',
        'PySide6.QtDBus',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='nmlinux',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='nmlinux',
)
