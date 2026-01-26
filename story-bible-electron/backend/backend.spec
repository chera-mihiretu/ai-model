# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec for Exelsias Backend
=====================================
Packages the Python backend with all dependencies for Electron bundling.
"""

import sys
import os
from pathlib import Path

# Get the project root (parent of story-bible-electron)
project_root = Path(SPECPATH).parent.parent

block_cipher = None

# Collect data files
datas = [
    # Include source code modules
    (str(project_root / 'src'), 'src'),
]

# Analysis
a = Analysis(
    ['api_bridge.py'],
    pathex=[
        str(project_root),
        str(project_root / 'src'),
    ],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Core dependencies
        'sqlite3',
        'json',
        'queue',
        'threading',
        'logging',
        'pathlib',
        'csv',
        'io',
        'os',
        
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
        'src.domain',
        'src.domain.usecases',
        'src.domain.usecases.import_parser',
        
        # llama-cpp-python
        'llama_cpp',
        'llama_cpp.llama',
        'llama_cpp.llama_cpp',
        
        # Edge TTS
        'edge_tts',
        'edge_tts.communicate',
        'aiohttp',
        'asyncio',
        'aiosignal',
        'frozenlist',
        'multidict',
        'yarl',
        'async_timeout',
        'charset_normalizer',
        'aiohttp.web',
        
        # Pygame for audio
        'pygame',
        'pygame.mixer',
        
        # Pydantic for models
        'pydantic',
        'pydantic.fields',
        'pydantic_core',
        
        # Transformers/Tokenizers
        'transformers',
        'tokenizers',
        'safetensors',
        'huggingface_hub',
        
        # NLP
        'spacy',
        'nltk',
        
        # Data processing
        'numpy',
        'pandas',
        
        # Other utilities
        'regex',
        'tqdm',
        'requests',
        'certifi',
        'urllib3',
        'packaging',
        'filelock',
        'typing_extensions',
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
        'PySide6',
        'PySide2',
        'wx',
        
        # Exclude test frameworks
        'pytest',
        'unittest',
        
        # Exclude dev tools
        'IPython',
        'jupyter',
        'notebook',
        
        # Exclude unnecessary large packages
        'matplotlib',
        'scipy',
        'sklearn',
        'tensorflow',
        'torch',  # We use llama.cpp, not PyTorch
        'cv2',
        'PIL.ImageTk',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out unnecessary files to reduce size
excluded_patterns = [
    'share/',
    'tcl/',
    'tk/',
    'Include/',
    '__pycache__/',
    '.pyc',
    'test/',
    'tests/',
    '_test.py',
    'test_.py',
]

a.datas = [x for x in a.datas if not any(pattern in x[0] for pattern in excluded_patterns)]

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
    icon=None,
)
