# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Platform detection
IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

# Collect customtkinter assets
datas = []
binaries = []
hiddenimports = ['customtkinter', 'llama_cpp', 'PIL._tkinter_finder']

# Collect customtkinter data contents (themes/fonts)
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collect llama_cpp (native libraries)
tmp_ret = collect_all('llama_cpp')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# --- Platform Specific Configuration ---
app_name = 'StoryBibleApp'
icon_file = None

if IS_WINDOWS:
    # Windows specific settings
    icon_file = 'resources/icon.ico' if os.path.exists('resources/icon.ico') else None
elif IS_MACOS:
    # macOS specific settings
    icon_file = 'resources/icon.icns' if os.path.exists('resources/icon.icns') else None
    app_name = 'StoryBibleApp' # macOS apps are bundles
else:
    # Linux/Other
    icon_file = 'resources/icon.png' if os.path.exists('resources/icon.png') else None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Set to False for windowed app
    disable_windowed_traceback=False,
    argv_emulation=False if IS_WINDOWS or IS_LINUX else True, # Open files on macOS
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)

# Mac OS App Bundle (Only created when running on macOS)
if IS_MACOS:
    app = BUNDLE(
        coll,
        name=f'{app_name}.app',
        icon=icon_file,
        bundle_identifier='com.storybible.app',
    )
