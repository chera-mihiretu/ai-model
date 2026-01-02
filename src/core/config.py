from pathlib import Path
from pydantic import BaseModel

class AppConfig(BaseModel):
    APP_NAME: str = "AI Desktop Assistant"
    VERSION: str = "0.1.0"
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "models"
    LLAMA_MODEL_PATH: Path = MODELS_DIR / "llama"
    TTS_MODEL_PATH: Path = MODELS_DIR / "tts"
    DATABASE_PATH: Path = DATA_DIR / "app_database.db"
    
    # UI
    WINDOW_TITLE: str = "AI Assistant"
    WINDOW_SIZE: tuple[int, int] = (1200, 800)

config = AppConfig()
