import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add src to path to allow imports
sys.path.append(str(Path(__file__).resolve().parent / "src"))

from src.config.manager import ConfigManager
from src.database.db_manager import DatabaseManager
from src.services.ai_engine import AIEngine
from src.presentation.app import StoryBibleApp

import os

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS  # PyInstaller bundled path
else:
    base_path = os.path.dirname(__file__)

MODEL_PATH = os.path.join(base_path, 'models', 'llama', 'Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf')

# load your model here using MODEL_PATH


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
    logging.info("Starting Story Bible App - PyQt6 Version")
    
    # 1. Initialize Database
    try:
        db_mgr = DatabaseManager()
    except Exception as e:
        logging.critical(f"Database setup failed: {e}")
        return

    # 2. Initialize AI Engine (REAL LLAMA INTEGRATION)
    try:
        ai_engine = AIEngine()
    except Exception as e:
        logging.critical(f"AI Engine setup failed: {e}")
        return

    # 3. Launch PyQt6 Application
    try:
        # Enable high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        app = QApplication(sys.argv)
        app.setApplicationName("Story Bible Pro")
        app.setOrganizationName("StoryBible")
        
        # Create and show main window
        main_window = StoryBibleApp(ai_engine, db_mgr)
        main_window.show()
        
        # Start event loop
        exit_code = app.exec()
        
        logging.info("Application exited cleanly.")
        sys.exit(exit_code)
        
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