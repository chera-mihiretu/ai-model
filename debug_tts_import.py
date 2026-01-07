import sys
import traceback

print(f"Python: {sys.version}")
print(f"Executable: {sys.executable}")
print("Attempting to import TTS...")
try:
    import TTS
    print(f"TTS version: {TTS.__version__}")
    from TTS.tts.configs.xtts_config import XttsConfig
    print("XttsConfig imported successfully")
except Exception:
    traceback.print_exc()
