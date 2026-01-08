# Story Bible Pro

AI-powered creative writing assistant built with PyQt6.

## Project Structure

```
ai-desktop-assist/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # This file
│
├── src/                         # Source code
│   ├── __init__.py
│   │
│   ├── presentation/            # 🎨 UI Layer (PyQt6)
│   │   ├── __init__.py
│   │   ├── app.py               # Main application window (StoryBibleApp)
│   │   ├── theme.py             # Theme constants and styling (QtTheme)
│   │   │
│   │   ├── character/           # Character page components
│   │   │   └── character_widget.py
│   │   │
│   │   ├── dashboard/           # Dashboard/Home view
│   │   ├── editor/              # Writing canvas & toolbar
│   │   ├── sidebar/             # Project sidebar
│   │   ├── assistant/           # Lore Chat panel
│   │   └── shared/              # Shared UI components
│   │       ├── background.py    # Background widget
│   │       └── widgets.py       # Reusable widgets
│   │
│   ├── domain/                  # 📦 Business Logic Layer
│   │   ├── __init__.py
│   │   ├── models.py            # Domain models (Pydantic)
│   │   └── usecases/            # Business operations
│   │
│   ├── data/                    # 💾 Data Layer
│   │   ├── __init__.py
│   │   ├── database.py          # DatabaseManager (SQLite)
│   │   └── repositories/        # Data access patterns
│   │
│   ├── services/                # 🔧 External Services
│   │   ├── __init__.py
│   │   └── ai_engine.py         # AI/LLM integration (LLaMA)
│   │
│   ├── config/                  # ⚙️ Configuration
│   │   └── manager.py           # Config management
│   │
│   └── core/                    # Core utilities
│       └── config.py
│
├── assets/                      # Static assets
│   ├── images/                  # Background images
│   │   └── backgroundimg.png
│   └── styles/                  # QSS stylesheets
│       └── dark_theme.qss
│
├── models/                      # AI Models
│   ├── llama/                   # LLaMA model files
│   └── tts/                     # Text-to-speech models
│
├── data/                        # Runtime data
│   └── story_bible.db           # SQLite database
│
├── logs/                        # Application logs
│   └── app.log
│
└── docs/                        # Documentation
    └── *.md                     # Development notes
```

## Architecture

This project follows **Clean Architecture** principles:

### Presentation Layer (`src/presentation/`)
- PyQt6 UI components
- Views and widgets
- Theme and styling

### Domain Layer (`src/domain/`)
- Business logic
- Domain models
- Use cases

### Data Layer (`src/data/`)
- Database operations
- Repositories
- Data persistence

### Services Layer (`src/services/`)
- External integrations
- AI engine (LLaMA)

## Getting Started

```bash
# Create virtual environment
python -m venv deskapp
source deskapp/Scripts/activate  # Windows
source deskapp/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Features

- **Dashboard**: Project overview with card-based navigation
- **Writing Canvas**: Rich text editor with AI assistance
- **Character System**: AI-powered character generation
- **Story Bible**: Organized story elements
- **Lore Chat**: Interactive AI assistant

## Theme

The application uses a dark glass overlay theme with:
- Translucent backgrounds
- Smooth animations
- Premium visual polish
