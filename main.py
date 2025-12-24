import sys
import logging
import customtkinter as ctk
from pathlib import Path

# Add src to path to allow imports
sys.path.append(str(Path(__file__).resolve().parent / "src"))

from src.config.manager import ConfigManager
from src.database.db_manager import DatabaseManager
from src.services.ai_engine import AIEngine
from src.ui.main_window import StoryBibleUI

def setup_logging():
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    logging.info("Starting Story Bible App - Milestone 1.3")
    
    # 1. Initialize Database
    try:
        db_mgr = DatabaseManager()
    except Exception as e:
        logging.critical(f"Database setup failed: {e}")
        return

    # 2. Initialize AI Engine (REAL LLAMA INTEGRATION)
    try:
        ai_engine = AIEngine()
        # ai_engine = MockAIEngine()
    except Exception as e:
        logging.critical(f"AI Engine setup failed: {e}")
        return

    # 3. Launch UI
    try:
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        app = StoryBibleUI(ai_engine, db_mgr)
        app.mainloop()
        
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt caught. Shutting down...")
        if ai_engine:
            ai_engine.unload_model()
    except Exception as e:
        logging.critical(f"Unhandled app exception: {e}", exc_info=True)
        if ai_engine:
            ai_engine.unload_model()
    finally:
        logging.info("App shutdown complete.")

if __name__ == "__main__":
    main()
