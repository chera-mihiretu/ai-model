# Linux Deployment Guide

## 1. Environment Setup

It is recommended to use a virtual environment to avoid conflicts with system packages (pacman/apt).

```bash
# Create venv (if not exists)
python3 -m venv deskapp

# Activate
source deskapp/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Build

Run the unified build script. This script automatically detects Linux and appends the correct options.

```bash
python build.py
```

## 3. Distribution & Setup

The build output is located at: `dist/StoryBibleApp/`.

### ⚠️ Essential: Add AI Models
The App does **not** bundle the huge LLaMA model. You **must** manually copy it.

```bash
# Assuming you are in the project root
cp -r models dist/StoryBibleApp/
```

**Final Folder Structure:**
```
dist/StoryBibleApp/
├── StoryBibleApp        (Executable binary)
├── _internal/           (Python libraries)
└── models/              (COPIED MANUALLY)
    └── llama/
        └── Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
```

## 4. Running

```bash
cd dist/StoryBibleApp
./StoryBibleApp
```

## 5. System Integration (Optional)

### Desktop Desktop Entry
To make the app appear in your application monitor, create a `.desktop` file in `~/.local/share/applications/storybible.desktop`.

```ini
[Desktop Entry]
Name=Story Bible App
Comment=AI-Powered Creative Writing Tool
Exec=/path/to/your/dist/StoryBibleApp/StoryBibleApp
Icon=/path/to/your/resources/icon.png
Type=Application
Categories=Office;Writing;
Terminal=false
```

*Note: Replace `/path/to/your/...` with the absolute path to the inner `dist/StoryBibleApp` folder.*
