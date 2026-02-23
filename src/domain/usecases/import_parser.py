"""
Import Parser - Detects chapters in imported documents and extracts story elements using AI
"""
import re
import json
import logging
from typing import List, Dict, Optional, Any


# AI Prompts for extraction
PROMPT_EXTRACT_SYNOPSIS = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a literary analyst. Given a manuscript excerpt, create a comprehensive synopsis.
<|eot_id|><|start_header_id|>user<|end_header_id|>
Analyze this manuscript and write a detailed synopsis covering:
- Main plot and story arc
- Key themes
- Beginning, middle, and end structure
- Central conflict

MANUSCRIPT (excerpt):
{text}

Write a 2-3 paragraph synopsis:
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

PROMPT_EXTRACT_CHARACTERS = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a literary analyst specializing in character analysis. Extract character profiles from manuscripts.
Output ONLY valid JSON.
<|eot_id|><|start_header_id|>user<|end_header_id|>
Analyze this manuscript and identify ALL named characters. For each character, provide:
- name: Full name
- role: (protagonist, antagonist, supporting, minor)
- personality_traits: Key personality characteristics
- physical_description: Physical appearance if mentioned
- backstory: Background information if provided
- speech_pattern: How they talk (formal, casual, accent, etc.)
- motivations: What drives them

CRITICAL: You MUST return at least 3-5 main characters. If fewer are explicitly named, include supporting characters who appear in the text.

MANUSCRIPT (excerpt):
{text}

Return a JSON array of character objects:
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
["""

PROMPT_EXTRACT_WORLD = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a literary analyst specializing in worldbuilding. Extract world elements from manuscripts.
Output ONLY valid JSON.
<|eot_id|><|start_header_id|>user<|end_header_id|>
Analyze this manuscript and identify key worldbuilding elements:
- Settings/Locations: Places where the story takes place
- Events: Significant historical or plot events
- Systems: Magic systems, political systems, social structures
- Items: Important objects or artifacts

For each element provide:
- name: Element name
- element_type: (setting, location, event, system, item)
- description: What it is
- sensory_details: Visual, auditory, or other sensory descriptions
- significance: Why it matters to the story

CRITICAL: You MUST return at least 2-3 world elements. Include the primary setting at minimum.

MANUSCRIPT (excerpt):
{text}

Return a JSON array of world element objects:
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
["""

PROMPT_DETECT_GENRE = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a literary genre expert. Identify the genre and style of manuscripts.
<|eot_id|><|start_header_id|>user<|end_header_id|>
Analyze this manuscript excerpt and identify:
1. Primary genre (fantasy, sci-fi, romance, mystery, thriller, literary fiction, etc.)
2. Subgenres if applicable
3. Writing style characteristics (POV, tense, narrative voice)
4. Tone (dark, lighthearted, comedic, serious, etc.)

MANUSCRIPT (excerpt):
{text}

Provide your analysis in 2-3 sentences:
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

PROMPT_EXTRACT_COMBINED = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a literary analyst extracting story elements from manuscripts.
Output ONLY valid JSON in the exact format specified.
<|eot_id|><|start_header_id|>user<|end_header_id|>
Analyze this manuscript and extract TWO types of story elements:

1. CHARACTERS - Identify ALL named characters with complete profiles:
   - name: Full character name
   - role: One of (protagonist, antagonist, supporting, minor)
   - personality_traits: Key personality characteristics
   - physical_description: Physical appearance if mentioned
   - backstory: Background information if provided
   - speech_pattern: How they talk (formal, casual, accent, etc.)
   - motivations: What drives them

2. WORLD ELEMENTS - Identify key worldbuilding elements:
   - name: Element name
   - element_type: One of (setting, location, event, system, item)
   - description: What it is
   - sensory_details: Visual, auditory, or other sensory descriptions
   - significance: Why it matters to the story

CRITICAL REQUIREMENTS:
- Extract at least 3-5 characters (include supporting characters if needed)
- Extract at least 2-3 world elements (include primary setting at minimum)
- Do NOT omit any named characters or important locations
- Return complete, valid JSON

MANUSCRIPT (excerpt):
{text}

Return JSON in this EXACT format:
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
{{
  "characters": ["""


class ImportParser:
    """Parse imported documents and detect chapter structure with AI extraction."""
    
    # Common chapter heading patterns
    CHAPTER_PATTERNS = [
        r'^#\s+Chapter\s+\d+',              # Markdown: # Chapter 1
        r'^##\s+Chapter\s+\d+',             # Markdown: ## Chapter 1
        r'^Chapter\s+\d+',                  # Plain: Chapter 1
        r'^CHAPTER\s+\d+',                  # Plain: CHAPTER 1
        r'^Ch\.\s+\d+',                     # Abbreviated: Ch. 1
        r'^Ch\s+\d+',                       # Abbreviated: Ch 1
        r'^\d+\.\s+[A-Z]',                  # Numbered: 1. Title
        r'^Part\s+\d+',                     # Part 1
        r'^PART\s+\d+',                     # PART 1
        r'^Prologue',                       # Prologue
        r'^PROLOGUE',                       # PROLOGUE
        r'^Epilogue',                       # Epilogue
        r'^EPILOGUE',                       # EPILOGUE
    ]
    
    def __init__(self, ai_engine=None):
        """Initialize with optional AI engine for extraction."""
        self.ai = ai_engine
    
    def set_ai_engine(self, ai_engine):
        """Set the AI engine for extraction."""
        self.ai = ai_engine
    
    @staticmethod
    def detect_chapters(content: str) -> List[Dict[str, str]]:
        """
        Detect chapters in document content.
        
        Returns:
            List of dicts with 'title' and 'content' keys
        """
        lines = content.split('\n')
        chapters = []
        current_chapter = None
        current_content = []
        
        for line in lines:
            # Check if line matches any chapter pattern
            is_chapter = False
            for pattern in ImportParser.CHAPTER_PATTERNS:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    is_chapter = True
                    break
            
            if is_chapter:
                # Save previous chapter if exists
                if current_chapter:
                    chapters.append({
                        'title': current_chapter,
                        'content': '\n'.join(current_content).strip()
                    })
                
                # Start new chapter
                current_chapter = line.strip()
                current_content = []
            else:
                # Add to current chapter content
                if current_chapter:
                    current_content.append(line)
        
        # Add final chapter
        if current_chapter:
            chapters.append({
                'title': current_chapter,
                'content': '\n'.join(current_content).strip()
            })
        
        # If no chapters detected, treat entire content as single chapter
        if not chapters:
            chapters.append({
                'title': 'Chapter 1',
                'content': content.strip()
            })
        
        return chapters
    
    @staticmethod
    def clean_chapter_title(title: str) -> str:
        """Clean up chapter title for display."""
        # Remove markdown headers
        title = re.sub(r'^#+\s*', '', title)
        # Remove extra whitespace
        title = ' '.join(title.split())
        # Capitalize properly if all caps
        if title.isupper() and len(title) > 10:
            title = title.title()
        return title or "Untitled Chapter"
    
    def _get_representative_text(self, content: str, max_chars: int = 8000) -> str:
        """Extract representative text for AI analysis."""
        if len(content) <= max_chars:
            return content
        
        # Take beginning, middle, and end samples
        third = max_chars // 3
        beginning = content[:third]
        middle_start = (len(content) - third) // 2
        middle = content[middle_start:middle_start + third]
        end = content[-third:]
        
        return f"{beginning}\n\n[...]\n\n{middle}\n\n[...]\n\n{end}"
    
    def extract_synopsis(self, content: str) -> str:
        """Use AI to generate a synopsis from manuscript content."""
        import time
        
        if not self.ai or not self.ai.llm:
            logging.warning("AI engine not available for synopsis extraction")
            return ""
        
        try:
            text = self._get_representative_text(content)
            logging.info(f"Starting synopsis extraction for {len(content)} characters of text")
            logging.info(f"Representative text sample: {len(text)} chars")
            
            prompt = PROMPT_EXTRACT_SYNOPSIS.format(text=text)
            
            start_time = time.time()
            response = self.ai.llm(prompt, max_tokens=500, stop=["<|eot_id|>"])
            elapsed = time.time() - start_time
            
            synopsis = response['choices'][0]['text'].strip()
            logging.info(f"Synopsis extraction completed in {elapsed:.2f}s")
            logging.info(f"Synopsis length: {len(synopsis)} chars, preview: {synopsis[:100]}...")
            
            return synopsis
        except Exception as e:
            logging.error(f"Synopsis extraction failed: {e}")
            return ""
    
    def extract_characters(self, content: str) -> List[Dict[str, Any]]:
        """Use AI to extract character profiles from manuscript content."""
        import time
        
        if not self.ai or not self.ai.llm:
            logging.warning("AI engine not available for character extraction")
            return []
        
        try:
            text = self._get_representative_text(content)
            logging.info(f"Starting character extraction for {len(content)} characters of text")
            logging.info(f"Representative text sample: {len(text)} chars")
            
            prompt = PROMPT_EXTRACT_CHARACTERS.format(text=text)
            
            start_time = time.time()
            response = self.ai.llm(prompt, max_tokens=2000, stop=["<|eot_id|>"])
            elapsed = time.time() - start_time
            
            raw_response = response['choices'][0]['text'].strip()
            logging.info(f"Character extraction completed in {elapsed:.2f}s")
            logging.info(f"Raw AI response length: {len(raw_response)} chars")
            
            json_str = "[" + raw_response
            
            # Clean up JSON
            if not json_str.endswith("]"):
                # Find last complete object
                last_bracket = json_str.rfind("}")
                if last_bracket > 0:
                    json_str = json_str[:last_bracket + 1] + "]"
            
            characters = json.loads(json_str)
            
            # Validate and clean character data
            cleaned = []
            for char in characters:
                if isinstance(char, dict) and char.get('name'):
                    cleaned.append({
                        'name': char.get('name', ''),
                        'role': char.get('role', 'supporting'),
                        'personality_traits': char.get('personality_traits', ''),
                        'physical_description': char.get('physical_description', ''),
                        'backstory': char.get('backstory', ''),
                        'speech_pattern': char.get('speech_pattern', ''),
                        'motivations': char.get('motivations', ''),
                        'is_visible': 1
                    })
            
            logging.info(f"Parsed {len(cleaned)} characters: {[c['name'] for c in cleaned[:10]]}")
            if len(cleaned) < 3:
                logging.warning(f"Only extracted {len(cleaned)} characters - expected at least 3")
            
            return cleaned
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse character JSON: {e}")
            logging.error(f"Raw response preview: {json_str[:500] if 'json_str' in locals() else 'N/A'}...")
            return []
        except Exception as e:
            logging.error(f"Character extraction failed: {e}")
            return []
    
    def extract_world_elements(self, content: str) -> List[Dict[str, Any]]:
        """Use AI to extract world building elements from manuscript content."""
        import time
        
        if not self.ai or not self.ai.llm:
            logging.warning("AI engine not available for world extraction")
            return []
        
        try:
            text = self._get_representative_text(content)
            logging.info(f"Starting world element extraction for {len(content)} characters of text")
            logging.info(f"Representative text sample: {len(text)} chars")
            
            prompt = PROMPT_EXTRACT_WORLD.format(text=text)
            
            start_time = time.time()
            response = self.ai.llm(prompt, max_tokens=2000, stop=["<|eot_id|>"])
            elapsed = time.time() - start_time
            
            raw_response = response['choices'][0]['text'].strip()
            logging.info(f"World element extraction completed in {elapsed:.2f}s")
            logging.info(f"Raw AI response length: {len(raw_response)} chars")
            
            json_str = "[" + raw_response
            
            # Clean up JSON
            if not json_str.endswith("]"):
                last_bracket = json_str.rfind("}")
                if last_bracket > 0:
                    json_str = json_str[:last_bracket + 1] + "]"
            
            elements = json.loads(json_str)
            
            # Validate and clean element data
            cleaned = []
            for elem in elements:
                if isinstance(elem, dict) and elem.get('name'):
                    cleaned.append({
                        'name': elem.get('name', ''),
                        'element_type': elem.get('element_type', 'other'),
                        'description': elem.get('description', ''),
                        'sensory_details': elem.get('sensory_details', ''),
                        'significance': elem.get('significance', ''),
                        'is_visible': 1
                    })
            
            logging.info(f"Parsed {len(cleaned)} world elements: {[w['name'] for w in cleaned[:10]]}")
            if len(cleaned) < 2:
                logging.warning(f"Only extracted {len(cleaned)} world elements - expected at least 2")
            
            return cleaned
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse world elements JSON: {e}")
            logging.error(f"Raw response preview: {json_str[:500] if 'json_str' in locals() else 'N/A'}...")
            return []
        except Exception as e:
            logging.error(f"World extraction failed: {e}")
            return []
    
    def extract_characters_and_world_combined(self, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Use AI to extract both characters and world elements in a single call.
        This is faster than separate calls but may be slightly less detailed.
        
        Returns:
            Dict with 'characters' and 'world_elements' keys
        """
        import time
        
        if not self.ai or not self.ai.llm:
            logging.warning("AI engine not available for combined extraction")
            return {'characters': [], 'world_elements': []}
        
        try:
            text = self._get_representative_text(content)
            logging.info(f"Starting combined extraction for {len(content)} characters of text")
            logging.info(f"Representative text sample: {len(text)} chars")
            
            prompt = PROMPT_EXTRACT_COMBINED.format(text=text)
            
            start_time = time.time()
            response = self.ai.llm(prompt, max_tokens=3500, stop=["<|eot_id|>"])
            elapsed = time.time() - start_time
            
            raw_response = response['choices'][0]['text'].strip()
            logging.info(f"Combined extraction completed in {elapsed:.2f}s")
            logging.info(f"Raw AI response length: {len(raw_response)} chars")
            
            # The response should start with { "characters": [
            json_str = "{" + raw_response
            
            # Clean up JSON - find the end of the structure
            if not json_str.endswith("}"):
                # Try to find the last complete closing brace for the main object
                # Look for pattern: ]} or similar
                last_world_bracket = json_str.rfind("]")
                if last_world_bracket > 0:
                    # Add closing brace after the last array
                    json_str = json_str[:last_world_bracket + 1] + "}"
            
            # Parse the combined JSON
            try:
                combined_data = json.loads(json_str)
            except json.JSONDecodeError:
                # If that fails, try to extract each section separately
                logging.warning("Failed to parse combined JSON, attempting to extract sections...")
                
                # Try to find characters array
                char_start = json_str.find('"characters"')
                world_start = json_str.find('"world_elements"')
                
                characters = []
                world_elements = []
                
                if char_start > 0:
                    char_array_start = json_str.find('[', char_start)
                    if world_start > char_start:
                        char_array_end = json_str.rfind(']', char_array_start, world_start)
                    else:
                        char_array_end = json_str.rfind(']')
                    
                    if char_array_start > 0 and char_array_end > char_array_start:
                        char_json = json_str[char_array_start:char_array_end + 1]
                        try:
                            characters = json.loads(char_json)
                        except:
                            pass
                
                if world_start > 0:
                    world_array_start = json_str.find('[', world_start)
                    world_array_end = json_str.rfind(']')
                    
                    if world_array_start > 0 and world_array_end > world_array_start:
                        world_json = json_str[world_array_start:world_array_end + 1]
                        try:
                            world_elements = json.loads(world_json)
                        except:
                            pass
                
                combined_data = {
                    'characters': characters,
                    'world_elements': world_elements
                }
            
            # Validate and clean character data
            cleaned_chars = []
            for char in combined_data.get('characters', []):
                if isinstance(char, dict) and char.get('name'):
                    cleaned_chars.append({
                        'name': char.get('name', ''),
                        'role': char.get('role', 'supporting'),
                        'personality_traits': char.get('personality_traits', ''),
                        'physical_description': char.get('physical_description', ''),
                        'backstory': char.get('backstory', ''),
                        'speech_pattern': char.get('speech_pattern', ''),
                        'motivations': char.get('motivations', ''),
                        'is_visible': 1
                    })
            
            # Validate and clean world element data
            cleaned_world = []
            for elem in combined_data.get('world_elements', []):
                if isinstance(elem, dict) and elem.get('name'):
                    cleaned_world.append({
                        'name': elem.get('name', ''),
                        'element_type': elem.get('element_type', 'other'),
                        'description': elem.get('description', ''),
                        'sensory_details': elem.get('sensory_details', ''),
                        'significance': elem.get('significance', ''),
                        'is_visible': 1
                    })
            
            logging.info(f"Parsed {len(cleaned_chars)} characters: {[c['name'] for c in cleaned_chars[:10]]}")
            logging.info(f"Parsed {len(cleaned_world)} world elements: {[w['name'] for w in cleaned_world[:10]]}")
            
            # Validate minimum results - if too few, fall back to separate extraction
            if len(cleaned_chars) < 2:
                logging.warning(f"Only extracted {len(cleaned_chars)} characters - expected at least 2. Falling back to separate extraction...")
                return {
                    'characters': self.extract_characters(content),
                    'world_elements': self.extract_world_elements(content)
                }
            
            return {
                'characters': cleaned_chars,
                'world_elements': cleaned_world
            }
            
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse combined JSON: {e}")
            logging.error(f"Raw response preview: {raw_response[:500] if 'raw_response' in locals() else 'N/A'}...")
            # Fall back to separate extraction
            logging.info("Falling back to separate character and world extraction...")
            return {
                'characters': self.extract_characters(content),
                'world_elements': self.extract_world_elements(content)
            }
        except Exception as e:
            logging.error(f"Combined extraction failed: {e}")
            # Fall back to separate extraction
            return {
                'characters': self.extract_characters(content),
                'world_elements': self.extract_world_elements(content)
            }
    
    def detect_genre_style(self, content: str) -> str:
        """Use AI to detect genre and writing style."""
        import time
        
        if not self.ai or not self.ai.llm:
            logging.warning("AI engine not available for genre detection")
            return ""
        
        try:
            text = self._get_representative_text(content, max_chars=4000)
            logging.info(f"Starting genre detection for {len(content)} characters of text")
            logging.info(f"Representative text sample: {len(text)} chars")
            
            prompt = PROMPT_DETECT_GENRE.format(text=text)
            
            start_time = time.time()
            response = self.ai.llm(prompt, max_tokens=200, stop=["<|eot_id|>"])
            elapsed = time.time() - start_time
            
            genre = response['choices'][0]['text'].strip()
            logging.info(f"Genre detection completed in {elapsed:.2f}s")
            logging.info(f"Detected genre: {genre[:100]}...")
            
            return genre
        except Exception as e:
            logging.error(f"Genre detection failed: {e}")
            return ""
    
    def parse_manuscript(self, content: str, extract_all: bool = True, combined_mode: bool = True) -> Dict[str, Any]:
        """
        Parse a complete manuscript and extract all story elements.
        
        Args:
            content: Full manuscript text
            extract_all: Whether to run AI extraction (can be slow)
            combined_mode: If True, extract characters and world elements in a single AI call (faster).
                          If False, use separate calls (more accurate but slower).
        
        Returns:
            Dict with chapters, synopsis, characters, world_elements, genre_style
        """
        result = {
            'chapters': self.detect_chapters(content),
            'synopsis': '',
            'characters': [],
            'world_elements': [],
            'genre_style': '',
            'word_count': len(content.split()),
            'chapter_count': 0
        }
        
        result['chapter_count'] = len(result['chapters'])
        
        # Clean chapter titles
        for chapter in result['chapters']:
            chapter['title'] = self.clean_chapter_title(chapter['title'])
        
        # AI extraction if requested and available
        if extract_all and self.ai and self.ai.llm:
            logging.info(f"Running AI extraction on manuscript (combined_mode={combined_mode})...")
            logging.info(f"Manuscript stats: {result['word_count']} words, {result['chapter_count']} chapters")
            
            # Use full content for extraction
            full_text = content
            
            # Extract synopsis first (always separate)
            result['synopsis'] = self.extract_synopsis(full_text)
            
            # Extract characters and world elements
            if combined_mode:
                # Single combined call - faster
                logging.info("Using combined extraction mode (faster)")
                combined = self.extract_characters_and_world_combined(full_text)
                result['characters'] = combined.get('characters', [])
                result['world_elements'] = combined.get('world_elements', [])
            else:
                # Separate calls - more accurate but slower
                logging.info("Using separate extraction mode (more accurate)")
                result['characters'] = self.extract_characters(full_text)
                result['world_elements'] = self.extract_world_elements(full_text)
            
            # Extract genre/style last
            result['genre_style'] = self.detect_genre_style(full_text)
            
            logging.info(f"Extraction complete: {len(result['characters'])} characters, {len(result['world_elements'])} world elements")
        
        return result
    
    @staticmethod
    def read_file(file_path: str) -> str:
        """Read content from various file formats."""
        import os
        
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif ext == '.md':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif ext == '.docx':
            try:
                import docx
                doc = docx.Document(file_path)
                paragraphs = [p.text for p in doc.paragraphs]
                return '\n'.join(paragraphs)
            except ImportError:
                logging.error("python-docx not installed. Run: pip install python-docx")
                return ""
        
        elif ext == '.epub':
            try:
                import ebooklib
                from ebooklib import epub
                from bs4 import BeautifulSoup
                
                book = epub.read_epub(file_path)
                content = []
                
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        soup = BeautifulSoup(item.get_content(), 'html.parser')
                        content.append(soup.get_text())
                
                return '\n'.join(content)
            except ImportError:
                logging.error("ebooklib or beautifulsoup4 not installed")
                return ""
        
        else:
            logging.warning(f"Unsupported file format: {ext}")
            return ""

