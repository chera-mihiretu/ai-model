# Your Immediate Fix - Python 3.14 Error

## What Happened

You ran `.\build-windows.ps1` and got these errors:
- `ERROR: Hidden import 'edge_tts.communicate' not found`
- `ERROR: Hidden import 'aiohttp' not found`
- `TypeError: expected string or bytes-like object, got 'NoneType'`

## Why It Failed

1. **Python 3.14.2** - Too new, PyInstaller doesn't fully support it yet
2. **Missing TTS packages** - edge-tts, aiohttp, pygame not installed in your venv

---

## Fix It Now (Copy & Paste These Commands)

### Option 1: Quick Fix (Install Missing Packages)

Try this first - it might work:

```powershell
# Make sure you're in project directory
cd C:\Users\chera\OneDrive\Desktop\projects\fiver\ricardo\ai-desktop-assist

# Activate venv
.\deskapp\Scripts\Activate.ps1

# Install missing TTS packages
pip install edge-tts==7.0.0
pip install aiohttp==3.10.11
pip install aiosignal frozenlist multidict yarl async-timeout
pip install pygame==2.6.1
pip install certifi urllib3 filelock nltk safetensors

# Upgrade packaging to handle Python 3.14
pip install --upgrade packaging setuptools

# Try building again
.\build-windows.ps1
```

### Option 2: Proper Fix (Downgrade to Python 3.11) - RECOMMENDED

If Option 1 doesn't work, do this:

```powershell
# 1. Download Python 3.11.8
# Go to: https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe
# Run installer, check "Add to PATH"

# 2. Remove old virtual environment
cd C:\Users\chera\OneDrive\Desktop\projects\fiver\ricardo\ai-desktop-assist
Remove-Item -Recurse -Force deskapp
Remove-Item -Recurse -Force venv

# 3. Create new venv with Python 3.11
python -m venv venv

# 4. Activate it
.\venv\Scripts\Activate.ps1

# 5. Verify Python version
python --version
# Should show: Python 3.11.8

# 6. Install everything
python -m pip install --upgrade pip
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
pip install edge-tts pygame aiohttp
pip install -r requirements.txt
pip install pyinstaller
python -m spacy download en_core_web_sm

# 7. Build
.\build-windows.ps1
```

---

## Verify Before Building

```powershell
# Check Python version
python --version
# MUST be 3.10.x or 3.11.x

# Check packages are installed
pip show edge-tts
pip show pygame
pip show aiohttp
pip show pyinstaller

# Test imports
python -c "import edge_tts; print('edge-tts OK')"
python -c "import pygame; print('pygame OK')"
python -c "import aiohttp; print('aiohttp OK')"
```

All should print "OK" with no errors.

---

## Expected Output After Fix

When you run `.\build-windows.ps1` successfully, you should see:

```
============================================
  Exelsias - Windows Build Script
============================================

[OK] Python: Python 3.11.8
[OK] Node.js: v25.4.0
[OK] npm: 11.7.0

Building Python Backend...
(no errors about missing imports)

Building React Frontend...
(builds successfully)

Building Electron App...
(creates NSIS installer)

============================================
  Build Completed Successfully!
============================================

Output: story-bible-electron\dist\Exelsias Setup X.X.X.exe
```

---

## Timeline

- **Option 1** (Quick fix): 5-10 minutes
- **Option 2** (Python 3.11): 20-30 minutes (includes Python download/install)

---

## Which Option Should You Choose?

| Situation | Recommended Option |
|-----------|-------------------|
| Just want to try quickly | Option 1 |
| Option 1 didn't work | Option 2 |
| Building for production | Option 2 (more stable) |
| Have time to do it right | Option 2 |

---

## After Successful Build

1. Find installer: `story-bible-electron\dist\Exelsias Setup X.X.X.exe`
2. Test it on a clean Windows machine
3. Verify TTS works (Read button)
4. Verify LLM works (load model, generate text)

---

## Need More Help?

- **Python 3.14 issues**: [FIX_PYTHON_314_ERROR.md](FIX_PYTHON_314_ERROR.md)
- **Other build errors**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Complete guide**: [WINDOWS_BUILD_GUIDE.md](WINDOWS_BUILD_GUIDE.md)

---

**Created**: 2026-02-23  
**Your Error**: Python 3.14 + Missing TTS packages  
**Solution**: Downgrade to Python 3.11 + Install missing packages
