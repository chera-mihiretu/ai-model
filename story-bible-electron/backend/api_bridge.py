"""
Python JSON-RPC API Bridge for Exelsias
=======================================
Exposes all backend services via stdin/stdout JSON-RPC protocol.
This allows Electron to communicate with Python services.
"""

import sys
import os
import json
import queue
import logging
import threading
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

# Determine project root from environment or file location
project_root = os.environ.get('EXELSIAS_PROJECT_ROOT')
if project_root:
    sys.path.insert(0, project_root)
else:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.db_manager import DatabaseManager
from src.services.ai_engine import AIEngine
from src.services.tts_engine import (
    get_engine as get_tts_engine,
    get_tts_mode,
    set_tts_mode,
    get_tts_availability,
    list_local_voices,
    download_local_voice,
    delete_local_voice,
    get_piper_download_progress,
    get_cloud_engine,
    get_local_engine,
)
from src.config.manager import ConfigManager
from src.domain.usecases.import_parser import ImportParser

# Configure logging - use data path if available
data_path = os.environ.get('EXELSIAS_DATA_PATH')
if data_path:
    log_dir = Path(data_path).parent / "logs"
else:
    log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "api_bridge.log"),
        logging.StreamHandler(sys.stderr)
    ]
)

# Log environment info for debugging
logging.info(f"EXELSIAS_PROJECT_ROOT: {os.environ.get('EXELSIAS_PROJECT_ROOT')}")
logging.info(f"EXELSIAS_DATA_PATH: {os.environ.get('EXELSIAS_DATA_PATH')}")
logging.info(f"EXELSIAS_MODELS_PATH: {os.environ.get('EXELSIAS_MODELS_PATH')}")


class APIBridge:
    """
    Main API Bridge class that handles JSON-RPC requests.
    Wraps DatabaseManager, AIEngine, and TTSEngine.
    """
    
    def __init__(self):
        logging.info("Initializing API Bridge...")
        
        # Initialize services
        self.db = DatabaseManager()
        self.ai = AIEngine()
        self.tts = get_tts_engine()
        self.config = ConfigManager()
        self.import_parser = ImportParser(ai_engine=self.ai)
        
        # Response queue for AI streaming
        self.ai_response_queue = queue.Queue()
        self.ai_thread = None
        
        # Summarization debounce: track last trigger time per (project_id, content_type)
        self._summary_cooldowns = {}  # key: "pid:ctype" -> timestamp
        self._summary_running = False  # prevent overlapping summarizations
        self._SUMMARY_COOLDOWN_SECS = 120  # minimum seconds between summarizations per type
        
        # TTS download progress tracking
        self._tts_download_progress = 0
        self._tts_download_lock = threading.Lock()
        
        logging.info("API Bridge initialized successfully")
    
    def _trigger_bg_summary(self, project_id: str = None, content_type: str = '', chapter_id: str = None, element_id: str = None):
        """Trigger background summarization with debouncing and busy-check."""
        import time
        
        try:
            # Resolve project_id from chapter_id or element_id if not provided
            if not project_id and chapter_id:
                try:
                    with self.db.get_connection() as conn:
                        cursor = conn.execute("SELECT project_id FROM chapters WHERE id = ?", (chapter_id,))
                        row = cursor.fetchone()
                        project_id = row[0] if row else None
                except Exception:
                    pass
            
            if not project_id and element_id:
                try:
                    with self.db.get_connection() as conn:
                        cursor = conn.execute("SELECT project_id FROM world_elements WHERE id = ?", (element_id,))
                        row = cursor.fetchone()
                        project_id = row[0] if row else None
                except Exception:
                    pass
            
            if not project_id or not content_type:
                return
            
            # --- Debounce check ---
            cooldown_key = f"{project_id}:{content_type}"
            now = time.time()
            last_trigger = self._summary_cooldowns.get(cooldown_key, 0)
            if now - last_trigger < self._SUMMARY_COOLDOWN_SECS:
                logging.debug(f"Skipping bg summary for {cooldown_key}: cooldown ({int(now - last_trigger)}s < {self._SUMMARY_COOLDOWN_SECS}s)")
                return
            
            # --- Skip if AI is currently busy with user-facing work ---
            if self._summary_running:
                logging.debug(f"Skipping bg summary for {cooldown_key}: another summarization already running")
                return
            if self.ai.lock.locked():
                logging.debug(f"Skipping bg summary for {cooldown_key}: AI model is busy")
                return
            
            # Mark cooldown and start
            self._summary_cooldowns[cooldown_key] = now
            
            def _bg_summarize(pid, ctype):
                try:
                    self._summary_running = True
                    logging.info(f"Background summarization started: project={pid}, type={ctype}")
                    self.ai.generate_content_summaries(pid, ctype, self.db)
                    logging.info(f"Background summarization complete: project={pid}, type={ctype}")
                except Exception as e:
                    logging.error(f"Background summarization error ({ctype}): {e}", exc_info=True)
                finally:
                    self._summary_running = False
            
            threading.Thread(
                target=_bg_summarize,
                args=(str(project_id), content_type),
                daemon=True
            ).start()
        except Exception as e:
            logging.error(f"_trigger_bg_summary error: {e}")
    
    def handle_request(self, request: Dict) -> Dict:
        """
        Handle incoming JSON-RPC request and return response.
        """
        method = request.get('method', '')
        params = request.get('params', {})
        request_id = request.get('id', None)
        
        try:
            result = self._dispatch(method, params)
            return {
                'jsonrpc': '2.0',
                'result': result,
                'id': request_id
            }
        except Exception as e:
            logging.error(f"Error handling request {method}: {e}")
            logging.error(traceback.format_exc())
            return {
                'jsonrpc': '2.0',
                'error': {
                    'code': -32000,
                    'message': str(e)
                },
                'id': request_id
            }
    
    def _validate_string(self, value: Any, field_name: str, max_length: int = 1000, required: bool = False) -> str:
        """Validate and sanitize string input."""
        if value is None:
            if required:
                raise ValueError(f"{field_name} is required")
            return ''
        if not isinstance(value, str):
            value = str(value)
        if len(value) > max_length:
            raise ValueError(f"{field_name} exceeds maximum length of {max_length} characters")
        return value
    
    def _validate_int(self, value: Any, field_name: str, required: bool = False) -> Optional[int]:
        """Validate integer input."""
        if value is None:
            if required:
                raise ValueError(f"{field_name} is required")
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be a valid integer")
    
    def _dispatch(self, method: str, params: Dict) -> Any:
        """
        Dispatch method call to appropriate service.
        """
        # ==================== PROJECT METHODS ====================
        if method == 'get_projects':
            return self.db.get_projects()
        
        elif method == 'get_projects_with_chapters':
            return self.db.get_projects_with_chapters()
        
        elif method == 'create_project':
            name = self._validate_string(params.get('name', 'New Project'), 'name', max_length=500)
            genre = self._validate_string(params.get('genre', ''), 'genre', max_length=5000)
            return self.db.create_project(name, genre)
        
        elif method == 'delete_project':
            project_id = self._validate_string(params.get('project_id'), 'project_id', required=True)
            return self.db.delete_project(project_id)
        
        elif method == 'rename_project':
            project_id = self._validate_string(params.get('project_id'), 'project_id', required=True)
            new_name = self._validate_string(params.get('new_name'), 'new_name', max_length=500, required=True)
            return self.db.rename_project(project_id, new_name)
        
        elif method == 'get_project_settings':
            project_id = params.get('project_id')
            return self.db.get_project_settings(project_id)
        
        # ==================== RECYCLE BIN METHODS ====================
        elif method == 'move_project_to_recycle_bin':
            project_id = params.get('project_id')
            return self.db.move_project_to_recycle_bin(project_id)
        
        elif method == 'move_to_recycle_bin':
            item_type = params.get('item_type')
            item_id = params.get('item_id')
            item_data = params.get('item_data')
            return self.db.move_to_recycle_bin(item_type, item_id, item_data)
        
        elif method == 'get_recycle_bin_items':
            return self.db.get_recycle_bin_items()
        
        elif method == 'restore_from_recycle_bin':
            recycle_id = params.get('recycle_id')
            return self.db.restore_from_recycle_bin(recycle_id)
        
        elif method == 'permanent_delete_from_recycle_bin':
            recycle_id = params.get('recycle_id')
            return self.db.permanent_delete_from_recycle_bin(recycle_id)
        
        elif method == 'empty_recycle_bin':
            return self.db.empty_recycle_bin()
        
        elif method == 'get_full_project_data':
            project_id = params.get('project_id')
            return self.db.get_full_project_data(project_id)
        
        # ==================== CHAPTER METHODS ====================
        elif method == 'create_chapter':
            project_id = self._validate_string(params.get('project_id'), 'project_id', required=True)
            title = self._validate_string(params.get('title', 'New Chapter'), 'title', max_length=500)
            content = params.get('content', '')  # Content can be very large, no limit
            return self.db.create_chapter(project_id, title, content)
        
        elif method == 'get_chapters':
            project_id = params.get('project_id')
            return self.db.get_chapters(project_id)
        
        elif method == 'get_chapter_content':
            chapter_id = params.get('chapter_id')
            return self.db.get_chapter_content(chapter_id)
        
        elif method == 'update_chapter_content':
            # Note: chapter saves happen on every auto-save, so we use an extra-long
            # cooldown for chapter summarization. The _SUMMARY_COOLDOWN_SECS (120s) plus
            # the lock-busy check prevents summarization from blocking user-facing AI ops.
            chapter_id = params.get('chapter_id')
            content = params.get('content')
            result = self.db.update_chapter_content(chapter_id, content)
            # Only trigger summarization for substantial content and with a very
            # conservative debounce - we rely on the 120s cooldown in _trigger_bg_summary
            # and the lock-busy check to avoid starving user-facing operations
            if result and chapter_id and content and len(content) > 2000:
                self._trigger_bg_summary(chapter_id=chapter_id, content_type='chapters')
            return result
        
        elif method == 'rename_chapter':
            chapter_id = params.get('chapter_id')
            new_title = params.get('new_title')
            return self.db.rename_chapter(chapter_id, new_title)
        
        elif method == 'delete_chapter':
            chapter_id = params.get('chapter_id')
            return self.db.delete_chapter(chapter_id)
        
        elif method == 'move_chapter_up':
            chapter_id = params.get('chapter_id')
            return self.db.move_chapter_up(chapter_id)
        
        elif method == 'move_chapter_down':
            chapter_id = params.get('chapter_id')
            return self.db.move_chapter_down(chapter_id)
        
        elif method == 'get_chapter_beats':
            chapter_id = params.get('chapter_id')
            return self.db.get_chapter_beats(chapter_id)
        
        elif method == 'update_chapter_beats':
            chapter_id = params.get('chapter_id')
            beats_text = params.get('beats_text')
            return self.db.update_chapter_beats(chapter_id, beats_text)
        
        # ==================== CHARACTER METHODS ====================
        elif method == 'get_characters':
            project_id = params.get('project_id')
            return self.db.get_characters(project_id)
        
        elif method == 'get_all_characters':
            project_id = params.get('project_id')
            return self.db.get_all_characters(project_id)
        
        elif method == 'get_character_details':
            name = params.get('name')
            project_id = params.get('project_id')
            return self.db.get_character_details(name, project_id)
        
        elif method == 'save_character':
            data = params.get('data')
            result = self.db.save_character(data)
            # Trigger background summary update for characters
            project_id = data.get('project_id') if data else None
            if result and project_id:
                self._trigger_bg_summary(project_id=str(project_id), content_type='characters')
            return result
        
        elif method == 'delete_character':
            character_id = params.get('character_id')
            return self.db.delete_character(character_id)
        
        # ==================== STORY BIBLE METHODS ====================
        elif method == 'get_story_bible':
            project_id = params.get('project_id')
            return self.db.get_story_bible(project_id)
        
        elif method == 'save_bible_field':
            project_id = params.get('project_id')
            field_name = params.get('field_name')
            content = params.get('content')
            self.db.save_bible_field(project_id, field_name, content)
            # Trigger background summary update for all summarizable bible fields
            summarizable_fields = ('synopsis', 'outline', 'worldbuilding', 'braindump', 'style', 'genre')
            if project_id and field_name in summarizable_fields:
                # Map bible field names to content_type names used in summarization
                content_type_map = {
                    'synopsis': 'synopsis',
                    'outline': 'outline',
                    'worldbuilding': 'world_elements',  # worldbuilding shares world_elements summary type
                    'braindump': 'synopsis',  # braindump contributes to synopsis context
                    'style': 'synopsis',
                    'genre': 'synopsis',
                }
                ctype = content_type_map.get(field_name, field_name)
                self._trigger_bg_summary(project_id=str(project_id), content_type=ctype)
            return True
        
        elif method == 'get_bible_field':
            project_id = params.get('project_id')
            field_name = params.get('field_name')
            return self.db.get_bible_field(project_id, field_name)
        
        # ==================== APP STATE METHODS ====================
        elif method == 'save_app_state':
            key = params.get('key')
            value = params.get('value')
            self.db.save_app_state(key, value)
            return True
        
        elif method == 'get_app_state':
            key = params.get('key')
            return self.db.get_app_state(key)
        
        # ==================== CONTEXT METHODS ====================
        elif method == 'get_context_window':
            project_id = params.get('project_id')
            chapter_id = params.get('chapter_id')
            char_limit = params.get('char_limit', 3000)
            return self.db.get_context_window(project_id, chapter_id, char_limit)
        
        elif method == 'get_deep_memory':
            project_id = params.get('project_id')
            query = params.get('query')
            return self.db.get_deep_memory(project_id, query)
        
        elif method == 'get_summarized_memory':
            project_id = params.get('project_id')
            token_tier = params.get('token_tier', 1000)
            return self.db.get_summarized_memory(project_id, token_tier)
        
        elif method == 'get_context_health':
            project_id = params.get('project_id')
            return self.db.get_context_health(project_id)
        
        elif method == 'get_full_project_content':
            project_id = params.get('project_id')
            return self.db.get_full_project_content(project_id)
        
        # ==================== AI METHODS ====================
        elif method == 'get_ai_status':
            return {
                'status': self.ai.status_message,
                'is_loaded': self.ai.llm is not None,
                'context_size': self.ai.context_size
            }
        
        elif method == 'ai_stream_start':
            instruction = params.get('instruction')
            bible_data = params.get('bible_data')
            current_text = params.get('current_text', '')
            character_context = params.get('character_context')
            rag_context = params.get('rag_context')
            style = params.get('style')
            long_form = params.get('long_form', False)
            
            # Start AI generation in background thread
            self.ai_response_queue = queue.Queue()
            
            def _safe_ai_stream(q):
                try:
                    self.ai.stream_response(instruction, q, bible_data, current_text,
                          character_context, rag_context, style, long_form)
                except Exception as e:
                    logging.error(f"AI stream thread error: {e}")
                    q.put(f"\n[AI Error: {str(e)}]")
                    q.put("[[END]]")
            
            self.ai_thread = threading.Thread(
                target=_safe_ai_stream,
                args=(self.ai_response_queue,),
                daemon=True
            )
            self.ai_thread.start()
            return {'status': 'started'}
        
        elif method == 'ai_stream_poll':
            # Poll for AI tokens
            tokens = []
            is_done = False
            try:
                while True:
                    token = self.ai_response_queue.get_nowait()
                    if token == '[[END]]':
                        is_done = True
                        break
                    tokens.append(token)
            except queue.Empty:
                pass
            return {'tokens': tokens, 'done': is_done}
        
        elif method == 'ai_stream_stop':
            # Stop AI generation: drain the queue and signal completion
            try:
                while not self.ai_response_queue.empty():
                    try:
                        self.ai_response_queue.get_nowait()
                    except queue.Empty:
                        break
                self.ai_response_queue.put('[[END]]')
            except Exception as e:
                logging.error(f"ai_stream_stop error: {e}")
            return {'status': 'stopped'}
        
        elif method == 'generate_summary':
            text = params.get('text')
            mode = params.get('mode', 'incremental')
            return self.ai.generate_summary(text, mode)
        
        elif method == 'generate_beat_summary':
            text = params.get('text')
            return self.ai.generate_beat_summary(text)
        
        elif method == 'expand_scene':
            context_text = params.get('context_text')
            response_queue = queue.Queue()
            self.ai.expand_scene(context_text, response_queue)
            
            # Collect all tokens
            result = []
            while True:
                token = response_queue.get()
                if token == '[[END]]':
                    break
                result.append(token)
            return ''.join(result)
        
        elif method == 'generate_plugin_response':
            text = params.get('text')
            plugin_type = params.get('plugin_type')
            context_data = params.get('context_data')
            
            response_queue = queue.Queue()
            self.ai.generate_plugin_response(text, plugin_type, response_queue, context_data)
            
            # Collect all tokens
            result = []
            while True:
                token = response_queue.get()
                if token == '[[END]]':
                    break
                result.append(token)
            return ''.join(result)
        
        elif method == 'ask_lore_assistant':
            query = params.get('query')
            project_memory = params.get('project_memory')
            project_name = params.get('project_name', 'Current Project')
            structured_context = params.get('structured_context')
            
            response_queue = queue.Queue()
            self.ai.ask_lore_assistant(query, response_queue, project_memory, project_name, structured_context)
            
            # Collect all tokens
            result = []
            while True:
                token = response_queue.get()
                if token == '[[END]]':
                    break
                result.append(token)
            return ''.join(result)
        
        elif method == 'lore_stream_start':
            query = params.get('query')
            project_memory = params.get('project_memory', '')
            project_name = params.get('project_name', 'Current Project')
            structured_context = params.get('structured_context')
            
            logging.info(f"lore_stream_start: query length={len(query or '')}, memory length={len(project_memory or '')}, structured={structured_context is not None}")
            
            # Use the shared response queue for streaming (same as ai_stream_start)
            self.ai_response_queue = queue.Queue()
            
            # Wrap in safety function to guarantee [[END]] is always sent
            def _safe_lore_stream(q, qry, mem, name, struct_ctx):
                try:
                    logging.info("Lore stream thread: starting ask_lore_assistant...")
                    self.ai.ask_lore_assistant(qry, q, mem, name, struct_ctx)
                    logging.info(f"Lore stream thread: finished. Queue size ~{q.qsize()}")
                except Exception as e:
                    logging.error(f"Lore stream thread error: {e}", exc_info=True)
                    q.put(f"\n[AI Error: {str(e)}]")
                    q.put("[[END]]")
            
            self.ai_thread = threading.Thread(
                target=_safe_lore_stream,
                args=(self.ai_response_queue, query, project_memory, project_name, structured_context),
                daemon=True
            )
            self.ai_thread.start()
            return {'status': 'started'}
        
        elif method == 'get_genre_context':
            genre = params.get('genre')
            return self.ai.get_genre_context(genre)
        
        elif method == 'generate_beats_from_prose':
            prose_text = params.get('prose_text')
            return self.ai.generate_beats_from_prose(prose_text)
        
        elif method == 'suggest_next_beats':
            prev_beats = params.get('prev_beats')
            lore_package = params.get('lore_package')
            return self.ai.suggest_next_beats(prev_beats, lore_package)
        
        elif method == 'check_continuity':
            beats = params.get('beats')
            lore_package = params.get('lore_package')
            result = self.ai.check_continuity(beats, lore_package)
            return {'valid': result[0], 'message': result[1]}
        
        # ==================== TTS METHODS ====================
        elif method == 'tts_list_voices':
            return self.tts.list_available_voices()
        
        elif method == 'tts_read_text':
            text = params.get('text')
            voice = params.get('voice', 'Jenny (US Female)')
            character_name = params.get('character_name')
            self.tts.tts_read_text(text, voice, character_name)
            return {'status': 'playing'}
        
        elif method == 'tts_stop':
            self.tts.stop()
            return {'status': 'stopped'}
        
        elif method == 'tts_generate_mp3':
            text = params.get('text')
            voice = params.get('voice')
            output_path = params.get('output_path')
            
            # Reset progress
            with self._tts_download_lock:
                self._tts_download_progress = 0
            
            # Progress callback to update shared state (thread-safe)
            def progress_callback(progress):
                try:
                    with self._tts_download_lock:
                        self._tts_download_progress = progress
                        logging.debug(f"TTS progress: {progress}%")
                except Exception as e:
                    logging.error(f"Progress callback error: {e}")
            
            # Run TTS generation
            result = self.tts.tts_generate_mp3(text, voice, output_path, progress_callback)
            
            # Reset progress when done
            with self._tts_download_lock:
                self._tts_download_progress = 0
            
            return result
        
        elif method == 'tts_get_download_progress':
            try:
                with self._tts_download_lock:
                    progress = self._tts_download_progress
                return {'progress': progress}
            except Exception as e:
                logging.error(f"Error getting download progress: {e}")
                return {'progress': 0}
        
        elif method == 'tts_is_playing':
            return {'is_playing': self.tts.is_playing}
        
        # ==================== TTS MODE METHODS ====================
        elif method == 'tts_get_mode':
            return {'mode': get_tts_mode()}
        
        elif method == 'tts_set_mode':
            mode = params.get('mode', 'cloud')
            result = set_tts_mode(mode)
            # Update self.tts to use the new engine
            self.tts = get_tts_engine()
            return result
        
        elif method == 'tts_get_availability':
            return get_tts_availability()
        
        elif method == 'tts_list_local_voices':
            return {'voices': list_local_voices()}
        
        elif method == 'tts_download_local_voice':
            voice_name = params.get('voice_name')
            if not voice_name:
                return {'success': False, 'error': 'No voice name provided'}
            
            # Reset progress
            def progress_callback(progress):
                pass  # Progress tracked internally by get_piper_download_progress
            
            success = download_local_voice(voice_name, progress_callback)
            return {'success': success}
        
        elif method == 'tts_get_local_download_progress':
            return {'progress': get_piper_download_progress()}
        
        elif method == 'tts_delete_local_voice':
            voice_name = params.get('voice_name')
            if not voice_name:
                return {'success': False, 'error': 'No voice name provided'}
            success = delete_local_voice(voice_name)
            return {'success': success}
        
        # ==================== CONFIG METHODS ====================
        elif method == 'get_ai_config':
            config = self.config.get_ai_config()
            return {
                'model_path': config.model_path,
                'n_gpu_layers': config.n_gpu_layers,
                'n_ctx': config.n_ctx,
                'n_batch': config.n_batch,
                'temperature': config.temperature
            }
        
        elif method == 'validate_model_path':
            valid, message = self.config.validate_model_path()
            return {'valid': valid, 'message': message}
        
        elif method == 'list_models':
            return {'models': self.config.list_available_models()}
        
        elif method == 'select_model':
            model_path = params.get('model_path')
            if not model_path:
                return {'status': 'Error: No model path provided', 'is_loaded': False}
            # Block any background summarization from starting during model switch
            self._summary_running = True
            try:
                result = self.ai.reload_model(model_path)
            finally:
                self._summary_running = False
            return result
        
        elif method == 'copy_model_to_directory':
            source_path = params.get('source_path')
            if not source_path:
                return {'success': False, 'error': 'No source path provided'}
            
            import shutil
            try:
                # Validate source file exists and is a .gguf file
                if not os.path.exists(source_path):
                    return {'success': False, 'error': f'Source file not found: {source_path}'}
                
                if not source_path.lower().endswith('.gguf'):
                    return {'success': False, 'error': 'File must be a .gguf model'}
                
                # Get destination path in models/llama directory
                filename = os.path.basename(source_path)
                dest_path = os.path.join(self.config.models_dir, filename)
                
                # Check if file already exists in destination
                if os.path.exists(dest_path):
                    # File already exists, just use it
                    logging.info(f"Model already exists at {dest_path}, skipping copy")
                    return {
                        'success': True, 
                        'destination_path': dest_path,
                        'message': f'Model already exists: {filename}'
                    }
                
                # Copy the file
                logging.info(f"Copying model from {source_path} to {dest_path}")
                shutil.copy2(source_path, dest_path)
                logging.info(f"Model copied successfully to {dest_path}")
                
                return {
                    'success': True, 
                    'destination_path': dest_path,
                    'message': f'Model copied successfully: {filename}'
                }
                
            except Exception as e:
                logging.error(f"Failed to copy model: {e}", exc_info=True)
                return {'success': False, 'error': str(e)}
        
        # ==================== WORLD ELEMENTS METHODS ====================
        elif method == 'create_world_element':
            project_id = params.get('project_id')
            result = self.db.create_world_element(
                project_id=project_id,
                name=params.get('name'),
                element_type=params.get('element_type', 'other'),
                description=params.get('description', ''),
                sensory_details=params.get('sensory_details', ''),
                significance=params.get('significance', ''),
                custom_traits=params.get('custom_traits', ''),
                series_id=params.get('series_id')
            )
            # Trigger background summary update for world_elements
            if result and project_id:
                self._trigger_bg_summary(project_id=str(project_id), content_type='world_elements')
            return result
        
        elif method == 'get_world_elements':
            return self.db.get_world_elements(
                project_id=params.get('project_id'),
                series_id=params.get('series_id'),
                element_type=params.get('element_type')
            )
        
        elif method == 'get_world_element':
            return self.db.get_world_element(params.get('element_id'))
        
        elif method == 'update_world_element':
            element_id = params.get('element_id')
            result = self.db.update_world_element(element_id, params.get('data', {}))
            # Trigger background summary update (need to look up project_id from element)
            if result and element_id:
                self._trigger_bg_summary(element_id=element_id, content_type='world_elements')
            return result
        
        elif method == 'delete_world_element':
            return self.db.delete_world_element(params.get('element_id'))
        
        # ==================== SERIES METHODS ====================
        elif method == 'create_series':
            return self.db.create_series(
                name=params.get('name'),
                description=params.get('description', '')
            )
        
        elif method == 'get_series_list':
            return self.db.get_series_list()
        
        elif method == 'get_series':
            return self.db.get_series(params.get('series_id'))
        
        elif method == 'update_series':
            return self.db.update_series(
                series_id=params.get('series_id'),
                name=params.get('name'),
                description=params.get('description'),
                timeline_data=params.get('timeline_data')
            )
        
        elif method == 'delete_series':
            return self.db.delete_series(params.get('series_id'))
        
        elif method == 'add_project_to_series':
            return self.db.add_project_to_series(
                series_id=params.get('series_id'),
                project_id=params.get('project_id'),
                book_order=params.get('book_order')
            )
        
        elif method == 'remove_project_from_series':
            return self.db.remove_project_from_series(
                series_id=params.get('series_id'),
                project_id=params.get('project_id')
            )
        
        elif method == 'get_series_bible':
            return self.db.get_series_bible(params.get('series_id'))
        
        elif method == 'get_series_characters':
            return self.db.get_series_characters(params.get('series_id'))
        
        elif method == 'get_series_world_elements':
            return self.db.get_series_world_elements(params.get('series_id'))
        
        elif method == 'get_series_timeline':
            return self.db.get_series_timeline(params.get('series_id'))
        
        elif method == 'update_series_timeline':
            return self.db.update_series_timeline(
                series_id=params.get('series_id'),
                timeline_data=params.get('timeline_data', [])
            )
        
        # ==================== SCENE METHODS ====================
        elif method == 'create_scene':
            return self.db.create_scene(
                chapter_id=params.get('chapter_id'),
                title=params.get('title', ''),
                summary=params.get('summary', ''),
                pov_character=params.get('pov_character', ''),
                location=params.get('location', '')
            )
        
        elif method == 'get_scenes':
            return self.db.get_scenes(params.get('chapter_id'))
        
        elif method == 'update_scene':
            return self.db.update_scene(
                scene_id=params.get('scene_id'),
                data=params.get('data', {})
            )
        
        elif method == 'delete_scene':
            return self.db.delete_scene(params.get('scene_id'))
        
        elif method == 'reorder_scenes':
            return self.db.reorder_scenes(
                chapter_id=params.get('chapter_id'),
                scene_ids=params.get('scene_ids', [])
            )
        
        elif method == 'get_scene_context':
            return self.db.get_scene_context(params.get('chapter_id'))
        
        elif method == 'get_project_series_id':
            return self.db.get_project_series_id(params.get('project_id'))
        
        elif method == 'get_series_context_for_project':
            return self.db.get_series_context_for_project(params.get('project_id'))
        
        # ==================== CHARACTER VERSION METHODS ====================
        elif method == 'create_character_version':
            return self.db.create_character_version(
                character_id=params.get('character_id'),
                project_id=params.get('project_id'),
                version_notes=params.get('version_notes', ''),
                trait_overrides=params.get('trait_overrides', '')
            )
        
        elif method == 'get_character_versions':
            return self.db.get_character_versions(params.get('character_id'))
        
        elif method == 'set_canonical_version':
            return self.db.set_canonical_version(
                version_id=params.get('version_id'),
                character_id=params.get('character_id')
            )
        
        elif method == 'delete_character_version':
            return self.db.delete_character_version(params.get('version_id'))
        
        # ==================== CHAPTER OUTLINE LINKING METHODS ====================
        elif method == 'link_chapter_to_outline':
            return self.db.link_chapter_to_outline(
                chapter_id=params.get('chapter_id'),
                outline_section=params.get('outline_section'),
                outline_order=params.get('outline_order', 0)
            )
        
        elif method == 'get_chapter_outline_links':
            return self.db.get_chapter_outline_links(params.get('project_id'))
        
        elif method == 'unlink_chapter_from_outline':
            return self.db.unlink_chapter_from_outline(params.get('chapter_id'))
        
        elif method == 'get_chapter_summary':
            return self.db.get_chapter_summary(params.get('chapter_id'))
        
        elif method == 'save_chapter_summary':
            return self.db.save_chapter_summary(
                chapter_id=params.get('chapter_id'),
                summary=params.get('summary'),
                recent_summary=params.get('recent_summary')
            )
        
        # ==================== CSV IMPORT/EXPORT METHODS ====================
        elif method == 'export_characters_csv':
            return self.db.export_characters_csv(params.get('project_id'))
        
        elif method == 'import_characters_csv':
            return self.db.import_characters_csv(
                project_id=params.get('project_id'),
                csv_data=params.get('csv_data')
            )
        
        elif method == 'export_world_elements_csv':
            return self.db.export_world_elements_csv(params.get('project_id'))
        
        elif method == 'import_world_elements_csv':
            return self.db.import_world_elements_csv(
                project_id=params.get('project_id'),
                csv_data=params.get('csv_data')
            )
        
        # ==================== IMPORT NOVEL METHODS ====================
        elif method == 'parse_manuscript':
            content = params.get('content')
            extract_all = params.get('extract_all', True)
            combined_mode = params.get('combined_mode', True)  # Default to combined mode for speed
            return self.import_parser.parse_manuscript(content, extract_all, combined_mode)
        
        elif method == 'detect_chapters':
            content = params.get('content')
            chapters = self.import_parser.detect_chapters(content)
            # Clean chapter titles
            for ch in chapters:
                ch['title'] = self.import_parser.clean_chapter_title(ch['title'])
            return chapters
        
        elif method == 'extract_synopsis':
            content = params.get('content')
            return self.import_parser.extract_synopsis(content)
        
        elif method == 'extract_characters':
            content = params.get('content')
            return self.import_parser.extract_characters(content)
        
        elif method == 'extract_world_elements':
            content = params.get('content')
            return self.import_parser.extract_world_elements(content)
        
        elif method == 'detect_genre_style':
            content = params.get('content')
            return self.import_parser.detect_genre_style(content)
        
        elif method == 'generate_characters_from_synopsis':
            synopsis = params.get('synopsis')
            genre = params.get('genre', 'fiction')
            return self.ai.generate_characters_from_synopsis(synopsis, genre)
        
        elif method == 'generate_single_character':
            description = params.get('description')
            genre = params.get('genre', 'fiction')
            return self.ai.generate_single_character(description, genre)
        
        elif method == 'generate_world_from_synopsis':
            synopsis = params.get('synopsis')
            genre = params.get('genre', 'fiction')
            return self.ai.generate_world_from_synopsis(synopsis, genre)
        
        elif method == 'generate_single_world_element':
            description = params.get('description')
            element_type = params.get('element_type', 'location')
            genre = params.get('genre', 'fiction')
            return self.ai.generate_single_world_element(description, element_type, genre)
        
        elif method == 'generate_synopsis':
            story_elements = params.get('story_elements')
            genre = params.get('genre', 'fiction')
            target_words = params.get('target_words', '300-500')
            return self.ai.generate_synopsis(story_elements, genre, target_words)
        
        elif method == 'generate_outline_from_synopsis':
            synopsis = params.get('synopsis', '')
            chapter_count = params.get('chapter_count', 10)
            genre = params.get('genre', 'fiction')
            characters = params.get('characters', '')
            worldbuilding = params.get('worldbuilding', '')
            braindump = params.get('braindump', '')
            return self.ai.generate_outline_from_synopsis(
                synopsis, chapter_count, genre, characters, worldbuilding, braindump
            )
        
        elif method == 'update_chapter_summary_ai':
            chapter_content = params.get('chapter_content')
            return self.ai.update_chapter_summary(chapter_content)
        
        elif method == 'generate_chapter_summary':
            chapter_number = params.get('chapter_number', 1)
            chapter_title = params.get('chapter_title', f'Chapter {chapter_number}')
            synopsis = params.get('synopsis', '')
            genre = params.get('genre', 'fiction')
            custom_instructions = params.get('custom_instructions', '')
            existing_outline = params.get('existing_outline', '')
            return self.ai.generate_chapter_summary(
                chapter_number, chapter_title, synopsis, genre,
                custom_instructions, existing_outline
            )
        
        elif method == 'expand_scene_from_summary':
            scene_summary = params.get('scene_summary')
            context = params.get('context', '')
            genre = params.get('genre', 'fiction')
            style = params.get('style', '')
            characters = params.get('characters', '')
            worldbuilding = params.get('worldbuilding', '')
            chapter_outline = params.get('chapter_outline', '')
            extra_instructions = params.get('extra_instructions', '')
            has_rich_context = any([style, characters, worldbuilding, chapter_outline, extra_instructions])
            if has_rich_context:
                return self.ai.expand_scene_with_context(
                    scene_summary, context, genre, style,
                    characters, worldbuilding, chapter_outline,
                    extra_instructions
                )
            return self.ai.expand_scene_from_summary(scene_summary, context, genre)
        
        elif method == 'generate_bible_section':
            section_key = params.get('section_key')
            project_id = self._validate_string(params.get('project_id'), 'project_id', required=True)
            return self.ai.generate_bible_section(section_key, project_id, self.db)
        
        elif method == 'import_manuscript_to_project':
            # Full import flow: create project, add chapters, extract story bible
            content = params.get('content')
            project_name = params.get('project_name', 'Imported Novel')
            extract_all = params.get('extract_all', True)
            combined_mode = params.get('combined_mode', True)  # Default to combined mode for speed
            
            # Parse manuscript with combined mode option
            parsed = self.import_parser.parse_manuscript(content, extract_all, combined_mode)
            
            # Create project
            project_id = self.db.create_project(project_name, parsed.get('genre_style', ''))
            
            if not project_id:
                return {'error': 'Failed to create project'}
            
            # Add chapters
            for chapter in parsed.get('chapters', []):
                self.db.create_chapter(project_id, chapter['title'], chapter['content'])
            
            # Save story bible data
            if parsed.get('synopsis'):
                self.db.save_bible_field(project_id, 'synopsis', parsed['synopsis'])
            if parsed.get('genre_style'):
                self.db.save_bible_field(project_id, 'genre', parsed['genre_style'])
            
            # Save characters
            for char in parsed.get('characters', []):
                char['project_id'] = project_id
                self.db.save_character(char)
            
            # Save world elements
            for elem in parsed.get('world_elements', []):
                self.db.create_world_element(
                    project_id=project_id,
                    name=elem.get('name', ''),
                    element_type=elem.get('element_type', 'other'),
                    description=elem.get('description', ''),
                    sensory_details=elem.get('sensory_details', ''),
                    significance=elem.get('significance', '')
                )
            
            return {
                'project_id': project_id,
                'chapters_imported': len(parsed.get('chapters', [])),
                'characters_imported': len(parsed.get('characters', [])),
                'world_elements_imported': len(parsed.get('world_elements', [])),
                'word_count': parsed.get('word_count', 0)
            }
        
        # ==================== UNKNOWN METHOD ====================
        else:
            raise ValueError(f"Unknown method: {method}")
    
    # Methods that involve AI model inference and can block for minutes.
    # These are dispatched to a thread pool so the main loop stays responsive.
    _LONG_RUNNING_METHODS = frozenset({
        'generate_outline_from_synopsis',
        'generate_chapter_summary',
        'generate_characters_from_synopsis',
        'generate_single_character',
        'generate_world_from_synopsis',
        'generate_single_world_element',
        'generate_synopsis',
        'generate_bible_section',
        'generate_beat_summary',
        'generate_beats_from_prose',
        'suggest_next_beats',
        'check_continuity',
        'generate_plugin_response',
        'expand_scene',
        'expand_scene_from_summary',
        'update_chapter_summary_ai',
        'ask_lore_assistant',
        'generate_summary',
        'parse_manuscript',
        'extract_synopsis',
        'extract_characters',
        'extract_world_elements',
        'detect_genre_style',
        'import_manuscript_to_project',
    })

    def run(self):
        """
        Main loop - reads JSON-RPC requests from stdin, writes responses to stdout.
        Long-running AI operations are dispatched to a thread pool so that quick
        operations (list_models, get_characters, etc.) aren't blocked.
        """
        from concurrent.futures import ThreadPoolExecutor
        
        logging.info("API Bridge running, waiting for requests...")
        
        # Lock to prevent interleaved writes to stdout
        self._stdout_lock = threading.Lock()
        
        # Thread pool for long-running operations (max 2: 1 AI + 1 import/parse)
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='api-worker')
        
        # Send ready signal
        self._send_response({'jsonrpc': '2.0', 'result': 'ready', 'id': 'init'})
        
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                method = request.get('method', '')
                
                # Dispatch long-running AI operations to thread pool
                if method in self._LONG_RUNNING_METHODS:
                    self._executor.submit(self._handle_and_respond, request)
                else:
                    # Handle quick operations synchronously to avoid thread overhead
                    response = self.handle_request(request)
                    self._send_response(response)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON: {e}")
                self._send_response({
                    'jsonrpc': '2.0',
                    'error': {'code': -32700, 'message': 'Parse error'},
                    'id': None
                })
    
    def _handle_and_respond(self, request: Dict):
        """Handle a request in a worker thread and send the response."""
        try:
            response = self.handle_request(request)
            self._send_response(response)
        except Exception as e:
            logging.error(f"Worker thread error: {e}")
            self._send_response({
                'jsonrpc': '2.0',
                'error': {'code': -32000, 'message': str(e)},
                'id': request.get('id')
            })
    
    def _send_response(self, response: Dict):
        """Send JSON response to stdout (thread-safe)."""
        line = json.dumps(response)
        if hasattr(self, '_stdout_lock'):
            with self._stdout_lock:
                print(line, flush=True)
        else:
            print(line, flush=True)


def main():
    """Entry point for the API bridge."""
    try:
        bridge = APIBridge()
        bridge.run()
    except KeyboardInterrupt:
        logging.info("API Bridge shutting down...")
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
        logging.critical(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()

