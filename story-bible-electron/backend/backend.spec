# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec for Story Bible Pro Backend
=============================================
Packages the Python backend with all dependencies for Electron bundling.
"""

import sys
from pathlib import Path

# Get the project root
project_root = Path(SPECPATH).parent.parent

block_cipher = None

# Analysis
a = Analysis(
    ['api_bridge.py'],
    pathex=[
        str(project_root),
        str(project_root / 'src'),
    ],
    binaries=[],
    datas=[
        # Include source code
        (str(project_root / 'src'), 'src'),
        # Include config files
        (str(project_root / 'src' / 'config'), 'src/config'),
    ],
    hiddenimports=[
        # Core dependencies
        'sqlite3',
        'json',
        'queue',
        'threading',
        'logging',
        'pathlib',
        
        # Project modules
        'src',
        'src.database',
        'src.database.db_manager',
        'src.services',
        'src.services.ai_engine',
        'src.services.tts_engine',
        'src.services.prompts',
        'src.config',
        'src.config.manager',
        
        # llama-cpp-python
        'llama_cpp',
        
        # Edge TTS
        'edge_tts',
        'aiohttp',
        'asyncio',
        
        # Pygame for audio
        'pygame',
        
        # pyttsx3 fallback
        'pyttsx3',
        
        # Pydantic for models
        'pydantic',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude GUI frameworks (not needed for backend)
        'PyQt6',
        'PyQt5',
        'tkinter',
        'customtkinter',
        
        # Exclude test frameworks
        'pytest',
        'unittest',
        
        # Exclude dev tools
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out unnecessary files
a.datas = [x for x in a.datas if not x[0].startswith('share/')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='api_bridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for stdin/stdout communication
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

