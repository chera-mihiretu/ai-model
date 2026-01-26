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

---

## Quick Start (Development)

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+ (3.11 recommended)
- **Git**
- **Visual Studio Build Tools** (Windows only - for compiling native modules)

### Windows Development Setup

```powershell
# Clone the repository
git clone <repository-url>
cd ricardoo

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Install frontend dependencies
cd story-bible-electron\frontend
npm install

# Install Electron dependencies
cd ..\electron
npm install

# Run in development mode
npm run dev
```

### Linux/macOS Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd ricardoo

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Install frontend dependencies
cd story-bible-electron/frontend
npm install

# Install Electron dependencies
cd ../electron
npm install

# Run in development mode
npm run dev
```

---

## Building for Production (Windows)

### Method 1: Using the Build Script (Recommended)

```powershell
# Open PowerShell as Administrator
cd story-bible-electron\build

# Run the build script
.\build.ps1
```

The script will:
1. Set up Python virtual environment
2. Install all Python dependencies
3. Build the Python backend with PyInstaller
4. Build the React frontend with Vite
5. Package everything with electron-builder

**Output:** `story-bible-electron\dist\Exelsias Setup X.X.X.exe`

### Method 2: Manual Build

```powershell
# 1. Activate Python environment
cd ricardoo
venv\Scripts\activate

# 2. Install PyInstaller
pip install pyinstaller

# 3. Build Python backend
cd story-bible-electron\backend
pyinstaller --clean --noconfirm backend.spec

# 4. Copy the executable to dist-win folder
mkdir dist-win
copy dist\api_bridge.exe dist-win\api_bridge.exe

# 5. Build frontend
cd ..\frontend
npm install
npm run build

# 6. Build Electron app
cd ..\electron
npm install
npm run build:win
```

**Output:** `story-bible-electron\dist\Exelsias Setup X.X.X.exe`

---

## Moving Build Output to Documents

After building, you can move the installer to your Documents folder:

```powershell
# PowerShell
Move-Item "story-bible-electron\dist\Exelsias Setup*.exe" "$env:USERPROFILE\Documents\"
```

Or simply copy the entire `dist` folder:

```powershell
Copy-Item -Recurse "story-bible-electron\dist" "$env:USERPROFILE\Documents\Exelsias-Build"
```

---

## Troubleshooting

### "Failed to build llama-cpp-python"

Install Visual Studio Build Tools first, or use the pre-built wheel:

```powershell
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

### "spawn api_bridge.exe ENOENT"

This means the Python backend wasn't bundled correctly. Make sure:

1. PyInstaller completed successfully
2. `api_bridge.exe` exists in `story-bible-electron\backend\dist-win\`
3. Rebuild with `npm run build:win`

### "numpy version conflict"

```powershell
pip uninstall numpy -y
pip install numpy==1.26.4
```

### "Microsoft Visual C++ 14.0 or greater is required"

Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) with "Desktop development with C++" selected.

### "Model not found" on app startup

Make sure the LLaMA model is in the correct location:
- Development: `models/llama/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf`
- Production: The model will be bundled from the `models/` folder

---

## Project Structure

```
ricardoo/
├── src/                      # Python backend source
│   ├── database/
│   │   └── db_manager.py     # SQLite database management
│   ├── services/
│   │   ├── ai_engine.py      # LLaMA AI integration
│   │   └── tts_engine.py     # Text-to-speech
│   └── config/
│       └── manager.py        # Configuration management
├── models/
│   └── llama/                # Place LLaMA model here
│       └── Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
├── data/
│   └── database/             # SQLite database files
├── story-bible-electron/
│   ├── electron/
│   │   ├── main.js           # Electron main process
│   │   ├── preload.js        # Context bridge for IPC
│   │   └── package.json      # Build configuration
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.jsx       # Main React component
│   │   │   ├── components/   # UI components
│   │   │   └── hooks/        # React hooks
│   │   └── package.json
│   ├── backend/
│   │   ├── api_bridge.py     # Python JSON-RPC server
│   │   ├── backend.spec      # PyInstaller configuration
│   │   └── dist-win/         # Built Windows executable
│   ├── build/
│   │   ├── build.ps1         # Windows build script
│   │   └── build.sh          # Linux/Mac build script
│   └── dist/                 # Built installers
└── requirements.txt          # Python dependencies
```

---

## Features

### Writing Tools
- **Write**: Continue writing with AI assistance
- **Rewrite**: Transform text (Show Don't Tell, Dramatic, Elegant, etc.)
- **Describe**: Add sensory details (Sight, Sound, Smell, Taste, Touch)
- **3 Openings**: Generate three different chapter openings
- **Generate Draft**: AI-powered draft generation

### Story Bible
- **Braindump**: Free-form notes and ideas
- **Genre**: Set story genre and conventions
- **Style**: Define writing style and tone
- **Synopsis**: Story overview with AI generation
- **Characters**: Character profiles with AI generation
- **World Elements**: Locations, items, events with AI generation
- **Outline**: Plot structure with chapter cards

### AI Assistant (Right Panel)
- Context-aware responses using your story data
- Knowledge of all characters, world elements, and outline
- Markdown-formatted responses
- Insert generated content directly into editor

### Text-to-Speech
- Neural voices via Edge TTS
- Multiple voice options (US, UK, Australian, Indian)

---

## Required Model

Download the LLaMA model and place it in `models/llama/`:

**Model**: `Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf`

**Download from**: [HuggingFace](https://huggingface.co/lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF)

---

## License

MIT License - See LICENSE file for details.
