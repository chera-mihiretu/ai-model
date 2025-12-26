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

## 3. Build the Executable

Run the following command in the project root (where `deployment.spec` is located):

```powershell
pyinstaller deployment.spec
```

This will create two folders: `build/` (temp files) and `dist/` (final output).

## 4. Post-Build Setup (CRITICAL)

The LLaMA model is too large to bundle, so you must place it manually.

1. Navigate to `dist/StoryBibleApp/`.
2. Create a folder named `models`.
3. Inside `models`, create a folder named `llama`.
4. Place your `.gguf` model file here.

**Structure:**
```
dist/
└── StoryBibleApp/
    ├── StoryBibleApp.exe
    ├── _internal/
    └── models/
        └── llama/
            └── Llama-3.1-8B-Instruct.gguf  <-- YOUR MODEL HERE
```

## 5. Persistent Data

When running the portable `.exe`, the application will create a `data` folder next to the executable to store:
- `story_bible.db` (User projects and characters)
- Logs

You can copy an existing `story_bible.db` into this `data` folder to migrate your work.

## 6. Running the App

Double-click `StoryBibleApp.exe`.
- The console window is hidden (Windowed mode).
- Check `data/app.log` if you encounter startup issues.
