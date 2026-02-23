# Fix: Python 3.14 Build Error

## Your Error

```
ERROR: Hidden import 'edge_tts.communicate' not found
ERROR: Hidden import 'aiohttp' not found
ERROR: Hidden import 'pygame.mixer' not found
TypeError: expected string or bytes-like object, got 'NoneType'
```

## Root Causes

1. **Python 3.14.2 is too new** - PyInstaller and packaging libraries have compatibility issues
2. **Missing TTS dependencies** - edge-tts, aiohttp, and pygame are not installed

---

## Solution: Downgrade to Python 3.11

### Step 1: Install Python 3.11.8

```powershell
# 1. Download Python 3.11.8 from:
# https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe

# 2. Run the installer
# - Check "Add Python to PATH"
# - Choose "Customize installation"
# - Check all optional features
# - Install for all users (if admin)

# 3. Verify installation
python --version
# Should show: Python 3.11.8
```

### Step 2: Recreate Virtual Environment

```powershell
# Navigate to project root
cd C:\Users\chera\OneDrive\Desktop\projects\fiver\ricardo\ai-desktop-assist

# Remove old venv
Remove-Item -Recurse -Force venv
Remove-Item -Recurse -Force deskapp

# Create new venv with Python 3.11
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Verify correct Python version in venv
python --version
# Should show: Python 3.11.8
```

### Step 3: Install Dependencies in Correct Order

```powershell
# Make sure venv is activated (you should see (venv) in prompt)

# 1. Upgrade pip
python -m pip install --upgrade pip

# 2. Install llama-cpp-python FIRST (pre-built wheel)
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# 3. Install TTS dependencies EXPLICITLY
pip install edge-tts==7.0.0
pip install pygame==2.6.1
pip install aiohttp==3.10.11

# 4. Install remaining requirements
pip install -r requirements.txt

# 5. Install PyInstaller
pip install pyinstaller==6.5.0

# 6. Download spaCy model
python -m spacy download en_core_web_sm
```

### Step 4: Verify All Dependencies

```powershell
# Check critical packages
pip show llama-cpp-python
pip show edge-tts
pip show pygame
pip show aiohttp
pip show pyinstaller

# All should show "Location: ...\venv\Lib\site-packages"
```

### Step 5: Test Imports

```powershell
# Test that all imports work
python -c "import llama_cpp; print('llama-cpp-python OK')"
python -c "import edge_tts; print('edge-tts OK')"
python -c "import pygame; print('pygame OK')"
python -c "import aiohttp; print('aiohttp OK')"
```

### Step 6: Rebuild

```powershell
# Now try building again
.\build-windows.ps1
```

---

## Alternative: Fix Python 3.14 Issues (Not Recommended)

If you cannot downgrade Python, try this workaround:

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Upgrade packaging and setuptools
pip install --upgrade packaging setuptools wheel

# Install specific PyInstaller version
pip install pyinstaller==6.5.0

# Install ALL missing dependencies explicitly
pip install edge-tts==7.0.0
pip install aiohttp==3.10.11
pip install aiosignal==1.3.2
pip install frozenlist==1.5.0
pip install multidict==6.1.0
pip install yarl==1.18.3
pip install async-timeout==5.0.1
pip install pygame==2.6.1
pip install certifi==2024.12.14
pip install urllib3==2.3.0
pip install filelock==3.16.1
pip install nltk==3.9.1
pip install safetensors==0.4.5

# Try building
cd story-bible-electron\backend
.\build-backend.ps1
```

⚠️ **Warning**: Python 3.14 may still have other compatibility issues. Python 3.11 is strongly recommended.

---

## Verification Checklist

Before building, verify:

- [ ] Python version is 3.10.x or 3.11.x (NOT 3.12+)
- [ ] Virtual environment is activated
- [ ] llama-cpp-python installed: `pip show llama-cpp-python`
- [ ] edge-tts installed: `pip show edge-tts`
- [ ] pygame installed: `pip show pygame`
- [ ] aiohttp installed: `pip show aiohttp`
- [ ] pyinstaller installed: `pip show pyinstaller`
- [ ] All imports work (test with python -c commands above)

---

## Quick Fix Commands

Copy and paste this entire block:

```powershell
# Remove old environment
Remove-Item -Recurse -Force venv -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force deskapp -ErrorAction SilentlyContinue

# Create new venv with Python 3.11
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install everything in correct order
python -m pip install --upgrade pip
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
pip install edge-tts==7.0.0 pygame==2.6.1 aiohttp==3.10.11
pip install -r requirements.txt
pip install pyinstaller==6.5.0
python -m spacy download en_core_web_sm

# Verify
python --version
pip show edge-tts pygame aiohttp pyinstaller

# Build
.\build-windows.ps1
```

---

## Why Python 3.11?

| Python Version | Status | Issues |
|----------------|--------|--------|
| 3.10.x | ✅ Recommended | Stable, well-tested |
| 3.11.x | ✅ Recommended | Best compatibility |
| 3.12.x | ⚠️ Risky | Some package compatibility issues |
| 3.13.x | ❌ Not supported | PyInstaller issues |
| 3.14.x | ❌ Not supported | Multiple compatibility issues |

---

## Still Having Issues?

If you still get errors after following this guide:

1. **Completely clean your environment**:
   ```powershell
   Remove-Item -Recurse -Force venv, deskapp, story-bible-electron\backend\dist, story-bible-electron\backend\build
   ```

2. **Verify Python 3.11 is default**:
   ```powershell
   python --version  # Must show 3.11.x
   ```

3. **Follow the Quick Fix Commands** above exactly

4. **Check logs** for specific errors:
   ```powershell
   # PyInstaller creates detailed logs
   Get-Content story-bible-electron\backend\build\warn-api_bridge.txt
   ```

5. **Create GitHub issue** with:
   - Full error output
   - Python version: `python --version`
   - Pip list: `pip list`
   - Build command used

---

**Last Updated**: 2026-02-23  
**Issue**: Python 3.14 compatibility  
**Solution**: Downgrade to Python 3.11.8
