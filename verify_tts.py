from src.services.tts_engine import get_engine; print('Initializing...'); e = get_engine(); print('Loaded voices:', e.list_available_voices())
