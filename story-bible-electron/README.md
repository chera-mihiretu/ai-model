# Story Bible Pro - Electron Edition

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
│  │  • Beautiful glass-effect theme                     │   │
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

- Node.js 18+ and npm
- Python 3.10+
- Git

### Install Dependencies

```bash
# Install frontend dependencies
cd frontend
npm install

# Install Electron dependencies
cd ../electron
npm install

# Set up Python environment (from project root)
cd ..
python -m venv deskapp
source deskapp/bin/activate  # Linux/Mac
# or: deskapp\Scripts\activate  # Windows
pip install -r ../requirements.txt
```

### Development Mode

Run the app in development mode with hot reloading:

```bash
# Terminal 1: Start the frontend dev server
cd frontend
npm run dev

# Terminal 2: Start Electron (after frontend is ready)
cd ../electron
npm start
```

Or use the combined command:

```bash
cd electron
npm run dev
```

## Building for Production

### Full Build

Use the build scripts to create a distributable package:

```bash
# Linux/Mac
chmod +x build/build.sh
./build/build.sh

# Windows (PowerShell)
.\build\build.ps1
```

### Build Options

```bash
# Build for current platform only
./build/build.sh

# Build for all platforms
./build/build.sh --all

# Development build (skip packaging)
./build/build.sh --dev
```

## Project Structure

```
story-bible-electron/
├── electron/
│   ├── main.js           # Electron main process
│   ├── preload.js        # Context bridge for IPC
│   └── package.json      # Electron dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # Main React component
│   │   ├── components/   # UI components
│   │   │   ├── Toolbar.jsx
│   │   │   ├── ProjectSidebar.jsx
│   │   │   ├── Editor.jsx
│   │   │   ├── StoryBible.jsx
│   │   │   ├── CharacterManager.jsx
│   │   │   ├── AssistantPanel.jsx
│   │   │   └── Notifications.jsx
│   │   ├── hooks/
│   │   │   ├── useStore.js         # Zustand state
│   │   │   └── usePythonBridge.js  # Python IPC
│   │   └── styles/
│   │       └── index.css           # Tailwind + custom styles
│   ├── index.html
│   └── package.json
├── backend/
│   ├── api_bridge.py     # Python JSON-RPC server
│   └── backend.spec      # PyInstaller configuration
├── build/
│   ├── build.sh          # Linux/Mac build script
│   └── build.ps1         # Windows build script
└── README.md
```

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
- **Synopsis**: Story overview
- **Characters**: Character profiles with AI generation
- **Worldbuilding**: World details and rules
- **Outline**: Plot structure

### AI Features
- Local LLaMA 3.1 8B model (runs offline)
- Context-aware writing suggestions
- Character-consistent dialogue
- Lore Assistant for story Q&A

### Text-to-Speech
- Neural voices via Edge TTS
- Multiple voice options (US, UK, Australian, Indian)
- Offline fallback with pyttsx3

## License

MIT License - See LICENSE file for details.

