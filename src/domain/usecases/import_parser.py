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
        if not self.ai or not self.ai.llm:
            logging.warning("AI engine not available for synopsis extraction")
            return ""
        
        try:
            text = self._get_representative_text(content)
            prompt = PROMPT_EXTRACT_SYNOPSIS.format(text=text)
            
            response = self.ai.llm(prompt, max_tokens=500, stop=["<|eot_id|>"])
            return response['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"Synopsis extraction failed: {e}")
            return ""
    
    def extract_characters(self, content: str) -> List[Dict[str, Any]]:
        """Use AI to extract character profiles from manuscript content."""
        if not self.ai or not self.ai.llm:
            logging.warning("AI engine not available for character extraction")
            return []
        
        try:
            text = self._get_representative_text(content)
            prompt = PROMPT_EXTRACT_CHARACTERS.format(text=text)
            
            response = self.ai.llm(prompt, max_tokens=2000, stop=["<|eot_id|>"])
            json_str = "[" + response['choices'][0]['text'].strip()
            
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
            
            return cleaned
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse character JSON: {e}")
            return []
        except Exception as e:
            logging.error(f"Character extraction failed: {e}")
            return []
    
    def extract_world_elements(self, content: str) -> List[Dict[str, Any]]:
        """Use AI to extract world building elements from manuscript content."""
        if not self.ai or not self.ai.llm:
            logging.warning("AI engine not available for world extraction")
            return []
        
        try:
            text = self._get_representative_text(content)
            prompt = PROMPT_EXTRACT_WORLD.format(text=text)
            
            response = self.ai.llm(prompt, max_tokens=2000, stop=["<|eot_id|>"])
            json_str = "[" + response['choices'][0]['text'].strip()
            
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
            
            return cleaned
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse world elements JSON: {e}")
            return []
        except Exception as e:
            logging.error(f"World extraction failed: {e}")
            return []
    
    def detect_genre_style(self, content: str) -> str:
        """Use AI to detect genre and writing style."""
        if not self.ai or not self.ai.llm:
            logging.warning("AI engine not available for genre detection")
            return ""
        
        try:
            text = self._get_representative_text(content, max_chars=4000)
            prompt = PROMPT_DETECT_GENRE.format(text=text)
            
            response = self.ai.llm(prompt, max_tokens=200, stop=["<|eot_id|>"])
            return response['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"Genre detection failed: {e}")
            return ""
    
    def parse_manuscript(self, content: str, extract_all: bool = True) -> Dict[str, Any]:
        """
        Parse a complete manuscript and extract all story elements.
        
        Args:
            content: Full manuscript text
            extract_all: Whether to run AI extraction (can be slow)
        
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
            logging.info("Running AI extraction on manuscript...")
            
            # Use full content for extraction
            full_text = content
            
            # Extract in parallel if possible, otherwise sequential
            result['synopsis'] = self.extract_synopsis(full_text)
            result['characters'] = self.extract_characters(full_text)
            result['world_elements'] = self.extract_world_elements(full_text)
            result['genre_style'] = self.detect_genre_style(full_text)
            
            logging.info(f"Extracted: {len(result['characters'])} characters, {len(result['world_elements'])} world elements")
        
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

