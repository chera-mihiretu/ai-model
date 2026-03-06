# Windows Deployment Guide

This guide explains how to package the Story Bible App as a standalone Windows executable (`.exe`) while keeping the 4.9GB LLaMA model external.

## 1. Prerequisites

Ensure you have the following installed on your Windows machine:
- **Python 3.10+**
- **Git**
- **C++ Build Tools** (Visual Studio Build Tools) - required for `llama-cpp-python` compilation if not using pre-built wheels.

## 2. Setup Build Environment

Open PowerShell or Command Prompt and run:

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install PyInstaller
pip install pyinstaller

# 3. Verify PyInstaller works
pyinstaller --version
```
# Story Bible App - Cross-Platform Deployment Guide

This guide explains how to build the Story Bible App for Windows, Linux, and macOS.
The application preserves all functionality, including the custom writing canvas and AI integration, across all platforms.

## ⚠️ Important Configuration

The LLaMA model (~4.9GB) is **too large to bundle** inside the executable.
It must be distributed alongside the app in a `models/` directory.

---

## 🏗️ Build Instructions

### Prerequisites
1.  Python 3.10+ installed.
2.  Dependencies installed:
    ```bash
    pip install -r requirements.txt
    ```

### How to Build (All Platforms)
We provide a unified build script that detects your OS and configures PyInstaller automatically.

1.  **Open a terminal** in the project root.
2.  **Run the build script**:
    ```bash
    python build.py
    ```

### Platform Specifics

#### 🪟 Windows
- **Output**: `dist\StoryBibleApp\StoryBibleApp.exe`
- **Icon**: Uses `resources/icon.ico` if available.
- **Console**: Hidden by default (GUI only).

#### 🐧 Linux
- **Output**: `dist/StoryBibleApp/StoryBibleApp`
- **Icon**: Uses `resources/icon.png` if available.
- **Note**: Ensure you have GLIBC compatible with your target distribution (build on the oldest distro you intend to support, e.g., Ubuntu 20.04).

#### 🍎 macOS
- **Output**: `dist/StoryBibleApp.app` (Application Bundle)
- **Icon**: Uses `resources/icon.icns` if available.
- **Note**: The build script enables `argv_emulation` so you can open files with valid double-click behavior.
- **Signing**: This build script does **not** code-sign the app. You may need to allow it in "Security & Privacy" to run.

---

## 📦 Distribution Steps (Post-Build)

After building, you must verify the folder structure before zipping potential releases.

1.  **Locate the executable folder**:
    - Windows/Linux: `dist/StoryBibleApp/`
    - macOS: `dist/StoryBibleApp.app/Contents/MacOS/`

2.  **Copy the AI Model**:
    Create a `models/llama/` folder next to the main executable and place your `.gguf` model there.

    **Structure:**
    ```text
    StoryBibleApp/          (or inside .app/Contents/MacOS/)
    ├── StoryBibleApp       (Executable)
    └── models/
        └── llama/
            └── Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
    ```

3.  **Run to Verify**:
    Double-click the executable. If the model is missing, the logs (or console if enabled) will show an error.

---

## 🐛 Troubleshooting

- **Model Not Found**: Check that `models/` is directly next to the executable file, not just in the parent `dist` folder.
- **DLL Missing (Windows)**: Ensure you have the Visual C++ Redistributable installed.
- **Permission Denied (Linux/macOS)**: Ensure the binary is executable: `chmod +x StoryBibleApp`.

### CPU Compatibility Issues (AVX2 Error)

If you see an error like:
> "Error: CPU incompatible (AVX2 not supported)" or "Your CPU does not support AVX2 instructions"

This means the `llama-cpp-python` library was compiled with AVX2 optimizations, but your CPU doesn't support them. This is common on older gaming PCs and some budget processors.

**Solution: Rebuild with basic CPU support**

1. **Uninstall the existing llama-cpp-python**:
   ```bash
   pip uninstall llama-cpp-python -y
   ```

2. **Reinstall without AVX2 (basic CPU build)**:
   
   For **Windows** (no AVX2):
   ```bash
   # Option 1: Use the pre-built noavx wheel
   pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
   
   # Option 2: Build from source with basic CPU
   set CMAKE_ARGS=-DGGML_AVX2=OFF -DGGML_AVX=OFF -DGGML_F16C=OFF -DGGML_FMA=OFF
   pip install llama-cpp-python --force-reinstall --no-cache-dir
   ```
   
   For **Linux**:
   ```bash
   CMAKE_ARGS="-DGGML_AVX2=OFF -DGGML_AVX=OFF -DGGML_F16C=OFF -DGGML_FMA=OFF" pip install llama-cpp-python --force-reinstall --no-cache-dir
   ```
   
   For **macOS**:
   ```bash
   CMAKE_ARGS="-DGGML_AVX2=OFF -DGGML_AVX=OFF" pip install llama-cpp-python --force-reinstall --no-cache-dir
   ```

3. **Rebuild the application** using `pyinstaller`:
   ```bash
   cd story-bible-electron/backend
   pyinstaller backend.spec
   ```

4. **Package the new build** and distribute to users with older CPUs.

**Note**: The noavx build will be slower than AVX2-optimized builds, but will work on all x86_64 CPUs.

## 5. Persistent Data

When running the portable `.exe`, the application will create a `data` folder next to the executable to store:
- `story_bible.db` (User projects and characters)
- Logs

You can copy an existing `story_bible.db` into this `data` folder to migrate your work.

## 6. Running the App

Double-click `StoryBibleApp.exe`.
- The console window is hidden (Windowed mode).
- Check `data/app.log` if you encounter startup issues.
