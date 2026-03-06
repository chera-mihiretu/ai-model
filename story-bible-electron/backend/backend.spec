# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec for Exelsias Backend (OPTIMIZED)
==================================================
Packages the Python backend with minimal dependencies for smaller build size.
IMPORTANT: Only includes packages that are actually used in the codebase.
"""

import sys
import os
from pathlib import Path

# Get the project root (parent of story-bible-electron)
project_root = Path(SPECPATH).parent.parent

# Get the virtual environment site-packages path
# Try common venv locations
if (project_root / 'venv' / 'Lib' / 'site-packages').exists():
    venv_site_packages = project_root / 'venv' / 'Lib' / 'site-packages'
elif (project_root / 'deskapp' / 'Lib' / 'site-packages').exists():
    venv_site_packages = project_root / 'deskapp' / 'Lib' / 'site-packages'
else:
    # Fallback to system Python
    import site
    venv_site_packages = Path(site.getsitepackages()[0])

# Find llama_cpp lib directory with DLLs
llama_cpp_lib = venv_site_packages / 'llama_cpp' / 'lib'

block_cipher = None

# Collect binary files (DLLs) - only llama_cpp DLLs needed
binaries = []
if llama_cpp_lib.exists():
    for dll in llama_cpp_lib.glob('*.dll'):
        binaries.append((str(dll), 'llama_cpp/lib'))

# Collect data files - minimal set
datas = [
    # Include source code modules
    (str(project_root / 'src'), 'src'),
    # Include only llama_cpp core (required for model loading)
    (str(venv_site_packages / 'llama_cpp'), 'llama_cpp'),
]

# Analysis with MINIMAL hidden imports (only what's actually used)
a = Analysis(
    ['api_bridge.py'],
    pathex=[
        str(project_root),
        str(project_root / 'src'),
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        # Core Python modules
        'sqlite3',
        'json',
        'queue',
        'threading',
        'logging',
        'pathlib',
        'csv',
        'io',
        'os',
        'platform',
        'subprocess',
        'tempfile',
        're',
        
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
        
        # llama-cpp-python (REQUIRED for AI)
        'llama_cpp',
        'llama_cpp.llama',
        'llama_cpp.llama_cpp',
        
        # Edge TTS (REQUIRED for cloud speech)
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
        
        # Piper TTS (REQUIRED for local/offline speech)
        'piper',
        'piper.voice',
        'piper.download',
        'onnxruntime',
        
        # Pygame for audio playback (REQUIRED for TTS)
        'pygame',
        'pygame.mixer',
        
        # Pydantic for data models (REQUIRED)
        'pydantic',
        'pydantic.fields',
        'pydantic_core',
        
        # Numpy (required by llama-cpp-python)
        'numpy',
        
        # EPUB support (for import feature)
        'ebooklib',
        'ebooklib.epub',
        
        # Minimal utilities (only what's actually imported)
        'regex',
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
        # ========================================
        # GUI frameworks (not needed - using Electron)
        # ========================================
        'PyQt6',
        'PyQt5',
        'tkinter',
        'customtkinter',
        'PySide6',
        'PySide2',
        'wx',
        'kivy',
        
        # ========================================
        # REMOVED - Not used in codebase (saves ~500MB+)
        # ========================================
        'transformers',      # Not imported anywhere
        'tokenizers',        # Not imported anywhere
        'safetensors',       # Not imported anywhere
        'huggingface_hub',   # Not imported anywhere
        'spacy',             # Not imported anywhere
        'nltk',              # Not imported anywhere
        'pandas',            # Not imported anywhere
        'PIL',               # Frontend handles images
        'pillow',            # Frontend handles images
        'fpdf2',             # Not imported anywhere
        'fpdf',              # Not imported anywhere
        'soundfile',         # Not needed - edge-tts handles audio
        'tqdm',              # Not imported anywhere
        'PyYAML',            # Not imported anywhere
        'yaml',              # Not imported anywhere
        
        # ========================================
        # Heavy ML/AI frameworks (we use llama.cpp)
        # ========================================
        'torch',
        'torchvision',
        'torchaudio',
        'tensorflow',
        'keras',
        'jax',
        'flax',
        'sklearn',
        'scikit-learn',
        'scipy',
        'sympy',
        
        # ========================================
        # Development/Testing tools
        # ========================================
        'pytest',
        'unittest',
        'nose',
        'IPython',
        'jupyter',
        'notebook',
        'jupyterlab',
        'debugpy',
        'coverage',
        'black',
        'flake8',
        'pylint',
        'mypy',
        
        # ========================================
        # Visualization (not needed)
        # ========================================
        'matplotlib',
        'seaborn',
        'plotly',
        'bokeh',
        'altair',
        'cv2',
        'opencv',
        
        # ========================================
        # Other unnecessary packages
        # ========================================
        'setuptools',
        'pip',
        'wheel',
        'distutils',
        'docutils',
        'sphinx',
        'email',
        'html',
        'xml',
        'ctypes.test',
        'lib2to3',
        'curses',
        'ensurepip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Aggressively filter out unnecessary files to reduce size
excluded_patterns = [
    # Test and documentation
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
    '.pyi',        # Type stubs
    '.pyx',        # Cython sources
    '.c',          # C sources
    '.h',          # C headers
    
    # Documentation
    'doc/',
    'docs/',
    '.md',
    '.rst',
    '.txt',
    'LICENSE',
    'CHANGELOG',
    'README',
    'NOTICE',
    'AUTHORS',
    
    # Locale data (only keep English)
    'locale/',
    '/de/',
    '/fr/',
    '/es/',
    '/it/',
    '/pt/',
    '/ru/',
    '/zh/',
    '/ja/',
    '/ko/',
    '/ar/',
    
    # Unnecessary data files
    'examples/',
    'sample/',
    'samples/',
    'demo/',
    'demos/',
    'benchmarks/',
    'fixtures/',
    
    # Large model files that shouldn't be bundled
    '.bin',
    '.safetensors',
    '.onnx',
    '.pt',
    '.pth',
    '.h5',
    '.hdf5',
    '.pkl',
    '.pickle',
    
    # Development files
    '.git/',
    '.github/',
    '.vscode/',
    '.idea/',
    'Makefile',
    'setup.py',
    'setup.cfg',
    'pyproject.toml',
    
    # REMOVED packages data (if somehow included)
    'transformers/',
    'spacy/',
    'nltk_data/',
    'pandas/',
    'matplotlib/',
]

# Filter datas
a.datas = [x for x in a.datas if not any(pattern in x[0] for pattern in excluded_patterns)]

# Also filter binaries (remove unnecessary DLLs)
excluded_dll_patterns = [
    'mkl_',           # Intel MKL (not needed for basic llama.cpp)
    'libopenblas',    # OpenBLAS (not needed)
    'tcl',
    'tk',
    '_tkinter',
]
a.binaries = [x for x in a.binaries if not any(pattern in x[0].lower() for pattern in excluded_dll_patterns)]

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
    strip=True,      # Strip symbols to reduce size
    upx=True,        # Compress with UPX
    upx_exclude=[
        'vcruntime140.dll',  # Don't compress VC runtime
        'python*.dll',       # Don't compress Python DLL
    ],
    runtime_tmpdir=None,
    console=True,  # Keep console for stdin/stdout communication
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
