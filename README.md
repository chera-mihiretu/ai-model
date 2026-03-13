# Exelsias - AI-Powered Writing Assistant

A professional AI-powered writing assistant with Story Bible management, character tracking, and neural text-to-speech.

## Architecture

This is an Electron application with a Python backend for AI processing.

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron App                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Electron Main Process                      │   │
│  │  • Spawns Python backend as child process           │   │
│  │  • Manages app lifecycle                            │   │
│  │  • IPC bridge to Python                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↕ IPC                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Electron Renderer (UI)                     │   │
│  │  • React frontend with Tailwind CSS                 │   │
│  │  • Beautiful violet glass-effect theme              │   │
│  │  • TipTap rich text editor                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↕ IPC                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Python Backend (Bundled)                   │   │
│  │  • AI Engine (LLaMA 3.1 8B)                         │   │
│  │  • TTS Engine (Edge TTS)                            │   │
│  │  • Database Manager (SQLite)                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Development Setup

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+ (3.11 recommended)
- **Git**
- **Visual Studio Build Tools** (Windows only - for compiling native modules)

---

## Windows Installation

### Step 1: Install Visual Studio Build Tools (Required for llama-cpp-python)

1. Download [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Run the installer and select **"Desktop development with C++"**
3. Restart your computer after installation

### Step 2: Clone the Project

```powershell
git clone <repository-url>
cd ricardoo
```

### Step 3: Set Up Python Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate

# Upgrade pip first
python -m pip install --upgrade pip

# Install llama-cpp-python (pre-built wheel for Windows CPU)
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# If you have NVIDIA GPU with CUDA, use this instead:
# pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

# Install remaining requirements
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm
```

### Step 4: Install Node.js Dependencies

```powershell
# Install frontend dependencies
cd story-bible-electron\frontend
npm install

# Install Electron dependencies
cd ..\electron
npm install
```

### Step 5: Run the Application

```powershell
# Make sure you're in the electron folder
cd story-bible-electron\electron

# Start the app (this will start frontend and electron together)
npm run dev
```

---

## Linux / macOS Installation

### Step 1: Clone the Project

```bash
git clone <repository-url>
cd ricardoo
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm
```

### Step 3: Install Node.js Dependencies

```bash
# Install frontend dependencies
cd story-bible-electron/frontend
npm install

# Install Electron dependencies
cd ../electron
npm install
```

### Step 4: Run the Application

```bash
cd story-bible-electron/electron
npm run dev
```

---

## Troubleshooting

### Windows: "Failed to build llama-cpp-python"

This error occurs when Visual Studio Build Tools are not installed. Follow Step 1 in the Windows installation guide.

Alternatively, use the pre-built wheel:
```powershell
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

### Windows: "numpy version conflict"

If you see numpy-related errors:
```powershell
pip uninstall numpy -y
pip install numpy==1.26.4
```

### Windows: "Microsoft Visual C++ 14.0 or greater is required"

Install Visual Studio Build Tools with C++ development tools selected.

### Linux: "ImportError: libGL.so.1"

Install OpenGL libraries:
```bash
# Ubuntu/Debian
sudo apt-get install libgl1-mesa-glx

# Fedora
sudo dnf install mesa-libGL
```

### macOS: "xcrun: error: invalid active developer path"

Install Xcode command line tools:
```bash
xcode-select --install
```

### "Port 5173 is already in use"

Kill the existing process or use a different port:
```bash
# Find and kill the process
# Linux/macOS
lsof -ti:5173 | xargs kill -9

# Windows PowerShell
Get-Process -Id (Get-NetTCPConnection -LocalPort 5173).OwningProcess | Stop-Process -Force
```

### Fresh Start / Database Reset

If you experience issues with project IDs or data mixing between projects, you can reset the database:

```bash
# Delete the database file to start fresh
# Linux/macOS
rm -f data/database/app.db

# Windows PowerShell
Remove-Item data\database\app.db -Force
```

Also clear browser localStorage for the app (in DevTools > Application > Local Storage):
- Delete `exelsias_folders`
- Delete `exelsias_series`

The app will create a new database with proper UUIDs on next launch.

---

## Building for Production

### Build Windows NSIS Installer (Universal - Recommended)

The **universal build** creates an installer compatible with ALL Windows PCs, including older gaming PCs and budget processors that lack AVX2 support.

```powershell
# Open PowerShell and navigate to the project root
cd ricardoo

# Run the universal build script
.\build-universal.ps1
```

**Build Options:**
```powershell
.\build-universal.ps1                  # Full build
.\build-universal.ps1 -SkipBackend     # Skip Python backend rebuild
.\build-universal.ps1 -SkipFrontend    # Skip frontend rebuild  
.\build-universal.ps1 -Clean           # Clean all previous builds first
.\build-universal.ps1 -ReinstallLlama  # Force reinstall llama-cpp-python with basic CPU
```

**Output:** `story-bible-electron\dist\Exelsias Setup X.X.X.exe`

⚠️ **Important**: 
- Use Python 3.10 or 3.11 (NOT 3.12+) for best compatibility
- The universal build disables AVX2/AVX optimizations for maximum compatibility
- Build time: ~5-10 minutes depending on your system

### Build Windows (Standard - AVX2 Required)

For modern PCs with AVX2 support (better performance):

```powershell
.\build-windows.ps1
```

### Build Linux AppImage

```bash
cd story-bible-electron/electron
npm run build:linux
```

### Build macOS DMG

```bash
cd story-bible-electron/electron
npm run build:mac
```

### After Building

The installer will be in `story-bible-electron\dist\`. You can:

1. **Test locally** - Run the installer on your machine
2. **Copy to Documents** - Move installer to a convenient location:
   ```powershell
   Move-Item "story-bible-electron\dist\Exelsias Setup*.exe" "$env:USERPROFILE\Documents\"
   ```
3. **Distribute** - Share the installer with others

---

## Project Structure

```
ricardoo/
├── src/                      # Python backend source
│   ├── database/
│   │   └── db_manager.py     # SQLite database management
│   └── services/
│       ├── ai_engine.py      # LLaMA AI integration
│       └── tts_engine.py     # Text-to-speech
├── models/
│   └── llama/                # Place LLaMA model here
│       └── Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
├── data/
│   └── database/             # SQLite database files
├── story-bible-electron/
│   ├── electron/
│   │   ├── main.js           # Electron main process
│   │   ├── preload.js        # Context bridge for IPC
│   │   └── package.json      # Electron dependencies
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.jsx       # Main React component
│   │   │   ├── components/   # UI components
│   │   │   ├── hooks/        # React hooks
│   │   │   └── styles/       # CSS files
│   │   └── package.json      # Frontend dependencies
│   └── backend/
│       └── api_bridge.py     # Python JSON-RPC server
└── requirements.txt          # Python dependencies
```

---

## Features

### Writing Tools
- **Write**: Continue writing with AI assistance
- **Rewrite**: Transform text (Show Don't Tell, Dramatic, Elegant, etc.)
- **Describe**: Add sensory details (Sight, Sound, Smell, Taste, Touch)
- **More Tools**: Visualize, Twist, Poem generation

### Story Bible
- **Braindump**: Free-form notes and ideas
- **Genre**: Set story genre and conventions
- **Style**: Define writing style and tone
- **Synopsis**: Story overview with AI generation
- **Characters**: Character profiles with AI generation
- **Worldbuilding**: World details and rules
- **Outline**: Plot structure with chapter cards

### AI Features
- Local LLaMA 3.1 8B model (runs offline)
- Context-aware writing suggestions
- Character-consistent dialogue
- Lore Assistant for story Q&A

### Text-to-Speech
- Neural voices via Edge TTS
- Multiple voice options (US, UK, Australian, Indian)

---

## Required Model

Download the LLaMA model and place it in `models/llama/`:

**Model**: `Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf`

Download from: [HuggingFace](https://huggingface.co/lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF)

---

## License

MIT License - See LICENSE file for details.
