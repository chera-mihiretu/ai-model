"""
Optimized TTS Engine with Realistic Neural Voices
==================================================
Uses Microsoft Edge TTS for natural, human-like speech.
Fast streaming, multiple voices, no model download needed.
"""

import os
import time
import logging
import threading
import asyncio
import tempfile
from typing import List, Optional
from pathlib import Path

# ============================================================
# EDGE TTS ENGINE - Realistic Neural Voices (Default)
# ============================================================

EDGE_TTS_AVAILABLE = False
PYGAME_AVAILABLE = False

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    logging.warning("edge-tts not available - install with: pip install edge-tts")
    edge_tts = None

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    logging.warning("pygame not available - install with: pip install pygame")
    pygame = None
except Exception as e:
    logging.warning(f"pygame init failed: {e}")
    pygame = None


class EdgeTTSEngine:
    """
    High-quality TTS using Microsoft Edge Neural Voices.
    
    Features:
    - Natural, human-like speech
    - Multiple voices (male/female, different accents)
    - Fast streaming playback
    - No large model downloads needed
    - Works with internet connection
    """
    
    # Popular high-quality voices
    VOICES = {
        # US English
        "Jenny (US Female)": "en-US-JennyNeural",
        "Aria (US Female)": "en-US-AriaNeural", 
        "Guy (US Male)": "en-US-GuyNeural",
        "Davis (US Male)": "en-US-DavisNeural",
        "Ana (US Female, Cheerful)": "en-US-AnaNeural",
        
        # UK English
        "Sonia (UK Female)": "en-GB-SoniaNeural",
        "Ryan (UK Male)": "en-GB-RyanNeural",
        "Libby (UK Female)": "en-GB-LibbyNeural",
        
        # Australian English
        "Natasha (AU Female)": "en-AU-NatashaNeural",
        "William (AU Male)": "en-AU-WilliamNeural",
        
        # Other accents
        "Neerja (Indian Female)": "en-IN-NeerjaNeural",
        "Prabhat (Indian Male)": "en-IN-PrabhatNeural",
        "Connor (Irish Male)": "en-IE-ConnorNeural",
        "Emily (Irish Female)": "en-IE-EmilyNeural",
        
        # Storytelling voices (great for books)
        "Sara (US, Storytelling)": "en-US-SaraNeural",
        "Tony (US, Conversational)": "en-US-TonyNeural",
        "Nancy (US, Friendly)": "en-US-NancyNeural",
    }
    
    # Default voice - sounds very natural
    DEFAULT_VOICE = "en-US-JennyNeural"
    
    def __init__(self, model_dir: str = "models/tts"):
        self.is_loaded = EDGE_TTS_AVAILABLE and PYGAME_AVAILABLE
        self.is_playing = False
        self.stop_flag = False
        self.current_voice = self.DEFAULT_VOICE
        self._playback_thread = None
        self._temp_files = []
        
        if self.is_loaded:
            logging.info("Edge TTS Engine initialized - Realistic neural voices ready!")
        else:
            if not EDGE_TTS_AVAILABLE:
                logging.warning("edge-tts not available")
            if not PYGAME_AVAILABLE:
                logging.warning("pygame not available")

    def list_available_voices(self) -> List[str]:
        """Returns list of available natural voices."""
        return list(self.VOICES.keys())
    
    def set_voice(self, voice_name: str):
        """Set the current voice by friendly name or voice ID."""
        if voice_name in self.VOICES:
            self.current_voice = self.VOICES[voice_name]
        elif voice_name.startswith("en-"):
            # Direct voice ID
            self.current_voice = voice_name
        else:
            # Default
            self.current_voice = self.DEFAULT_VOICE
    
    def tts_read_text(self, text: str, voice: str = "Jenny (US Female)", character_name: Optional[str] = None):
        """
        Speaks text using realistic neural voice.
        Streams audio for fast response.
        """
        if not self.is_loaded:
            logging.warning("Edge TTS not available")
            return
            
        if not text or not text.strip():
             return

        # Stop any current playback
        self.stop()
        
        self.stop_flag = False
        self.is_playing = True
        
        # Set voice
        self.set_voice(voice)
        
        # Run in background thread
        self._playback_thread = threading.Thread(
            target=self._speak_async_wrapper,
            args=(text,),
            daemon=True
        )
        self._playback_thread.start()
        
    def _speak_async_wrapper(self, text: str):
        """Wrapper to run async TTS in thread."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._generate_and_play(text))
            loop.close()
        except Exception as e:
            logging.error(f"TTS error: {e}")
        finally:
            self.is_playing = False
            self._cleanup_temp_files()
    
    async def _generate_and_play(self, text: str):
        """Generate speech and play it."""
        try:
            # Split into paragraphs for faster streaming
            paragraphs = self._split_text(text)
            
            for para in paragraphs:
                if self.stop_flag:
                    break
                    
                if not para.strip():
                    continue
                    
                # Generate audio to temp file
                temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                self._temp_files.append(temp_file.name)
                
                communicate = edge_tts.Communicate(para, self.current_voice)
                await communicate.save(temp_file.name)
                temp_file.close()
                
                if self.stop_flag:
                    break
                
                # Play the audio
                self._play_audio_file(temp_file.name)
                
        except Exception as e:
            logging.error(f"Error generating speech: {e}")

    def _play_audio_file(self, file_path: str):
        """Play an audio file using pygame."""
        if not pygame or self.stop_flag:
            return

        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                if self.stop_flag:
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.1)
                
        except Exception as e:
            logging.error(f"Playback error: {e}")
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into paragraphs for streaming."""
        import re
        # Split on paragraph breaks or every ~500 chars at sentence boundaries
        paragraphs = text.split('\n\n')
        
        result = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If paragraph is too long, split at sentences
            if len(para) > 500:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current = []
                current_len = 0
                
                for sent in sentences:
                    if current_len + len(sent) > 500:
                        if current:
                            result.append(' '.join(current))
                        current = [sent]
                        current_len = len(sent)
                    else:
                        current.append(sent)
                        current_len += len(sent)
                
                if current:
                    result.append(' '.join(current))
            else:
                result.append(para)
        
        return result
    
    def _cleanup_temp_files(self):
        """Clean up temporary audio files."""
        for f in self._temp_files:
            try:
                if os.path.exists(f):
                    os.unlink(f)
            except:
                pass
        self._temp_files = []

    def stop(self):
        """Stop current playback."""
        self.stop_flag = True
        self.is_playing = False
        
        if pygame:
            try:
                pygame.mixer.music.stop()
            except:
                pass

    def tts_generate_mp3(self, text: str, voice: str, output_path: str, progress_callback=None) -> str:
        """Generate MP3 file from text with progress tracking."""
        if not EDGE_TTS_AVAILABLE:
            return ""
            
        self.set_voice(voice)
        
        try:
            async def _generate():
                communicate = edge_tts.Communicate(text, self.current_voice)
                
                # Use streaming to track progress
                total_bytes = 0
                chunks_received = 0
                last_reported_progress = 0
                
                # Estimate total size based on text length (rough estimate)
                # Average: ~1000 bytes per 100 characters of text
                estimated_total = max(len(text) * 10, 10000)
                
                with open(output_path, "wb") as f:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])
                            total_bytes += len(chunk["data"])
                            chunks_received += 1
                            
                            # Report progress more frequently (every 3 chunks)
                            if progress_callback and chunks_received % 3 == 0:
                                # Calculate progress with better estimation
                                progress = min(95, int((total_bytes / estimated_total) * 100))
                                
                                # Only report if progress changed significantly (at least 5%)
                                if progress >= last_reported_progress + 5:
                                    progress_callback(progress)
                                    last_reported_progress = progress
                
                # Final progress update
                if progress_callback:
                    progress_callback(100)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_generate())
            loop.close()
            
            logging.info(f"Generated audio: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"Failed to generate MP3: {e}")
            return ""
            
    def add_paragraph_voice(self, name: str, wav_path: str):
        """Voice cloning not supported with Edge TTS."""
        return False, "Voice cloning requires XTTS model"
    
    def delete_paragraph_voice(self, name: str):
        return False
    
    def extract_speaker_embedding(self, wav_path: str):
        return None


class DummyTTSEngine:
    """Dummy TTS Engine when nothing is available."""
    
    def __init__(self, model_dir: str = "models/tts"):
        self.is_loaded = False
        self.is_playing = False
        logging.info("TTS Engine: Running in dummy mode")
    
    def list_available_voices(self) -> List[str]:
        return ["default"]
    
    def tts_read_text(self, text: str, voice: str = "default", character_name: Optional[str] = None):
        logging.info(f"TTS (dummy): Would speak: {text[:50]}...")
    
    def stop(self):
        self.is_playing = False
    
    def tts_generate_mp3(self, text: str, voice: str, output_path: str, progress_callback=None) -> str:
        return ""
    
    def add_paragraph_voice(self, name: str, wav_path: str):
        return False, "TTS not available"
    
    def delete_paragraph_voice(self, name: str):
        return False
    
    def extract_speaker_embedding(self, wav_path: str):
        return None


# ============================================================
# PYTTSX3 FALLBACK (Offline, robotic but works without internet)
# ============================================================

PYTTSX3_AVAILABLE = False
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    pyttsx3 = None


class OfflineTTSEngine:
    """
    Offline TTS using pyttsx3 (system TTS).
    Sounds robotic but works without internet.
    """
    
    def __init__(self, model_dir: str = "models/tts"):
        self.is_loaded = False
        self.is_playing = False
        self.stop_flag = False
        self.engine = None
        self._lock = threading.Lock()
        
        if PYTTSX3_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', 175)
                self.engine.setProperty('volume', 1.0)
                self.is_loaded = True
                logging.info("Offline TTS Engine initialized (pyttsx3)")
            except Exception as e:
                logging.error(f"pyttsx3 init failed: {e}")
    
    def list_available_voices(self) -> List[str]:
        return ["default", "fast", "slow"]
    
    def tts_read_text(self, text: str, voice: str = "default", character_name: Optional[str] = None):
        if not self.is_loaded or not self.engine:
            return
        
        self.stop_flag = False
        self.is_playing = True
        
        thread = threading.Thread(target=self._speak, args=(text, voice), daemon=True)
        thread.start()
    
    def _speak(self, text: str, voice: str):
        try:
            with self._lock:
                if voice == "fast":
                    self.engine.setProperty('rate', 220)
                elif voice == "slow":
                    self.engine.setProperty('rate', 130)
                else:
                    self.engine.setProperty('rate', 175)
                
                self.engine.say(text)
                self.engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS error: {e}")
        finally:
            self.is_playing = False
    
    def stop(self):
        self.stop_flag = True
        self.is_playing = False
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
    
    def tts_generate_mp3(self, text: str, voice: str, output_path: str, progress_callback=None) -> str:
        if not self.is_loaded:
            return ""
        try:
            if progress_callback:
                progress_callback(50)
            self.engine.save_to_file(text, output_path)
            self.engine.runAndWait()
            if progress_callback:
                progress_callback(100)
            return output_path
        except:
            return ""

    def add_paragraph_voice(self, name: str, wav_path: str):
        return False, "Not supported"
    
    def delete_paragraph_voice(self, name: str):
        return False
    
    def extract_speaker_embedding(self, wav_path: str):
        return None


# ============================================================
# SINGLETON ENGINE FACTORY
# ============================================================

_engine = None
_engine_type = "neural"  # Default to neural voices

def set_engine_type(engine_type: str):
    """
    Set which TTS engine to use:
    - "neural": Edge TTS with realistic voices (default, needs internet)
    - "offline": pyttsx3 system TTS (no internet, robotic voice)
    """
    global _engine, _engine_type
    _engine_type = engine_type
    _engine = None  # Force recreation

def get_engine():
    """
    Returns the TTS engine instance.
    Uses Edge TTS (neural voices) by default for realistic speech.
    """
    global _engine, _engine_type
    
    if _engine is None:
        if _engine_type == "neural" and EDGE_TTS_AVAILABLE and PYGAME_AVAILABLE:
            logging.info("🎙️ Using Edge TTS - Realistic neural voices")
            _engine = EdgeTTSEngine()
        elif _engine_type == "offline" and PYTTSX3_AVAILABLE:
            logging.info("📢 Using offline TTS (pyttsx3)")
            _engine = OfflineTTSEngine()
        elif EDGE_TTS_AVAILABLE and PYGAME_AVAILABLE:
            logging.info("🎙️ Using Edge TTS - Realistic neural voices")
            _engine = EdgeTTSEngine()
        elif PYTTSX3_AVAILABLE:
            logging.info("📢 Fallback: Using offline TTS (pyttsx3)")
            _engine = OfflineTTSEngine()
        else:
            logging.warning("⚠️ No TTS engine available")
            _engine = DummyTTSEngine()
    
    return _engine


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = get_engine()
    print(f"Engine loaded: {engine.is_loaded}")
    print(f"Available voices: {engine.list_available_voices()}")
    
    # Test speech
    engine.tts_read_text(
        "Hello! This is a test of the neural text to speech system. "
        "It should sound natural and human-like.",
        voice="Jenny (US Female)"
    )
    
    # Wait for speech to complete
    time.sleep(10)
