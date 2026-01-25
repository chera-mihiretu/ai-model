"""
Python JSON-RPC API Bridge for Story Bible Pro
===============================================
Exposes all backend services via stdin/stdout JSON-RPC protocol.
This allows Electron to communicate with Python services.
"""

import sys
import json
import queue
import logging
import threading
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.db_manager import DatabaseManager
from src.services.ai_engine import AIEngine
from src.services.tts_engine import get_engine as get_tts_engine
from src.config.manager import ConfigManager
from src.domain.usecases.import_parser import ImportParser

# Configure logging
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
        
        logging.info("API Bridge initialized successfully")
    
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
            name = params.get('name', 'New Project')
            genre = params.get('genre', '')
            return self.db.create_project(name, genre)
        
        elif method == 'delete_project':
            project_id = params.get('project_id')
            return self.db.delete_project(project_id)
        
        elif method == 'rename_project':
            project_id = params.get('project_id')
            new_name = params.get('new_name')
            return self.db.rename_project(project_id, new_name)
        
        elif method == 'get_project_settings':
            project_id = params.get('project_id')
            return self.db.get_project_settings(project_id)
        
        # ==================== CHAPTER METHODS ====================
        elif method == 'create_chapter':
            project_id = params.get('project_id')
            title = params.get('title', 'New Chapter')
            content = params.get('content', '')
            return self.db.create_chapter(project_id, title, content)
        
        elif method == 'get_chapters':
            project_id = params.get('project_id')
            return self.db.get_chapters(project_id)
        
        elif method == 'get_chapter_content':
            chapter_id = params.get('chapter_id')
            return self.db.get_chapter_content(chapter_id)
        
        elif method == 'update_chapter_content':
            chapter_id = params.get('chapter_id')
            content = params.get('content')
            return self.db.update_chapter_content(chapter_id, content)
        
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
            return self.db.save_character(data)
        
        # ==================== STORY BIBLE METHODS ====================
        elif method == 'get_story_bible':
            project_id = params.get('project_id')
            return self.db.get_story_bible(project_id)
        
        elif method == 'save_bible_field':
            project_id = params.get('project_id')
            field_name = params.get('field_name')
            content = params.get('content')
            self.db.save_bible_field(project_id, field_name, content)
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
        
        elif method == 'get_full_project_content':
            project_id = params.get('project_id')
            return self.db.get_full_project_content(project_id)
        
        # ==================== AI METHODS ====================
        elif method == 'get_ai_status':
            return {
                'status': self.ai.status_message,
                'is_loaded': self.ai.llm is not None
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
            self.ai_thread = threading.Thread(
                target=self.ai.stream_response,
                args=(instruction, self.ai_response_queue, bible_data, current_text,
                      character_context, rag_context, style, long_form),
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
            
            response_queue = queue.Queue()
            self.ai.ask_lore_assistant(query, response_queue, project_memory, project_name)
            
            # Collect all tokens
            result = []
            while True:
                token = response_queue.get()
                if token == '[[END]]':
                    break
                result.append(token)
            return ''.join(result)
        
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
            return self.tts.tts_generate_mp3(text, voice, output_path)
        
        elif method == 'tts_is_playing':
            return {'is_playing': self.tts.is_playing}
        
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
        
        # ==================== WORLD ELEMENTS METHODS ====================
        elif method == 'create_world_element':
            return self.db.create_world_element(
                project_id=params.get('project_id'),
                name=params.get('name'),
                element_type=params.get('element_type', 'other'),
                description=params.get('description', ''),
                sensory_details=params.get('sensory_details', ''),
                significance=params.get('significance', ''),
                custom_traits=params.get('custom_traits', ''),
                series_id=params.get('series_id')
            )
        
        elif method == 'get_world_elements':
            return self.db.get_world_elements(
                project_id=params.get('project_id'),
                series_id=params.get('series_id'),
                element_type=params.get('element_type')
            )
        
        elif method == 'get_world_element':
            return self.db.get_world_element(params.get('element_id'))
        
        elif method == 'update_world_element':
            return self.db.update_world_element(
                params.get('element_id'),
                params.get('data', {})
            )
        
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
            return self.import_parser.parse_manuscript(content, extract_all)
        
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
            synopsis = params.get('synopsis')
            chapter_count = params.get('chapter_count', 10)
            genre = params.get('genre', 'fiction')
            return self.ai.generate_outline_from_synopsis(synopsis, chapter_count, genre)
        
        elif method == 'update_chapter_summary_ai':
            chapter_content = params.get('chapter_content')
            return self.ai.update_chapter_summary(chapter_content)
        
        elif method == 'expand_scene_from_summary':
            scene_summary = params.get('scene_summary')
            context = params.get('context', '')
            genre = params.get('genre', 'fiction')
            return self.ai.expand_scene_from_summary(scene_summary, context, genre)
        
        elif method == 'import_manuscript_to_project':
            # Full import flow: create project, add chapters, extract story bible
            content = params.get('content')
            project_name = params.get('project_name', 'Imported Novel')
            extract_all = params.get('extract_all', True)
            
            # Parse manuscript
            parsed = self.import_parser.parse_manuscript(content, extract_all)
            
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
                'world_elements_imported': len(parsed.get('world_elements', []))
            }
        
        # ==================== UNKNOWN METHOD ====================
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def run(self):
        """
        Main loop - reads JSON-RPC requests from stdin, writes responses to stdout.
        """
        logging.info("API Bridge running, waiting for requests...")
        
        # Send ready signal
        self._send_response({'jsonrpc': '2.0', 'result': 'ready', 'id': 'init'})
        
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                self._send_response(response)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON: {e}")
                self._send_response({
                    'jsonrpc': '2.0',
                    'error': {'code': -32700, 'message': 'Parse error'},
                    'id': None
                })
    
    def _send_response(self, response: Dict):
        """Send JSON response to stdout."""
        print(json.dumps(response), flush=True)


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

