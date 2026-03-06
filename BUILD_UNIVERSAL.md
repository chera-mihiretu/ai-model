# Exelsias - Universal Build Guide (Windows)

## Complete Build Instructions for Any PC Compatibility

This guide creates a build that works on **ALL Windows PCs**, including older gaming PCs without AVX2 support.

**OPTIMIZED BUILD**: This build has been optimized to reduce installer size by:
- Removing unused Python packages (transformers, spacy, nltk, pandas, etc.)
- Excluding test files, documentation, and unnecessary data
- Using maximum compression for the installer

---

## Prerequisites

Before you begin, you need:

| Tool | Version | Download Link |
|------|---------|--------------|
| Python | 3.10 or 3.11 (NOT 3.12+) | https://www.python.org/downloads/ |
| Node.js | 18.x or 20.x LTS | https://nodejs.org/ |
| Git | Latest | https://git-scm.com/ |
| Visual Studio Build Tools | 2019 or 2022 | https://visualstudio.microsoft.com/visual-cpp-build-tools/ |

### Visual Studio Build Tools Installation
When installing Visual Studio Build Tools, select:
- "Desktop development with C++" workload
- Windows 10/11 SDK
- C++ CMake tools

---

## Step-by-Step Build Process

### STEP 1: Clone the Repository

Open PowerShell as Administrator and run:

```powershell
# Navigate to your projects folder
cd C:\Projects

# Clone the repository (replace with your actual repo URL)
git clone <your-repo-url> exelsias
cd exelsias
```

**Expected Output:**
```
Cloning into 'exelsias'...
remote: Enumerating objects: 1234, done.
remote: Counting objects: 100% (1234/1234), done.
Receiving objects: 100% (1234/1234), 5.67 MiB | 2.34 MiB/s, done.
```

---

### STEP 2: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1
```

**Expected Output:**
```
(venv) PS C:\Projects\exelsias>
```

You should see `(venv)` at the beginning of your prompt.

---

### STEP 3: Install Base Python Dependencies

```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install all dependencies EXCEPT llama-cpp-python
pip install pydantic>=2.5.0
pip install transformers>=4.36.0 tokenizers>=0.15.0 safetensors>=0.4.0 huggingface-hub>=0.20.0
pip install spacy>=3.7.0 nltk>=3.8.0
pip install numpy>=1.24.0 pandas>=2.0.0
pip install pillow>=10.0.0
pip install fpdf2>=2.7.0 ebooklib>=0.18
pip install requests>=2.31.0 tqdm>=4.66.0 PyYAML>=6.0.0 regex>=2023.0.0 filelock>=3.13.0 packaging>=23.0 typing_extensions>=4.9.0
pip install soundfile>=0.12.0 edge-tts>=6.1.0 pygame>=2.5.0
pip install pyinstaller
```

**Expected Output:**
```
Successfully installed pydantic-2.5.x ...
Successfully installed transformers-4.36.x tokenizers-0.15.x ...
... (multiple success messages)
```

---

### STEP 4: Install Universal llama-cpp-python (NO AVX2)

**THIS IS THE CRITICAL STEP FOR UNIVERSAL COMPATIBILITY**

```powershell
# Set environment variables to disable AVX2 and other advanced CPU instructions
$env:CMAKE_ARGS = "-DGGML_AVX2=OFF -DGGML_AVX=OFF -DGGML_F16C=OFF -DGGML_FMA=OFF"
$env:FORCE_CMAKE = "1"

# Install llama-cpp-python from source with basic CPU support
pip install llama-cpp-python --no-binary llama-cpp-python --force-reinstall --no-cache-dir
```

**Expected Output:**
```
Collecting llama-cpp-python
  Downloading llama_cpp_python-0.2.x.tar.gz (...)
Building wheels for collected packages: llama-cpp-python
  Building wheel for llama-cpp-python (setup.py) ... done
Successfully built llama-cpp-python
Successfully installed llama-cpp-python-0.2.x
```

**If the build fails**, try the alternative method:

```powershell
# Alternative: Use pre-built wheel (may still have AVX2)
pip uninstall llama-cpp-python -y
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

---

### STEP 5: Verify llama-cpp-python Installation

```powershell
python -c "from llama_cpp import Llama; print('llama-cpp-python installed successfully!')"
```

**Expected Output:**
```
llama-cpp-python installed successfully!
```

---

### STEP 6: Install Frontend Dependencies

```powershell
# Navigate to frontend folder
cd story-bible-electron\frontend

# Install npm dependencies
npm install
```

**Expected Output:**
```
added 456 packages in 45s
```

```powershell
# Go back to project root
cd ..\..
```

---

### STEP 7: Install Electron Dependencies

```powershell
# Navigate to electron folder
cd story-bible-electron\electron

# Install npm dependencies
npm install
```

**Expected Output:**
```
added 234 packages in 30s
```

```powershell
# Go back to project root
cd ..\..
```

---

### STEP 8: Create Application Icon

The application needs a proper `.ico` file for Windows. The icon is already available in the assets folder:

```powershell
# Copy the existing icon to the electron folder
Copy-Item "story-bible-electron\frontend\public\assets\logo.ico" "story-bible-electron\electron\icon.ico" -Force
Write-Host "Icon copied successfully!" -ForegroundColor Green

# Verify the icon
if (Test-Path "story-bible-electron\electron\icon.ico") {
    $size = (Get-Item "story-bible-electron\electron\icon.ico").Length
    Write-Host "Icon size: $size bytes" -ForegroundColor Cyan
}
```

**Expected Output:**
```
Icon copied successfully!
Icon size: 517 bytes
```

**If you need to create a new icon from PNG:**

```powershell
# Install Pillow if not already installed
pip install pillow

# Run the icon conversion script
python convert_icon.py
```

**Or create manually:**

1. Go to https://cloudconvert.com/png-to-ico
2. Upload `story-bible-electron\frontend\public\assets\logo.png`
3. Download the `.ico` file
4. Save it as `story-bible-electron\electron\icon.ico`

---

### STEP 9: Build the Python Backend

```powershell
# Make sure venv is activated
.\venv\Scripts\Activate.ps1

# Navigate to backend folder
cd story-bible-electron\backend

# Run PyInstaller
pyinstaller backend.spec
```

**Expected Output:**
```
123 INFO: PyInstaller: 6.x.x
123 INFO: Python: 3.11.x
...
Building EXE because EXE-00.toc is non existent
...
12345 INFO: Building EXE from EXE-00.toc completed successfully.
```

```powershell
# Verify the executable was created
if (Test-Path "dist\api_bridge.exe") {
    $size = [math]::Round((Get-Item "dist\api_bridge.exe").Length / 1MB, 2)
    Write-Host "SUCCESS: api_bridge.exe created ($size MB)" -ForegroundColor Green
} else {
    Write-Host "ERROR: api_bridge.exe not found!" -ForegroundColor Red
}
```

```powershell
# Create dist-win folder and copy executable
if (-not (Test-Path "dist-win")) { New-Item -ItemType Directory -Path "dist-win" }
Copy-Item "dist\api_bridge.exe" "dist-win\api_bridge.exe" -Force
Write-Host "Backend copied to dist-win folder" -ForegroundColor Green

# Go back to project root
cd ..\..
```

---

### STEP 10: Build the Frontend

```powershell
cd story-bible-electron\frontend
npm run build
```

**Expected Output:**
```
vite v5.x.x building for production...
✓ 234 modules transformed.
dist/index.html                  1.23 kB │ gzip:  0.56 kB
dist/assets/index-abc123.css    45.67 kB │ gzip: 12.34 kB
dist/assets/index-def456.js    567.89 kB │ gzip: 178.90 kB
✓ built in 12.34s
```

```powershell
# Verify build
if (Test-Path "dist\index.html") {
    Write-Host "SUCCESS: Frontend built successfully!" -ForegroundColor Green
} else {
    Write-Host "ERROR: Frontend build failed!" -ForegroundColor Red
}

# Go back to project root
cd ..\..
```

---

### STEP 11: Build the Electron Installer

```powershell
cd story-bible-electron\electron
npm run build:win
```

**Expected Output:**
```
  • electron-builder  version=24.x.x
  • loaded configuration  file=package.json
  • writing effective config  file=dist\builder-effective-config.yaml
  • packaging       platform=win32 arch=x64 electron=28.x.x
  • building        target=nsis file=dist\Exelsias Setup 1.0.0.exe
  • building block map  blockMapFile=dist\Exelsias Setup 1.0.0.exe.blockmap
```

```powershell
# Verify installer was created
$installer = Get-ChildItem "..\dist\*.exe" | Select-Object -First 1
if ($installer) {
    $size = [math]::Round($installer.Length / 1MB, 2)
    Write-Host "SUCCESS: Installer created!" -ForegroundColor Green
    Write-Host "  File: $($installer.Name)" -ForegroundColor Cyan
    Write-Host "  Size: $size MB" -ForegroundColor Cyan
    Write-Host "  Path: $($installer.FullName)" -ForegroundColor Cyan
} else {
    Write-Host "ERROR: Installer not found!" -ForegroundColor Red
}

# Go back to project root
cd ..\..
```

---

### STEP 12: Verify the Complete Build

```powershell
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  BUILD VERIFICATION CHECKLIST" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check backend
$backend = "story-bible-electron\backend\dist-win\api_bridge.exe"
if (Test-Path $backend) {
    Write-Host "[OK] Backend executable exists" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Backend executable missing" -ForegroundColor Red
}

# Check frontend
$frontend = "story-bible-electron\frontend\dist\index.html"
if (Test-Path $frontend) {
    Write-Host "[OK] Frontend build exists" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Frontend build missing" -ForegroundColor Red
}

# Check icon
$icon = "story-bible-electron\electron\icon.ico"
if (Test-Path $icon) {
    Write-Host "[OK] Application icon exists" -ForegroundColor Green
} else {
    Write-Host "[WARN] Application icon missing (will use default)" -ForegroundColor Yellow
}

# Check installer
$installers = Get-ChildItem "story-bible-electron\dist\*.exe" -ErrorAction SilentlyContinue
if ($installers.Count -gt 0) {
    Write-Host "[OK] Installer created: $($installers[0].Name)" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Installer not found" -ForegroundColor Red
}

Write-Host ""
```

---

## Complete One-Liner Build Script

For experienced users, here's the complete build in one script:

```powershell
# Save this as build-universal.ps1 and run it

# Activate venv
.\venv\Scripts\Activate.ps1

# Set universal CPU flags
$env:CMAKE_ARGS = "-DGGML_AVX2=OFF -DGGML_AVX=OFF -DGGML_F16C=OFF -DGGML_FMA=OFF"
$env:FORCE_CMAKE = "1"

# Reinstall llama-cpp-python with basic CPU
pip uninstall llama-cpp-python -y
pip install llama-cpp-python --no-binary llama-cpp-python --force-reinstall --no-cache-dir

# Build backend
Push-Location "story-bible-electron\backend"
pyinstaller backend.spec
if (-not (Test-Path "dist-win")) { New-Item -ItemType Directory -Path "dist-win" }
Copy-Item "dist\api_bridge.exe" "dist-win\api_bridge.exe" -Force
Pop-Location

# Build frontend
Push-Location "story-bible-electron\frontend"
npm install
npm run build
Pop-Location

# Build electron
Push-Location "story-bible-electron\electron"
npm install
npm run build:win
Pop-Location

Write-Host "BUILD COMPLETE!" -ForegroundColor Green
Write-Host "Installer: story-bible-electron\dist\" -ForegroundColor Cyan
```

---

## Testing the Build

### Test on the Build Machine

1. Navigate to `story-bible-electron\dist\`
2. Run the installer: `Exelsias Setup 1.0.0.exe`
3. Install to default location
4. Launch Exelsias

### Test Checklist

| Feature | How to Test | Expected Result |
|---------|-------------|-----------------|
| **App Launch** | Double-click Exelsias | App opens without errors |
| **Animations** | Watch home screen | Particle animations visible |
| **Icons** | Check window/taskbar | Custom icon visible |
| **Load Model** | Settings → Import Model | Model loads without CPU error |
| **AI Writing** | Create project → Use AI | Text generates |
| **TTS/Speech** | Click "Read Aloud" | Audio plays |
| **Save/Load** | Create and reopen project | Data persists |

### Test on an Older PC

Copy the installer to a PC without AVX2 support and verify:
- App launches
- Model loads (no "CPU incompatible" error)
- All features work

---

## Troubleshooting

### "CPU incompatible (AVX2 not supported)" Error

This means Step 4 wasn't done correctly. Fix:

```powershell
# Uninstall existing
pip uninstall llama-cpp-python -y

# Reinstall with correct flags
$env:CMAKE_ARGS = "-DGGML_AVX2=OFF -DGGML_AVX=OFF -DGGML_F16C=OFF -DGGML_FMA=OFF"
$env:FORCE_CMAKE = "1"
pip install llama-cpp-python --no-binary llama-cpp-python --force-reinstall --no-cache-dir

# Rebuild backend
cd story-bible-electron\backend
Remove-Item -Recurse -Force dist, build, dist-win -ErrorAction SilentlyContinue
pyinstaller backend.spec
if (-not (Test-Path "dist-win")) { New-Item -ItemType Directory -Path "dist-win" }
Copy-Item "dist\api_bridge.exe" "dist-win\api_bridge.exe" -Force
cd ..\..

# Rebuild electron
cd story-bible-electron\electron
npm run build:win
cd ..\..
```

### "Icon not showing"

1. Create a proper `.ico` file (256x256, 128x128, 64x64, 48x48, 32x32, 16x16 sizes)
2. Place at `story-bible-electron\electron\icon.ico`
3. Rebuild electron: `npm run build:win`

### "TTS not working"

Check internet connection (Edge TTS requires internet). Verify pygame is installed:

```powershell
pip install pygame soundfile edge-tts --force-reinstall
```

### "Model won't load"

1. Ensure `.gguf` model file is in the models folder
2. Check the model path in settings
3. Verify the model file isn't corrupted (re-download if needed)

### "Build fails on PyInstaller"

```powershell
# Clean and retry
cd story-bible-electron\backend
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
pip install pyinstaller --upgrade
pyinstaller backend.spec
```

---

## Output Files

After successful build, you'll have:

```
story-bible-electron/
├── dist/
│   ├── Exelsias Setup 1.0.0.exe    ← INSTALLER (distribute this!)
│   └── win-unpacked/                ← Portable version
├── backend/
│   └── dist-win/
│       └── api_bridge.exe           ← Python backend
└── frontend/
    └── dist/
        └── index.html               ← React frontend
```

**Distribute the installer file: `Exelsias Setup 1.0.0.exe`**

---

## Notes

- Build time: ~15-30 minutes depending on your machine
- Installer size: ~300-500 MB (varies based on dependencies)
- The universal build is slightly slower than AVX2-optimized but works everywhere
- Edge TTS requires internet connection for text-to-speech

---

## Quick Reference Commands

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Check Python
python --version

# Check if llama-cpp-python is installed
pip show llama-cpp-python

# Rebuild backend only
cd story-bible-electron\backend && pyinstaller backend.spec && cd ..\..

# Rebuild frontend only
cd story-bible-electron\frontend && npm run build && cd ..\..

# Rebuild electron only
cd story-bible-electron\electron && npm run build:win && cd ..\..

# Full clean rebuild
Remove-Item -Recurse -Force story-bible-electron\dist, story-bible-electron\backend\dist, story-bible-electron\backend\build, story-bible-electron\backend\dist-win, story-bible-electron\frontend\dist -ErrorAction SilentlyContinue
```
