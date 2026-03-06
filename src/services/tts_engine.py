"""
TTS Engine with Cloud and Local Options
========================================
Supports two modes:
- Cloud: Microsoft Edge TTS (requires internet, high quality neural voices)
- Local: Piper TTS (offline, good quality neural voices)
"""

import os
import sys
import time
import logging
import threading
import asyncio
import tempfile
import wave
import io
from typing import List, Optional, Dict, Any, Callable
from pathlib import Path

# ============================================================
# AVAILABILITY FLAGS
# ============================================================

EDGE_TTS_AVAILABLE = False
PIPER_TTS_AVAILABLE = False
PYGAME_AVAILABLE = False

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    logging.warning("edge-tts not available - install with: pip install edge-tts")
    edge_tts = None

try:
    from piper import PiperVoice
    PIPER_TTS_AVAILABLE = True
except ImportError:
    logging.warning("piper-tts not available - install with: pip install piper-tts")
    PiperVoice = None

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
# PIPER TTS ENGINE - Local/Offline Neural Voices
# ============================================================

def get_piper_models_dir() -> Path:
    """Get the directory for storing Piper voice models."""
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', os.path.expanduser('~')))
        return base / 'Exelsias' / 'models' / 'piper'
    elif sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'Exelsias' / 'models' / 'piper'
    else:
        return Path.home() / '.config' / 'exelsias' / 'models' / 'piper'


# Piper voice models available for download (English voices)
PIPER_VOICE_MODELS = {
    "Amy (US Female)": {
        "id": "en_US-amy-medium",
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json",
        "size_mb": 63
    },
    "Ryan (US Male)": {
        "id": "en_US-ryan-medium",
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json",
        "size_mb": 63
    },
    "Lessac (US Female)": {
        "id": "en_US-lessac-medium",
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
        "size_mb": 63
    },
    "Libritts (US Neutral)": {
        "id": "en_US-libritts-high",
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts/high/en_US-libritts-high.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts/high/en_US-libritts-high.onnx.json",
        "size_mb": 75
    },
    "Jenny (UK Female)": {
        "id": "en_GB-jenny_dioco-medium",
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium.onnx.json",
        "size_mb": 63
    },
    "Alan (UK Male)": {
        "id": "en_GB-alan-medium",
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json",
        "size_mb": 63
    },
}

# Global download progress tracker
_piper_download_progress = 0


class PiperTTSEngine:
    """
    Local/Offline TTS using Piper neural voices.
    
    Features:
    - Good quality neural voices
    - Works completely offline (after model download)
    - Multiple voice options
    - No internet required after setup
    """
    
    DEFAULT_VOICE = "Amy (US Female)"
    
    def __init__(self, model_dir: str = None):
        self.model_dir = Path(model_dir) if model_dir else get_piper_models_dir()
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.is_loaded = PIPER_TTS_AVAILABLE and PYGAME_AVAILABLE
        self.is_playing = False
        self.stop_flag = False
        self.current_voice = self.DEFAULT_VOICE
        self.current_piper_voice = None
        self._playback_thread = None
        self._temp_files = []
        
        if self.is_loaded:
            logging.info(f"Piper TTS Engine initialized - Models dir: {self.model_dir}")
            # Try to load a default voice if available
            self._try_load_default_voice()
        else:
            if not PIPER_TTS_AVAILABLE:
                logging.warning("piper-tts not available")
            if not PYGAME_AVAILABLE:
                logging.warning("pygame not available")
    
    def _try_load_default_voice(self):
        """Try to load a default voice if one is downloaded."""
        downloaded = self.list_downloaded_voices()
        if downloaded:
            try:
                self._load_voice(downloaded[0])
                self.current_voice = downloaded[0]
                logging.info(f"Loaded default Piper voice: {downloaded[0]}")
            except Exception as e:
                logging.warning(f"Could not load default voice: {e}")
    
    def _get_voice_paths(self, voice_name: str) -> tuple:
        """Get model and config paths for a voice."""
        if voice_name not in PIPER_VOICE_MODELS:
            return None, None
        
        voice_info = PIPER_VOICE_MODELS[voice_name]
        voice_id = voice_info["id"]
        model_path = self.model_dir / f"{voice_id}.onnx"
        config_path = self.model_dir / f"{voice_id}.onnx.json"
        return model_path, config_path
    
    def _load_voice(self, voice_name: str):
        """Load a Piper voice model."""
        if not PIPER_TTS_AVAILABLE:
            raise RuntimeError("Piper TTS not available")
        
        model_path, config_path = self._get_voice_paths(voice_name)
        if not model_path or not model_path.exists():
            raise FileNotFoundError(f"Voice model not downloaded: {voice_name}")
        
        self.current_piper_voice = PiperVoice.load(str(model_path), str(config_path))
        self.current_voice = voice_name
        logging.info(f"Loaded Piper voice: {voice_name}")
    
    def is_voice_downloaded(self, voice_name: str) -> bool:
        """Check if a voice model is downloaded."""
        model_path, config_path = self._get_voice_paths(voice_name)
        if not model_path:
            return False
        return model_path.exists() and config_path.exists()
    
    def list_downloaded_voices(self) -> List[str]:
        """List all downloaded voice models."""
        downloaded = []
        for voice_name in PIPER_VOICE_MODELS:
            if self.is_voice_downloaded(voice_name):
                downloaded.append(voice_name)
        return downloaded
    
    def list_available_voices(self) -> List[str]:
        """Returns list of downloaded voices (for compatibility with other engines)."""
        return self.list_downloaded_voices()
    
    def list_all_voices(self) -> List[Dict[str, Any]]:
        """List all available voices with download status."""
        voices = []
        for voice_name, info in PIPER_VOICE_MODELS.items():
            voices.append({
                "name": voice_name,
                "id": info["id"],
                "size_mb": info["size_mb"],
                "downloaded": self.is_voice_downloaded(voice_name)
            })
        return voices
    
    def download_voice(self, voice_name: str, progress_callback: Callable[[int], None] = None) -> bool:
        """Download a Piper voice model."""
        global _piper_download_progress
        
        if voice_name not in PIPER_VOICE_MODELS:
            logging.error(f"Unknown voice: {voice_name}")
            return False
        
        voice_info = PIPER_VOICE_MODELS[voice_name]
        model_path, config_path = self._get_voice_paths(voice_name)
        
        try:
            import requests
            
            _piper_download_progress = 0
            
            # Download model file
            logging.info(f"Downloading Piper voice: {voice_name}")
            
            response = requests.get(voice_info["model_url"], stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 90)
                            _piper_download_progress = progress
                            if progress_callback:
                                progress_callback(progress)
            
            # Download config file
            _piper_download_progress = 92
            if progress_callback:
                progress_callback(92)
            
            config_response = requests.get(voice_info["config_url"])
            config_response.raise_for_status()
            
            with open(config_path, 'wb') as f:
                f.write(config_response.content)
            
            _piper_download_progress = 100
            if progress_callback:
                progress_callback(100)
            
            logging.info(f"Downloaded Piper voice: {voice_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to download voice {voice_name}: {e}")
            # Clean up partial downloads
            if model_path.exists():
                model_path.unlink()
            if config_path.exists():
                config_path.unlink()
            return False
    
    def delete_voice(self, voice_name: str) -> bool:
        """Delete a downloaded voice model."""
        model_path, config_path = self._get_voice_paths(voice_name)
        if not model_path:
            return False
        
        try:
            if model_path.exists():
                model_path.unlink()
            if config_path.exists():
                config_path.unlink()
            logging.info(f"Deleted Piper voice: {voice_name}")
            return True
        except Exception as e:
            logging.error(f"Failed to delete voice {voice_name}: {e}")
            return False
    
    def set_voice(self, voice_name: str):
        """Set the current voice."""
        if voice_name in PIPER_VOICE_MODELS and self.is_voice_downloaded(voice_name):
            if voice_name != self.current_voice or self.current_piper_voice is None:
                try:
                    self._load_voice(voice_name)
                except Exception as e:
                    logging.error(f"Failed to load voice {voice_name}: {e}")
    
    def tts_read_text(self, text: str, voice: str = None, character_name: Optional[str] = None):
        """Speak text using Piper TTS."""
        if not self.is_loaded:
            logging.warning("Piper TTS not available")
            return
        
        if not text or not text.strip():
            return
        
        # Stop any current playback
        self.stop()
        
        self.stop_flag = False
        self.is_playing = True
        
        # Set voice if specified
        if voice:
            self.set_voice(voice)
        
        if not self.current_piper_voice:
            downloaded = self.list_downloaded_voices()
            if downloaded:
                self.set_voice(downloaded[0])
            else:
                logging.error("No Piper voice downloaded. Please download a voice first.")
                self.is_playing = False
                return
        
        # Run in background thread
        self._playback_thread = threading.Thread(
            target=self._speak_threaded,
            args=(text,),
            daemon=True
        )
        self._playback_thread.start()
    
    def _speak_threaded(self, text: str):
        """Generate and play speech in a thread."""
        try:
            # Split text into manageable chunks
            chunks = self._split_text(text)
            
            for i, chunk in enumerate(chunks):
                if self.stop_flag:
                    break
                
                if not chunk.strip():
                    continue
                
                # Generate audio to temp file
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                self._temp_files.append(temp_file.name)
                temp_file.close()
                
                # Synthesize with Piper
                with wave.open(temp_file.name, 'wb') as wav_file:
                    self.current_piper_voice.synthesize_wav(chunk, wav_file)
                
                if self.stop_flag:
                    break
                
                # Play the audio
                self._play_audio_file(temp_file.name)
                
        except Exception as e:
            logging.error(f"Piper TTS error: {e}")
        finally:
            self.is_playing = False
            self._cleanup_temp_files()
    
    def _play_audio_file(self, file_path: str):
        """Play an audio file using pygame."""
        if not pygame or self.stop_flag:
            return
        
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                if self.stop_flag:
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.1)
                
        except Exception as e:
            logging.error(f"Playback error: {e}")
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks for processing."""
        import re
        paragraphs = text.split('\n\n')
        
        result = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
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
        """Generate audio file from text."""
        if not self.is_loaded or not self.current_piper_voice:
            return ""
        
        if voice:
            self.set_voice(voice)
        
        if not self.current_piper_voice:
            return ""
        
        try:
            # Generate WAV first
            wav_path = output_path.replace('.mp3', '.wav')
            
            if progress_callback:
                progress_callback(10)
            
            with wave.open(wav_path, 'wb') as wav_file:
                self.current_piper_voice.synthesize_wav(text, wav_file)
            
            if progress_callback:
                progress_callback(90)
            
            # For now, just return the WAV file (MP3 conversion would need additional library)
            if progress_callback:
                progress_callback(100)
            
            return wav_path
            
        except Exception as e:
            logging.error(f"Failed to generate audio: {e}")
            return ""
    
    def add_paragraph_voice(self, name: str, wav_path: str):
        return False, "Voice cloning not supported"
    
    def delete_paragraph_voice(self, name: str):
        return False
    
    def extract_speaker_embedding(self, wav_path: str):
        return None


def get_piper_download_progress() -> int:
    """Get current Piper voice download progress."""
    global _piper_download_progress
    return _piper_download_progress


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

_cloud_engine = None  # Edge TTS engine
_local_engine = None  # Piper TTS engine
_current_mode = "cloud"  # Default to cloud (Edge TTS)


def set_tts_mode(mode: str) -> dict:
    """
    Set which TTS engine to use:
    - "cloud": Edge TTS with realistic voices (default, needs internet)
    - "local": Piper TTS with neural voices (offline, requires model download)
    
    Returns status dict with success and any error message.
    Allows switching to local even if Piper is not installed (for pre-downloading voices).
    """
    global _current_mode
    
    if mode not in ("cloud", "local"):
        return {"success": False, "error": f"Invalid mode: {mode}. Use 'cloud' or 'local'."}
    
    warnings = []
    
    if mode == "local":
        if not PIPER_TTS_AVAILABLE:
            warnings.append("Piper TTS engine not installed. Voice playback won't work until piper-tts is installed, but you can still download voices.")
        if not PYGAME_AVAILABLE:
            warnings.append("pygame not available for audio playback")
        
        # Check if any voices are downloaded
        downloaded_voices = [v for v in list_local_voices() if v.get("downloaded")]
        if not downloaded_voices:
            warnings.append("No local voices downloaded. Please download a voice to use local TTS.")
    
    elif mode == "cloud":
        if not EDGE_TTS_AVAILABLE:
            return {"success": False, "error": "Edge TTS not available. Install with: pip install edge-tts"}
        if not PYGAME_AVAILABLE:
            return {"success": False, "error": "pygame not available for audio playback"}
    
    _current_mode = mode
    logging.info(f"TTS mode set to: {mode}")
    
    result = {"success": True, "mode": mode}
    if warnings:
        result["warning"] = " ".join(warnings)
    return result


def get_tts_mode() -> str:
    """Get current TTS mode ('cloud' or 'local')."""
    return _current_mode


def get_cloud_engine():
    """Get the cloud (Edge TTS) engine instance."""
    global _cloud_engine
    if _cloud_engine is None:
        if EDGE_TTS_AVAILABLE and PYGAME_AVAILABLE:
            _cloud_engine = EdgeTTSEngine()
        else:
            _cloud_engine = DummyTTSEngine()
    return _cloud_engine


def get_local_engine():
    """Get the local (Piper TTS) engine instance."""
    global _local_engine
    if _local_engine is None:
        if PIPER_TTS_AVAILABLE and PYGAME_AVAILABLE:
            _local_engine = PiperTTSEngine()
        else:
            _local_engine = DummyTTSEngine()
    return _local_engine


def get_engine():
    """
    Returns the current TTS engine based on mode setting.
    """
    if _current_mode == "local":
        return get_local_engine()
    else:
        return get_cloud_engine()


# Legacy function for backward compatibility
def set_engine_type(engine_type: str):
    """Legacy function - use set_tts_mode instead."""
    if engine_type == "neural":
        set_tts_mode("cloud")
    elif engine_type == "offline" or engine_type == "local":
        set_tts_mode("local")


# ============================================================
# HELPER FUNCTIONS FOR LOCAL TTS
# ============================================================

def _get_piper_model_dir() -> Path:
    """Get the directory for storing Piper voice models (works even without Piper installed)."""
    return get_piper_models_dir()


def _is_voice_downloaded(voice_name: str) -> bool:
    """Check if a voice model is downloaded (works even without Piper installed)."""
    if voice_name not in PIPER_VOICE_MODELS:
        return False
    
    voice_info = PIPER_VOICE_MODELS[voice_name]
    voice_id = voice_info["id"]
    model_dir = _get_piper_model_dir()
    model_path = model_dir / f"{voice_id}.onnx"
    config_path = model_dir / f"{voice_id}.onnx.json"
    return model_path.exists() and config_path.exists()


def list_local_voices() -> List[Dict[str, Any]]:
    """List all available local (Piper) voices with download status.
    Works even when Piper TTS is not installed - allows downloading voices in advance.
    """
    # First try the engine if available
    engine = get_local_engine()
    if hasattr(engine, 'list_all_voices'):
        return engine.list_all_voices()
    
    # Fallback: list voices from PIPER_VOICE_MODELS directly
    # This allows viewing and downloading voices even without piper-tts installed
    voices = []
    for voice_name, info in PIPER_VOICE_MODELS.items():
        voices.append({
            "name": voice_name,
            "id": info["id"],
            "size_mb": info["size_mb"],
            "downloaded": _is_voice_downloaded(voice_name)
        })
    return voices


def download_local_voice(voice_name: str, progress_callback: Callable[[int], None] = None) -> bool:
    """Download a local (Piper) voice model.
    Works even when Piper TTS is not installed - users can pre-download voices.
    """
    global _piper_download_progress
    
    # First try the engine if available
    engine = get_local_engine()
    if hasattr(engine, 'download_voice'):
        return engine.download_voice(voice_name, progress_callback)
    
    # Fallback: download directly (works without piper-tts installed)
    if voice_name not in PIPER_VOICE_MODELS:
        logging.error(f"Unknown voice: {voice_name}")
        return False
    
    voice_info = PIPER_VOICE_MODELS[voice_name]
    voice_id = voice_info["id"]
    model_dir = _get_piper_model_dir()
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = model_dir / f"{voice_id}.onnx"
    config_path = model_dir / f"{voice_id}.onnx.json"
    
    try:
        import requests
        
        _piper_download_progress = 0
        
        # Download model file
        logging.info(f"Downloading Piper voice: {voice_name}")
        
        response = requests.get(voice_info["model_url"], stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(model_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = int((downloaded / total_size) * 90)
                        _piper_download_progress = progress
                        if progress_callback:
                            progress_callback(progress)
        
        # Download config file
        _piper_download_progress = 92
        if progress_callback:
            progress_callback(92)
        
        config_response = requests.get(voice_info["config_url"])
        config_response.raise_for_status()
        
        with open(config_path, 'wb') as f:
            f.write(config_response.content)
        
        _piper_download_progress = 100
        if progress_callback:
            progress_callback(100)
        
        logging.info(f"Downloaded Piper voice: {voice_name}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to download voice {voice_name}: {e}")
        # Clean up partial downloads
        if model_path.exists():
            model_path.unlink()
        if config_path.exists():
            config_path.unlink()
        return False


def delete_local_voice(voice_name: str) -> bool:
    """Delete a local (Piper) voice model.
    Works even when Piper TTS is not installed.
    """
    # First try the engine if available
    engine = get_local_engine()
    if hasattr(engine, 'delete_voice'):
        return engine.delete_voice(voice_name)
    
    # Fallback: delete directly
    if voice_name not in PIPER_VOICE_MODELS:
        return False
    
    voice_info = PIPER_VOICE_MODELS[voice_name]
    voice_id = voice_info["id"]
    model_dir = _get_piper_model_dir()
    model_path = model_dir / f"{voice_id}.onnx"
    config_path = model_dir / f"{voice_id}.onnx.json"
    
    try:
        if model_path.exists():
            model_path.unlink()
        if config_path.exists():
            config_path.unlink()
        logging.info(f"Deleted Piper voice: {voice_name}")
        return True
    except Exception as e:
        logging.error(f"Failed to delete voice {voice_name}: {e}")
        return False


def get_tts_availability() -> Dict[str, bool]:
    """Check availability of TTS engines."""
    return {
        "cloud": EDGE_TTS_AVAILABLE and PYGAME_AVAILABLE,
        "local": PIPER_TTS_AVAILABLE and PYGAME_AVAILABLE,
        "edge_tts": EDGE_TTS_AVAILABLE,
        "piper_tts": PIPER_TTS_AVAILABLE,
        "pygame": PYGAME_AVAILABLE
    }


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("TTS Availability:", get_tts_availability())
    print("Current mode:", get_tts_mode())
    
    engine = get_engine()
    print(f"Engine loaded: {engine.is_loaded}")
    print(f"Available voices: {engine.list_available_voices()}")
    
    # Test speech
    engine.tts_read_text(
        "Hello! This is a test of the text to speech system. "
        "It should sound natural and human-like.",
        voice="Jenny (US Female)"
    )
    
    # Wait for speech to complete
    time.sleep(10)
