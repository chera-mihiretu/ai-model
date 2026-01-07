import sys
import os
import logging

logging.basicConfig(level=logging.DEBUG)

print(f"Python: {sys.version}")
print("Importing src.presentation.app...")
try:
    # Need to simulate main.py context
    sys.path.append(os.getcwd())
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    from src.presentation.app import StoryBibleApp
    print("src.presentation.app imported successfully.")
except Exception as e:
    print(f"Failed to import app: {e}")

print("Importing src.services.tts_engine...")
try:
    import src.services.tts_engine
    print("src.services.tts_engine imported successfully.")
    
    if src.services.tts_engine.Xtts is None:
        print("TTSEngine loaded but TTS module is None (Import failed inside).")
    else:
        print("TTSEngine loaded and TTS module is available.")
        
except Exception as e:
    print(f"Failed to import tts_engine: {e}")
