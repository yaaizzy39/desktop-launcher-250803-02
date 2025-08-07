# -*- mode: python ; coding: utf-8 -*-

# バージョン情報を読み込み
import sys
sys.path.append('.')
from version import __version__

a = Analysis(
    ['launcher\\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('launcher\\icons', 'icons'),
        ('app_icon.ico', '.'),
    ],
    hiddenimports=[
        'ctypes',
        'ctypes.wintypes',
        '_ctypes',
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'winreg',
        'win32com',
        'win32com.client',
        'win32com.shell',
        'win32api',
        'win32con'
    ],
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
    name='iconLaunch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon='app_icon.ico',
    version=f'version_info.py',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='iconLaunch',
)
