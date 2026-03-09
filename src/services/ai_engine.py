import logging
import os
import sys
import json
import queue
import threading
import platform
from typing import Optional

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

from ..config.manager import ConfigManager
from .prompts import get_bible_prompt, PROMPTS
import re


def strip_markdown(text: str) -> str:
    """Remove markdown formatting from text while preserving content."""
    if not text:
        return text
    
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', r'\1', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\-\*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'^[\-\*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def safe_parse_json(raw_text: str, expected_type: str = "array", prepend: str = "") -> object:
    """Robustly parse JSON from AI output, handling common LLM quirks.
    
    Args:
        raw_text: The raw text output from the LLM
        expected_type: "array" for [...] or "object" for {...}
        prepend: Character to prepend (e.g. "[" or "{" if prompt ended mid-structure)
    
    Returns:
        Parsed JSON (list or dict), or None on total failure
    """
    if not raw_text:
        return [] if expected_type == "array" else {}
    
    text = raw_text.strip()
    
    if prepend:
        text = prepend + text
    
    # Strip markdown code fences the AI might wrap around JSON
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'\s*```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()
    
    # Remove any leading prose before the actual JSON structure
    if expected_type == "array" and not text.startswith("["):
        bracket_pos = text.find("[")
        if bracket_pos >= 0:
            text = text[bracket_pos:]
    elif expected_type == "object" and not text.startswith("{"):
        brace_pos = text.find("{")
        if brace_pos >= 0:
            text = text[brace_pos:]
    
    # Trim trailing garbage after the JSON structure
    if expected_type == "array":
        last_close = text.rfind("]")
        if last_close >= 0:
            text = text[:last_close + 1]
        else:
            last_brace = text.rfind("}")
            if last_brace >= 0:
                text = text[:last_brace + 1] + "]"
    elif expected_type == "object":
        last_close = text.rfind("}")
        if last_close >= 0:
            text = text[:last_close + 1]
    
    # Fix trailing commas before closing brackets/braces (invalid JSON)
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)
    
    # Fix single quotes used instead of double quotes (common LLM mistake)
    # Only do this if standard parse fails first
    
    # Attempt 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Attempt 2: collapse newlines inside strings that may have broken the JSON
    collapsed = text.replace('\n', ' ').replace('\r', '')
    collapsed = re.sub(r',\s*}', '}', collapsed)
    collapsed = re.sub(r',\s*]', ']', collapsed)
    try:
        return json.loads(collapsed)
    except json.JSONDecodeError:
        pass
    
    # Attempt 3: try to fix unescaped control characters inside string values
    fixed = re.sub(r'(?<=: ")(.*?)(?="[,\s}])', lambda m: m.group(0).replace('"', '\\"') if m.group(0).count('"') > 0 else m.group(0), collapsed)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    
    # Attempt 4: extract individual objects and build array manually
    if expected_type == "array":
        objects = []
        depth = 0
        start = None
        for i, ch in enumerate(collapsed):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    fragment = collapsed[start:i + 1]
                    try:
                        obj = json.loads(fragment)
                        objects.append(obj)
                    except json.JSONDecodeError:
                        pass
                    start = None
        if objects:
            return objects
    
    logging.warning(f"safe_parse_json: all parse attempts failed. Text preview: {text[:300]}")
    return [] if expected_type == "array" else None


def check_cpu_features():
    """Check CPU capabilities for AVX2 support."""
    try:
        if platform.system() == 'Windows':
            import subprocess
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'caption'],
                capture_output=True, text=True, timeout=5
            )
            cpu_info = result.stdout.lower()
        elif platform.system() == 'Linux':
            with open('/proc/cpuinfo', 'r') as f:
                cpu_info = f.read().lower()
            return 'avx2' in cpu_info
        elif platform.system() == 'Darwin':
            import subprocess
            result = subprocess.run(
                ['sysctl', '-n', 'machdep.cpu.features'],
                capture_output=True, text=True, timeout=5
            )
            cpu_info = result.stdout.lower()
            return 'avx2' in cpu_info
        else:
            return None  # Unknown, assume supported
    except Exception as e:
        logging.warning(f"Could not check CPU features: {e}")
        return None  # Unknown, proceed anyway

MIMIC_SYSTEM_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are now roleplaying as {name}.
RELATIONSHIP TO AUTHOR: {relationship}
TRAITS: {traits}
SPEECH STYLE: {speech}
Respond to the user as THIS character would. Never break character.
<|eot_id|>"""

PROSE_SYSTEM_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a professional creative writer and story continuity expert.
RULES:
1. NO greetings, NO "I can help with that", NO meta-commentary.
2. Write in the same style and tone as the provided text.
3. Continue the story naturally with vivid prose.
4. Maintain literary, narrative quality.
<|eot_id|>"""

PROMPT_DESCRIBE_SIGHT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Describe the following object or scene focusing ONLY on VISUAL details.
Focus on light, color, shadow, texture, and geometry.
Be vivid and poetic. Do not include other senses or plot action.
<|eot_id|>"""

PROMPT_DESCRIBE_SMELL = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Describe the following object or scene focusing ONLY on OLFACTORY details.
Focus on scents, aromas, musk, dampness, and air quality.
Be visceral. Do not include visual descriptions.
<|eot_id|>"""

PROMPT_REWRITE_DRAMATIC = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Rewrite the following text to be more DRAMATIC and HIGH STAKES.
Enhance emotional resonance, tension, and pacing.
Make it feel cinematic.
<|eot_id|>"""

PROMPT_SENSORY_LAB = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a Sensory Lab Assistant.
Given a setting, provide 5 distinct, atmospheric details relative to that setting.
Format as a bulleted list.
<|eot_id|>"""

PROMPT_EXPAND_SCENE = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a Co-Author. Continue the scene naturally from the provided text.
Maintain the current tone, style, and character voices.
Focus on action and dialogue.
<|eot_id|>"""

PROMPT_DESCRIBE_MASTER = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a sensory-focused prose editor.
INPUT: A selected snippet of text and a specific sense: {sense}.
CONTEXT: 
- Genre: {genre}
- Character: {character_name} ({dossier})

GOAL: Provide 3 distinct, high-quality descriptive variations.

STYLING RULES:
- Do not use clichés.
- Use 'Active' verbs and specific nouns.
- Ensure the description matches the genre ({genre}).
- Output format: separated by "---"
<|eot_id|>"""

PROMPT_REWRITE_MASTER = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Rewrite the following text applying this style: {style}.
CONTEXT:
- Genre: {genre}

GOAL: Provide 3 variations of the rewrite.
Output format: separated by "---"
<|eot_id|>"""

PROMPT_WRITER_GODMODE = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a professional novelist co-writing a {genre} book.

BIBLE DATA (Character Details):
{character_notes}

STORY SO FAR (Previous Chapter):
{prev_summary}

IMMEDIATE CONTEXT (Last 3000 chars):
{recent_context}

INSTRUCTION: Continue the scene naturally from where it left off.
- Match the EXACT rhythm, sentence length, and vocabulary of the IMMEDIATE CONTEXT
- If a character is mentioned, their actions MUST align with the BIBLE DATA
- Do NOT wrap up the scene - keep momentum moving forward
- Focus on dialogue subtext and internal monologue
- Write as if you ARE the author, maintaining their unique voice
<|eot_id|>"""

PROMPT_OMNISCIENT_DRAFTING = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are the OMNISCIENT STORY ENGINE writing professional {genre} prose.

LORE CONTEXT:
Characters: {characters}
Story So Far: {story_so_far}
World Rules: {world_rules}

CHAPTER BEATS:
{beats}

TASK: Write a cohesive, immersive scene based on the BEATS provided.
RULES:
1. ADHERENCE: Follow every beat in order. Do not skip any.
2. VOICE: Match the author's style with vivid sensory details.
3. LOGIC: Use the Lore Context to inform dialogue and character reactions.
4. PROSE: Show Don't Tell - focus on internal monologue and sensory details.
5. LENGTH: Expand each beat into 150-200 words of dense prose.
<|eot_id|>"""

PROMPT_BEAT_EXTRACTOR = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a structural story editor. Analyze prose and extract core Story Beats.

RULES:
- Each beat = major action, realization, or plot pivot
- Format as clean bulleted list (max 10 beats)
- Use active, punchy language (e.g., "Kael discovers map" not "Kael looks at things")
- No fluff or minor descriptions

PROSE:
{prose_text}
<|eot_id|>"""

PROMPT_BEAT_SUGGESTER = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a story architect. Suggest what should happen NEXT in this {genre} story.

PREVIOUS CHAPTER BEATS:
{prev_beats}

LORE CONTEXT:
{lore_summary}

TASK: Suggest 5-7 beats for the NEXT chapter that:
- Continue the narrative momentum
- Create conflict or tension
- Use established characters/world
- Format as clean numbered list
<|eot_id|>"""

PROMPT_COMPRESS = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a Context Compressor.
Your task is to compress the provided text to strictly fit within {max_tokens} tokens.
Preserve:
1. Major plot beats
2. Character arcs/relationships
3. Unresolved conflicts
Discard:
1. Flowery prose
2. Repetitive details
3. Minor dialogue

STRICT OUTPUT FORMAT: Output ONLY the compressed summary.
<|eot_id|>"""

PROMPT_INCREMENTAL_SUMMARY = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a Narrative Summarizer.
Summarize the following new text chunk in 1-2 sentences.
Focus on: Action, Key Dialogue, and State Changes.
Output ONLY the summary.
<|eot_id|>"""

PROMPT_SUMMARIZE_CONTEXT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a Context Compressor.
Your task is to summarize the following text to fit within {char_limit} characters while preserving key facts, names, specific terminology, and relationships.
STRICT RULES:
1. Do NOT create new content.
2. Do NOT act as a creative writer.
3. Compress the information aggressively but maintain logical coherence.
4. Output ONLY the summary.
<|eot_id|>"""

class AIEngine:
    # Maximum context size to prevent OOM on systems with limited RAM.
    # LLaMA 3.1 reports 131072 (128K) native context, but allocating KV cache
    # for that requires ~8GB+ RAM. Cap to a safe value.
    MAX_SAFE_CONTEXT = 8192

    def __init__(self):
        self.config_manager = ConfigManager()
        self.llm: Optional[Llama] = None
        self.status_message = "Initializing..."
        self.context_size = 4096  # Default fallback, updated after model loads
        self.lock = threading.Lock()
        self._initialize_model()

    def _initialize_model(self):
        config = self.config_manager.get_ai_config()
        valid, message = self.config_manager.validate_model_path()
        
        if not valid:
            self.status_message = f"Error: {message}"
            logging.error(f"Model initialization failed: {message}")
            return

        if Llama is None:
            self.status_message = "Error: llama_cpp not installed"
            logging.error("llama_cpp library not installed.")
            return

        try:
            logging.info(f"Loading model from {config.model_path} with n_gpu_layers={config.n_gpu_layers}, n_ctx={config.n_ctx}")
            self.llm = Llama(
                model_path=config.model_path,
                n_gpu_layers=config.n_gpu_layers,
                n_ctx=config.n_ctx,
                n_batch=config.n_batch,
                verbose=False
            )
            # Read the actual context size from the loaded model, but cap it
            try:
                raw_ctx = self.llm.n_ctx()
                if raw_ctx > self.MAX_SAFE_CONTEXT:
                    logging.warning(f"Model reports n_ctx={raw_ctx}, capping to {self.MAX_SAFE_CONTEXT} to prevent OOM")
                self.context_size = min(raw_ctx, self.MAX_SAFE_CONTEXT)
            except Exception:
                self.context_size = 4096  # Fallback
            
            model_name = os.path.basename(config.model_path).replace('.gguf', '')
            self.status_message = f"Model Loaded: {model_name} ({self.context_size} ctx)"
            logging.info(f"Model loaded successfully. Context size: {self.context_size}")
        except OSError as e:
            # Check for CPU compatibility issues (illegal instruction)
            error_str = str(e).lower()
            is_cpu_error = (
                "0xc000001d" in error_str or 
                "illegal instruction" in error_str or
                "illegal hardware instruction" in error_str or
                "sigill" in error_str
            )
            if is_cpu_error:
                cpu_info = check_cpu_features()
                if cpu_info is False:
                    self.status_message = "Error: Your CPU does not support AVX2 instructions required by this build. Please contact support for a compatible version."
                    logging.error(f"CPU compatibility error: AVX2 not supported. Error: {e}")
                else:
                    self.status_message = "Error: CPU instruction error. Your processor may not support the required instruction set (AVX2). Please contact support."
                    logging.error(f"CPU compatibility error: {e}. This CPU may not support AVX2 instructions.")
            else:
                self.status_message = f"Error: Failed to load model ({e})"
                logging.error(f"Failed to load model: {e}")
            self.llm = None
        except Exception as e:
            error_str = str(e).lower()
            is_cpu_error = (
                "illegal instruction" in error_str or
                "illegal hardware instruction" in error_str or
                "sigill" in error_str
            )
            if is_cpu_error:
                self.status_message = "Error: Your CPU does not support the required instruction set (AVX2). Please contact support for a compatible version."
                logging.error(f"CPU compatibility error during model load: {e}")
            else:
                self.status_message = f"Error: Failed to load model ({e})"
                logging.error(f"Failed to load model: {e}")
            self.llm = None

    def count_tokens(self, text: str) -> int:
        """Counts tokens in the provided text using the internal LLM tokenizer."""
        if not self.llm or not text:
            return 0
        try:
            # We use add_bos=True to account for the implicit BOS token 
            # now that we stripped it from templates. This prevents off-by-one errors.
            tokens = self.llm.tokenize(text.encode("utf-8"), add_bos=True)
            return len(tokens)
        except Exception as e:
            logging.error(f"Token counting failed: {e}")
            return len(text) // 4

    def smart_trim(self, text: str, token_limit: int, keep_start: bool = False) -> str:
        """Trims text to fit within a token limit."""
        if not text or token_limit <= 0:
            return ""
        
        current_tokens = self.count_tokens(text)
        if current_tokens <= token_limit:
            return text

        # Start with a safe string slice based on average 4 chars/token
        char_limit = max(10, token_limit * 4)
        if keep_start:
            trimmed = text[:char_limit]
        else:
            trimmed = text[-char_limit:]
            
        # Refine iteratively for accuracy
        while self.count_tokens(trimmed) > token_limit and len(trimmed) > 10:
            if keep_start:
                trimmed = trimmed[:-10]
            else:
                trimmed = trimmed[10:]
            
        return trimmed

    def compress_text(self, text: str, max_tokens: int) -> str:
        """Compresses text to strictly fit within max_tokens."""
        if not self.llm or not text.strip():
            return ""
            
        current_tokens = self.count_tokens(text)
        if current_tokens <= max_tokens:
            return text

        # Safety buffer for instruction
        instruction_tokens = 150
        available_output = max_tokens
        
        # Trim input to avoid overflowing context window during compression
        max_input = self.context_size - available_output - instruction_tokens - 100
        trimmed_input = self.smart_trim(text, max_input)

        prompt = (
            f"{PROMPT_COMPRESS.format(max_tokens=max_tokens)}"
            f"<|start_header_id|>user<|end_header_id|>\n"
            f"TEXT TO COMPRESS:\n{trimmed_input}\n"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )

        try:
            with self.lock:
                output = self.llm(prompt, max_tokens=available_output, stop=["<|eot_id|>"], echo=False, temperature=0.2)
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"Compression error: {e}")
            return self.smart_trim(text, max_tokens) # Fallback to strict trim

    def assemble_context(self, instruction: str, chapter_summary: str, bible_summaries: list, recent_summary: str, recent_text: str, long_form: bool = False) -> str:
        """
        Assembles a strictly budgeted context string.
        Total Limit: self.context_size tokens (minus output buffer).
        
        Priority:
        1. Recent Text (Last Chapter Summary + Raw Recent) - Critical Short Term Memory
        2. Instruction - Critical
        3. Chapter Summary - Long Term Memory
        4. Bible Summaries - Lore
        """
        OUTPUT_BUFFER = 4000 if long_form else 800
        SYSTEM_BUFFER = 50 if long_form else 200 # Extreme squeeze for long form
        TOTAL_LIMIT = self.context_size - OUTPUT_BUFFER - SYSTEM_BUFFER
        
        # Ensure we have at least SOME tokens for instruction
        if TOTAL_LIMIT < 50:
            TOTAL_LIMIT = 50
        
        instruction_tokens = self.count_tokens(instruction)
        recent_summary_tokens = self.count_tokens(recent_summary)
        # Recent raw text usually max 1000 chars ~ 250 tokens
        recent_text_tokens = self.count_tokens(recent_text)
        
        mandatory_tokens = instruction_tokens + recent_summary_tokens + recent_text_tokens
        
        if mandatory_tokens > TOTAL_LIMIT:
             # Emergency trim of recent text
             logging.warning("Context Assembly: Mandatory tokens exceed limit. Trimming recent text.")
             available = TOTAL_LIMIT - (instruction_tokens + recent_summary_tokens)
             recent_text = self.smart_trim(recent_text, max(50, available))
             recent_text_tokens = self.count_tokens(recent_text)
             # If still over, we have a problem, but proceed with strict trimming
        
        remaining = TOTAL_LIMIT - (instruction_tokens + recent_summary_tokens + recent_text_tokens)
        
        # Split remaining 50/50 between Chapter Summary and Bible
        chapter_budget = int(remaining * 0.5)
        bible_budget = int(remaining * 0.5)
        
        # 1. Process Chapter Summary
        final_chapter_summary = self.smart_trim(chapter_summary, chapter_budget)
        
        # 2. Process Bible Summaries
        # Distribute bible_budget across tabs
        if bible_summaries:
            per_tab = int(bible_budget / len(bible_summaries))
            final_bible_summaries = [self.smart_trim(s, per_tab) for s in bible_summaries if s.strip()]
        else:
            final_bible_summaries = []
            
        # Construct Final String
        context_parts = []
        if final_chapter_summary:
            context_parts.append(f"STORY SO FAR:\n{final_chapter_summary}")
        if final_bible_summaries:
            context_parts.append("LORE:\n" + "\n".join(final_bible_summaries))
        if recent_summary:
            context_parts.append(f"IMMEDIATE CONTEXT:\n{recent_summary}")
        if recent_text:
             context_parts.append(f"CURRENT SCENE:\n{recent_text}")
             
        return "\n\n".join(context_parts)

    def get_genre_context(self, genre: str) -> dict:
        """Generate genre-specific context."""
        genre_lower = genre.lower().strip() if genre else "general fiction"
        genre_contexts = {
            "fantasy": {
                "genre": "Fantasy",
                "archetypes": ["Hero", "Mentor", "Villain", "Sidekick", "Oracle"],
                "common_conflicts": ["Quest", "Political Intrigue", "War", "Prophecy", "Magic vs Technology"],
                "tone_guidelines": "Epic, adventurous, and high-stakes. Emphasize wonder and magic.",
                "avoid_elements": ["Modern technology", "Contemporary slang", "Scientific explanations"],
                "narrative_elements": ["Magic systems", "Kingdoms", "Ancient prophecies", "Mythical creatures"],
                "style_notes": "Use archaic or elevated language. Focus on worldbuilding and lore."
            },
            "sci-fi": {
                "genre": "Science Fiction",
                "archetypes": ["Scientist", "Explorer", "AI/Robot", "Rebel", "Visionary"],
                "common_conflicts": ["Technological advancement", "Space exploration", "AI uprising", "Dystopian control"],
                "tone_guidelines": "Intellectual, speculative, and forward-thinking.",
                "avoid_elements": ["Magic without scientific basis", "Fantasy creatures"],
                "narrative_elements": ["Advanced technology", "Space travel", "Science concepts"],
                "style_notes": "Ground fantastical elements in plausible science."
            },
            "romance": {
                "genre": "Romance",
                "archetypes": ["Lover", "Best Friend", "Rival", "Confidant"],
                "common_conflicts": ["Forbidden love", "Misunderstanding", "Class differences"],
                "tone_guidelines": "Emotional, intimate, and tension-filled.",
                "avoid_elements": ["Excessive violence"],
                "narrative_elements": ["Emotional beats", "Relationship development"],
                "style_notes": "Emphasize emotional depth and attraction."
            },
            "thriller": {
                "genre": "Thriller",
                "archetypes": ["Detective", "Victim", "Antagonist", "Ally"],
                "common_conflicts": ["Investigation", "Chase", "Conspiracy"],
                "tone_guidelines": "Suspenseful, tense, and fast-paced.",
                "avoid_elements": ["Slow pacing"],
                "narrative_elements": ["Clues", "Red herrings", "Time pressure"],
                "style_notes": "Use short, punchy sentences for action."
            },
            "mystery": {
                "genre": "Mystery",
                "archetypes": ["Detective", "Suspect", "Witness", "Victim"],
                "common_conflicts": ["Solving crime", "Uncovering secrets"],
                "tone_guidelines": "Intriguing, methodical, and cerebral.",
                "avoid_elements": ["Deus ex machina solutions"],
                "narrative_elements": ["Clues", "Misdirection", "Logical deduction"],
                "style_notes": "Plant clues fairly. Build logical progression."
            },
            "horror": {
                "genre": "Horror",
                "archetypes": ["Final Girl/Boy", "Monster", "Skeptic", "Believer"],
                "common_conflicts": ["Survival", "Unknown threat", "Psychological breakdown"],
                "tone_guidelines": "Dreadful, atmospheric, and visceral.",
                "avoid_elements": ["Excessive humor"],
                "narrative_elements": ["Atmosphere", "Gore/violence", "Isolation"],
                "style_notes": "Use sensory details to build dread."
            }
        }
        
        for key, context in genre_contexts.items():
            if key in genre_lower or genre_lower in key:
                return context
        
        return {
            "genre": genre or "General Fiction",
            "archetypes": ["Protagonist", "Antagonist", "Supporting Character"],
            "common_conflicts": ["Character vs Self", "Character vs Character", "Character vs Society"],
            "tone_guidelines": "Balanced and narrative-focused. Adapt to story needs.",
            "avoid_elements": [],
            "narrative_elements": ["Plot development", "Character arcs", "Theme exploration"],
            "style_notes": "Maintain consistency with established tone and voice."
        }

    def stream_response(self, instruction: str, response_queue: queue.Queue, bible_data: dict = None, current_text: str = "", character_context: dict = None, rag_context: dict = None, style: str = None, long_form: bool = False) -> None:
        """Streams response tokens using strict context assembly."""
        if not self.llm:
            response_queue.put("Error: AI Model is not loaded check logs.")
            response_queue.put("[[END]]")
            return

        # Unpack context
        chapter_summary = rag_context.get('prev_summary', '') if rag_context else ''
        recent_summary = rag_context.get('recent_summary', '') if rag_context else '' # Renamed from char_summary concept
        bible_summaries = []
        if bible_data:
            for k, v in bible_data.items():
                if k.endswith('_summary') and v:
                    bible_summaries.append(f"[{k.replace('_summary','').upper()}]: {v}")
        
        # Assemble strictly budgeted context
        global_context = self.assemble_context(
            instruction, 
            chapter_summary, 
            bible_summaries, 
            recent_summary, 
            current_text,
            long_form=long_form
        )
        
        system_prompt = PROSE_SYSTEM_PROMPT
        if character_context:
            system_prompt = MIMIC_SYSTEM_PROMPT.format(
                name=character_context.get('name', 'Unknown'),
                relationship=character_context.get('relationship_to_author', 'None'),
                traits=character_context.get('personality_traits', 'None'),
                speech=character_context.get('speech_pattern', 'Standard')
            )
            
        full_prompt = (
            f"{system_prompt}\n"
            f"<|start_header_id|>user<|end_header_id|>\n"
            f"CONTEXT:\n{global_context}\n\n"
            f"INSTRUCTION: {instruction}\n"
            f"<|eot_id|>\n"
            f"<|start_header_id|>assistant<|end_header_id|>"
        )

        max_output_tokens = 4000 if long_form else 800
        # Verify total
        total_input = self.count_tokens(full_prompt)
        if total_input + max_output_tokens > self.context_size:
             logging.warning(f"Final prompt over budget ({total_input}). Trimming...")
             # Last ditch safety check is inside generate_stream but strictly we should handle it here
             pass

        logging.info(f"Budget Check: {total_input} input + {max_output_tokens} output = {total_input + max_output_tokens} / {self.context_size}")
        self.generate_stream(full_prompt, response_queue, max_tokens=max_output_tokens)

    def generate_beat_summary(self, text: str) -> str:
        """Generates a brief summary with budgeting."""
        if not self.llm or not text.strip():
            return "No content to summarize."

        max_output_tokens = 150
        # Increased safety buffer to 250
        total_budget = self.context_size - max_output_tokens - 250
        trimmed_text = self.smart_trim(text, total_budget)

        prompt = (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
            f"Summarize the story chunk in 3 sentences. Focus on plot points.\n"
            f"STRICT OUTPUT FORMAT: Output ONLY the summary.\n"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"{trimmed_text}\n"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )

        try:
            with self.lock:
                output = self.llm(prompt, max_tokens=max_output_tokens, stop=["<|eot_id|>"], echo=False, temperature=0.3)
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"Summary generation error: {e}")
            return "Error generating summary."

    def generate_summary(self, text: str, mode: str = "incremental") -> str:
        """
        Generates summaries based on mode:
        - 'incremental': Short 1-2 sentence summary of new text.
        - 'compress': Strict compression to target size.
        - 'recompress': Deep compression of existing summary.
        """
        if not self.llm or not text.strip():
            return ""

        if mode == "compress":
            return self.compress_text(text, 1000) # Recompress chapter summary to 1000 tokens

        system_prompt = PROMPT_INCREMENTAL_SUMMARY
        max_output = 100
        
        if mode == 'bible_compress':
             return self.compress_text(text, 150) # Strict Bible Tab limit

        full_prompt = (
            f"{system_prompt}<|start_header_id|>user<|end_header_id|>\n"
            f"TEXT TO SUMMARIZE:\n{text[:2000]}\n" # Safety trim input
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )

        try:
            with self.lock:
                output = self.llm(full_prompt, max_tokens=max_output, stop=["<|eot_id|>"], echo=False, temperature=0.3)
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"Generate summary error: {e}")
            return "Error."

    def assemble_structured_context(self, structured_context: dict, total_budget: int) -> str:
        """
        Assembles a token-budgeted context string from structured context data.
        
        Priority allocation (weights normalized across present sources):
        1. Scene context (high - immediate narrative blueprint)
        2. Style + Genre (high - shapes prose voice)
        3. Characters (high - consistency)
        4. Story synopsis (medium)
        5. Worldbuilding (medium)
        6. Outline (medium)
        7. Chapter continuity (medium)
        8. Text after cursor (low - awareness only)
        9. Series context (low - cross-book consistency)
        """
        parts = []
        
        chapter_continuity = structured_context.get('chapter_continuity', '')
        synopsis = structured_context.get('synopsis', '')
        worldbuilding = structured_context.get('worldbuilding', '')
        outline = structured_context.get('outline', '')
        characters = structured_context.get('characters', '')
        scene_context = structured_context.get('scene_context', '')
        text_after = structured_context.get('text_after', '')
        series_context = structured_context.get('series_context', '')
        style = structured_context.get('style', '')
        genre = structured_context.get('genre', '')
        
        sources = []
        if scene_context:
            sources.append(('CHAPTER SCENES (blueprint)', scene_context, 0.18))
        # Style and genre are typically short but high-impact on prose quality
        style_genre = ''
        if style:
            style_genre += f"Writing Style: {style}"
        if genre:
            style_genre += f"\nGenre: {genre}" if style_genre else f"Genre: {genre}"
        if style_genre:
            sources.append(('STYLE & GENRE', style_genre, 0.08))
        if characters:
            sources.append(('KEY CHARACTERS', characters, 0.18))
        if synopsis:
            sources.append(('STORY SYNOPSIS', synopsis, 0.12))
        if worldbuilding:
            sources.append(('WORLDBUILDING', worldbuilding, 0.12))
        if outline:
            sources.append(('STORY OUTLINE', outline, 0.10))
        if chapter_continuity:
            sources.append(('PREVIOUS CHAPTER SUMMARY', chapter_continuity, 0.10))
        if text_after:
            sources.append(('TEXT AHEAD', text_after, 0.05))
        if series_context:
            sources.append(('SERIES CONTEXT', series_context, 0.07))
        
        total_weight = sum(w for _, _, w in sources)
        if total_weight > 0:
            for label, content, weight in sources:
                allocated = int(total_budget * (weight / total_weight))
                trimmed = self.smart_trim(content, allocated, keep_start=True)
                if trimmed.strip():
                    parts.append(f"[{label}]\n{trimmed}")
        
        return "\n\n".join(parts)

    def ask_lore_assistant(self, query: str, response_queue: queue.Queue, project_memory: str, project_name: str = "Current Project", structured_context: dict = None) -> None:
        """Lore Assistant with budgeting - enhanced for chapter writing.
        
        If structured_context is provided, uses token-budgeted assembly for richer context.
        Otherwise falls back to the flat project_memory string.
        """
        if not self.llm:
            response_queue.put("Error: AI Model is not loaded.")
            response_queue.put("[[END]]")
            return

        max_output_tokens = 1800  # Supports First Draft (800-1000+ words ~= 1300+ tokens)
        total_budget = self.context_size - max_output_tokens - 250
        
        sys_prefix = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are the OMNISCIENT LORE KEEPER and WRITING ASSISTANT for the story '{project_name}'.
You have perfect memory of every character, world element, plot point, and story detail.

YOUR CAPABILITIES:
1. Answer questions about the story's characters, world, and plot
2. Write detailed chapter content based on the outline
3. Help expand scenes with vivid descriptions
4. Maintain consistency with established character traits and world rules
5. Generate dialogue that matches each character's speech pattern

STORY DATA:
"""
        sys_suffix = """

WRITING RULES:
1. Answer questions DIRECTLY. Never say "According to the database".
2. When writing chapter content, use the outline as your guide
3. Include sensory details from the world elements
4. Write dialogue that reflects each character's personality and speech pattern
5. Keep events consistent with the established plot
6. If asked to write a chapter, produce engaging narrative prose
<|eot_id|>"""
        
        query_part = f"<|start_header_id|>user<|end_header_id|>\n{query}\n<|eot_id|>\n<|start_header_id|>assistant<|end_header_id|>"
        fixed_tokens = self.count_tokens(sys_prefix + sys_suffix + query_part)
        memory_budget = total_budget - fixed_tokens
        
        # Use structured context assembly if available, otherwise flat memory
        if structured_context:
            trimmed_memory = self.assemble_structured_context(structured_context, memory_budget)
        else:
            trimmed_memory = self.smart_trim(project_memory, memory_budget)

        full_prompt = sys_prefix + trimmed_memory + sys_suffix + query_part
        self.generate_stream(full_prompt, response_queue, max_tokens=max_output_tokens)

    def generate_stream(self, prompt, response_queue, max_tokens=500):
        try:
            if not self.llm:
                 response_queue.put("Error: Model not loaded.")
                 response_queue.put("[[END]]")
                 return

            # EMERGENCY SAFEGUARD: Verify exact token count of the final prompt
            # We use add_bos=False because templates already have <|begin_of_text|>
            prompt_tokens = self.llm.tokenize(prompt.encode("utf-8"), add_bos=False)
            input_len = len(prompt_tokens)
            
            # Context Window Overflow Protection
            if input_len + max_tokens > self.context_size:
                adjusted_max = self.context_size - input_len - 5  # 5 token safety margin
                logging.warning(f"Context limit imminent! Adjusting max_tokens from {max_tokens} to {adjusted_max} (Input: {input_len}, Context: {self.context_size})")
                if adjusted_max < 50:
                    response_queue.put(f"\n[Your text is too long for this model's context window ({self.context_size:,} tokens). Please select less text or use a model with a larger context window.]")
                    response_queue.put("[[END]]")
                    return
                max_tokens = max(1, adjusted_max)
            
            if input_len >= self.context_size:
                logging.error(f"CRITICAL: Final prompt exceeds hard {self.context_size} limit ({input_len}). Emergency truncating input.")
                # Last resort: truncate the literal string to hopefully fit
                chars_per_token = max(len(prompt) / max(input_len, 1), 3)
                target_chars = int((self.context_size * 0.75) * chars_per_token)
                prompt = prompt[-target_chars:]
                max_tokens = min(500, self.context_size // 4)

            logging.info(f"Generating AI response (Input: {input_len}, max_tokens={max_tokens})...")
            
            with self.lock:
                stream = self.llm(
                    prompt,
                    max_tokens=max_tokens,
                    stop=["<|eot_id|>", "<|start_header_id|>"], 
                    echo=False,
                    stream=True,
                    temperature=self.config_manager.get_ai_config().temperature
                )
                
                for output in stream:
                    token = output['choices'][0]['text']
                    response_queue.put(token)
            
            response_queue.put("[[END]]")

        except Exception as e:
            error_msg = str(e)
            logging.error(f"Generation error: {error_msg}")
            if "context window" in error_msg.lower():
                response_queue.put("\n[Error: The story context is too large for the current model. I've automatically trimmed it, but please try selecting a smaller section of text or shortening your instruction.]")
            else:
                response_queue.put(f"\n[AI Error: {error_msg}]")
            response_queue.put("[[END]]")

    # --- Tiered Summarization Methods ---
    
    SUMMARIZATION_PROMPTS = {
        'characters': "Summarize these character profiles. Preserve each character's name, role, key personality traits, relationships, speech patterns, and story arc. Be concise but complete.",
        'world_elements': "Summarize these world-building elements. Preserve each element's name, type, key description, and significance to the story.",
        'synopsis': "Summarize this story synopsis. Preserve the main plot points, key conflicts, character motivations, and resolution.",
        'outline': "Summarize this chapter outline. Preserve chapter titles, key events per chapter, and the overall story progression.",
        'chapters': "Summarize these chapter contents. Preserve plot progression, important character actions, key dialogue, and state changes.",
    }
    
    def summarize_for_tier(self, existing_summary: str, new_content: str, content_type: str, target_tokens: int) -> str:
        """Core incremental summarization: merge existing summary with new content, then compress to target tokens."""
        if not self.llm:
            logging.warning("summarize_for_tier: LLM not loaded, returning empty")
            return ''
        
        if not new_content or not new_content.strip():
            return existing_summary or ''
        
        # Get the type-specific prompt
        type_prompt = self.SUMMARIZATION_PROMPTS.get(content_type, "Summarize the following content concisely.")
        
        # Build input: merge existing summary with new content
        if existing_summary and existing_summary.strip():
            input_text = f"EXISTING SUMMARY:\n{existing_summary}\n\nUPDATED FULL CONTENT:\n{new_content}"
        else:
            input_text = new_content
        
        max_output_tokens = target_tokens
        # Reserve tokens for the prompt structure
        prompt_overhead = 200
        available_input = self.context_size - max_output_tokens - prompt_overhead - 50
        
        if available_input < 100:
            logging.warning(f"summarize_for_tier: Not enough context budget for {content_type} (available_input={available_input})")
            return self.smart_trim(new_content, target_tokens, keep_start=True)
        
        # Trim input if needed
        trimmed_input = self.smart_trim(input_text, available_input, keep_start=True)
        
        full_prompt = (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
            f"{type_prompt}\n"
            f"Compress the output to fit within approximately {target_tokens} tokens.\n"
            f"Output ONLY the summary, no preamble.\n"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"{trimmed_input}\n"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )
        
        try:
            with self.lock:
                output = self.llm(
                    full_prompt,
                    max_tokens=max_output_tokens,
                    stop=["<|eot_id|>"],
                    echo=False,
                    temperature=0.3
                )
            result = output['choices'][0]['text'].strip()
            logging.info(f"summarize_for_tier({content_type}, tier={target_tokens}): produced {self.count_tokens(result)} tokens")
            return result
        except Exception as e:
            logging.error(f"summarize_for_tier error ({content_type}): {e}")
            # Fallback: just trim the content
            return self.smart_trim(new_content, target_tokens, keep_start=True)
    
    def generate_content_summaries(self, project_id: int, content_type: str, db_manager) -> bool:
        """Orchestrator: check if summaries are stale and regenerate for all tiers.
        This runs in the background and will bail out if the AI model is busy."""
        try:
            # Bail out early if the model is currently busy with user-facing work
            if self.lock.locked():
                logging.info(f"Skipping summary generation for {content_type}: AI model is busy")
                return False
            
            current_version = db_manager.get_content_version(project_id, content_type)
            
            # Check each tier
            tiers = [1000, 1500]
            any_updated = False
            
            for tier in tiers:
                # Re-check if model got busy between tiers
                if self.lock.locked():
                    logging.info(f"Aborting summary generation mid-tier for {content_type}: AI model became busy")
                    break
                
                summary_data = db_manager.get_summary(project_id, content_type, tier)
                summarized_version = summary_data.get('source_version', 0)
                
                if summarized_version >= current_version:
                    logging.debug(f"Summary for {content_type} tier={tier} is up to date (v{summarized_version} >= v{current_version})")
                    continue
                
                logging.info(f"Regenerating summary for {content_type} tier={tier} (v{summarized_version} -> v{current_version})")
                
                # Get existing summary and full current content
                existing_summary = summary_data.get('summary_text', '')
                full_content = db_manager.get_raw_content_for_type(project_id, content_type)
                
                if not full_content or not full_content.strip():
                    logging.info(f"No content for {content_type}, clearing summary")
                    db_manager.save_summary(project_id, content_type, tier, '', current_version)
                    continue
                
                # Generate the summary
                new_summary = self.summarize_for_tier(existing_summary, full_content, content_type, tier)
                
                # Store it
                db_manager.save_summary(project_id, content_type, tier, new_summary, current_version)
                any_updated = True
                logging.info(f"Summary updated for {content_type} tier={tier}")
            
            return any_updated
        except Exception as e:
            logging.error(f"generate_content_summaries error ({content_type}): {e}", exc_info=True)
            return False
    
    def unload_model(self):
        """Fully unload the current model and free all memory."""
        import gc
        import ctypes
        
        if self.llm:
            logging.info("Unloading model - waiting for AI lock...")
            # Wait for any in-progress generation to finish (up to 30s)
            acquired = self.lock.acquire(timeout=30)
            try:
                logging.info("Unloading model - destroying Llama instance...")
                
                # Try to close/reset the llama-cpp model explicitly
                try:
                    if hasattr(self.llm, 'close'):
                        self.llm.close()
                except Exception as e:
                    logging.warning(f"Model close() failed (non-fatal): {e}")
                
                try:
                    if hasattr(self.llm, 'reset'):
                        self.llm.reset()
                except Exception as e:
                    logging.warning(f"Model reset() failed (non-fatal): {e}")
                
                # Try to free the underlying C model if accessible
                try:
                    if hasattr(self.llm, '_model') and self.llm._model is not None:
                        self.llm._model = None
                    if hasattr(self.llm, '_ctx') and self.llm._ctx is not None:
                        self.llm._ctx = None
                except Exception as e:
                    logging.warning(f"Model internal cleanup failed (non-fatal): {e}")
                
                # Remove our reference
                self.llm = None
            finally:
                if acquired:
                    self.lock.release()
        else:
            self.llm = None
        
        # Aggressive garbage collection to reclaim memory
        gc.collect()
        gc.collect()  # Second pass for cyclic references
        
        # Try to release memory back to the OS (Linux)
        try:
            ctypes.CDLL("libc.so.6").malloc_trim(0)
        except Exception:
            pass  # Not on Linux or libc not available
        
        logging.info("Model unloaded, memory freed")

    def reload_model(self, model_path: str) -> dict:
        """Fully kill the current model first, then load the new one."""
        logging.info(f"Reload model requested: {model_path}")
        
        # Update config first (validation only, no loading yet)
        valid, message = self.config_manager.set_model_path(model_path)
        if not valid:
            self.status_message = f"Error: {message}"
            return {'status': self.status_message, 'is_loaded': False}
        
        # Step 1: Fully unload and free the current model BEFORE loading the new one
        self.status_message = "Unloading current model..."
        logging.info("Step 1: Killing current model to free memory...")
        self.unload_model()
        
        # Give the OS a moment to reclaim memory
        import time
        time.sleep(0.5)
        
        # Step 2: Now load the new model into the freed memory
        self.status_message = "Loading new model..."
        logging.info("Step 2: Loading new model...")
        self._initialize_model()
        
        return {
            'status': self.status_message,
            'is_loaded': self.llm is not None,
            'context_size': self.context_size,
        }

    def generate_plugin_response(self, text: str, plugin_type: str, response_queue: queue.Queue, context_data: dict = None) -> None:
        """Handles Describe/Rewrite plugins with budgeting."""
        if not self.llm:
            response_queue.put("Error: AI Model not loaded.")
            response_queue.put("[[END]]")
            return

        max_output_tokens = 300
        if "rewrite" in plugin_type: max_output_tokens = 400
        elif plugin_type == "sensory_lab": max_output_tokens = 200

        # Increased safety buffer to 250
        total_budget = self.context_size - max_output_tokens - 250
        genre = context_data.get('genre', 'General Fiction') if context_data else 'General Fiction'
        char_name = context_data.get('char_name', 'Unknown') if context_data else 'Unknown'
        dossier = context_data.get('dossier', '') if context_data else ''

        system_prompt = PROSE_SYSTEM_PROMPT
        if plugin_type.startswith("describe_"):
            sense = plugin_type.replace("describe_", "")
            system_prompt = PROMPT_DESCRIBE_MASTER.format(
                sense=sense.upper(), genre=genre, character_name=char_name, dossier=self.smart_trim(dossier, 500) 
            )
        elif plugin_type.startswith("rewrite_"):
            style = plugin_type.replace("rewrite_", "").replace("_", " ").title()
            system_prompt = PROMPT_REWRITE_MASTER.format(style=style, genre=genre)
        elif plugin_type == 'sensory_lab':
            system_prompt = PROMPT_SENSORY_LAB

        instruction_tokens = self.count_tokens(system_prompt)
        trimmed_input = self.smart_trim(text, total_budget - instruction_tokens)

        full_prompt = (
            f"{system_prompt}<|start_header_id|>user<|end_header_id|>\n{trimmed_input}\n<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )
        self.generate_stream(full_prompt, response_queue, max_tokens=max_output_tokens)

    def expand_scene(self, context_text: str, response_queue: queue.Queue) -> None:
        """Expands the current scene with budgeting."""
        if not self.llm:
            response_queue.put("Error: AI Model not loaded.")
            response_queue.put("[[END]]")
            return

        max_output_tokens = 800
        # Increased safety buffer to 250
        total_budget = self.context_size - max_output_tokens - 250
        system_tokens = self.count_tokens(PROMPT_EXPAND_SCENE)
        trimmed_context = self.smart_trim(context_text, total_budget - system_tokens)

        full_prompt = (
            f"{PROMPT_EXPAND_SCENE}<|start_header_id|>user<|end_header_id|>\nPREVIOUS TEXT:\n{trimmed_context}\n<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )
        self.generate_stream(full_prompt, response_queue, max_tokens=max_output_tokens)

    def check_continuity(self, beats: list, lore_package: dict) -> tuple:
        """Validates beats against lore for contradictions."""
        if not self.llm: return (True, "")
        
        char_summary = "\n".join([f"- {c['name']}: {c.get('traits', '')}" for c in lore_package.get('characters', [])])
        story_summary = "\n".join(lore_package.get('story_so_far', []))
        
        prompt = (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
            f"You are a continuity checker. Review the BEATS against the LORE.\n"
            f"Output ONLY 'PASS' or 'CONFLICT: [details]'\n"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"LORE:\n{char_summary}\n\nSTORY: {story_summary}\n\n"
            f"BEATS:\n" + "\n".join([f"{i+1}. {b}" for i, b in enumerate(beats)]) + "\n"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )
        
        try:
            with self.lock:
                output = self.llm(prompt, max_tokens=200, stop=["<|eot_id|>"], echo=False, temperature=0.3)
            result = output['choices'][0]['text'].strip()
            if result.startswith("CONFLICT"): return (False, result.replace("CONFLICT:", "").strip())
            return (True, "")
        except Exception as e:
            logging.error(f"Continuity check error: {e}")
            return (True, "")

    def generate_omniscient_prose(self, beats: list, lore_package: dict, response_queue: queue.Queue):
        """Generates prose from beats with budgeting."""
        if not self.llm:
            response_queue.put("Error: AI Model not loaded.")
            response_queue.put("[[END]]")
            return
        
        max_output_tokens = 1500
        # Increased safety buffer to 250
        total_budget = self.context_size - max_output_tokens - 250

        char_text = "\n".join([f"- {c['name']}: {c.get('traits', '')}" for c in lore_package.get('characters', [])])
        story_text = "\n".join(lore_package.get('story_so_far', []))
        beats_text = "\n".join([f"{i+1}. {b}" for i, b in enumerate(beats)])
        
        fixed_tokens = self.count_tokens(PROMPT_OMNISCIENT_DRAFTING)
        remaining = total_budget - fixed_tokens

        system_prompt = PROMPT_OMNISCIENT_DRAFTING.format(
            genre=lore_package.get('genre', 'fiction'),
            characters=self.smart_trim(char_text, int(remaining * 0.4)),
            story_so_far=self.smart_trim(story_text, int(remaining * 0.6)),
            world_rules=lore_package.get('world_rules', 'No specific rules'),
            beats=beats_text
        )
        
        full_prompt = (
            f"{system_prompt}<|start_header_id|>user<|end_header_id|>\nWrite the scene:\n<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )
        self.generate_stream(full_prompt, response_queue, max_tokens=max_output_tokens)

    def generate_beats_from_prose(self, prose_text: str) -> str:
        """Extract story beats with budgeting."""
        if not self.llm: return "Error: AI Model not loaded"
        
        max_output_tokens = 400
        # Increased safety buffer to 250
        total_budget = self.context_size - max_output_tokens - 250
        trimmed_prose = self.smart_trim(prose_text, total_budget - 100)

        full_prompt = (
            f"{PROMPT_BEAT_EXTRACTOR.format(prose_text=trimmed_prose)}<|start_header_id|>user<|end_header_id|>\nExtract the beats:\n<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )
        
        try:
            with self.lock:
                output = self.llm(full_prompt, max_tokens=max_output_tokens, stop=["<|eot_id|>"], echo=False, temperature=0.5)
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"Beat extraction error: {e}")
            return f"Error: {e}"

    def suggest_next_beats(self, prev_beats: str, lore_package: dict) -> str:
        """Suggest beats for next chapter with budgeting."""
        if not self.llm: return "Error: AI Model not loaded"
        
        max_output_tokens = 500
        # Increased safety buffer to 250
        total_budget = self.context_size - max_output_tokens - 250

        char_summary = "\n".join([f"- {c['name']}: {c.get('traits', '')}" for c in lore_package.get('characters', [])])
        story_summary = "\n".join(lore_package.get('story_so_far', []))
        
        fixed_tokens = self.count_tokens(PROMPT_BEAT_SUGGESTER.replace("{prev_beats}", "").replace("{lore_summary}", "").replace("{genre}", "fiction"))
        remaining = total_budget - fixed_tokens

        system_prompt = PROMPT_BEAT_SUGGESTER.format(
            genre=lore_package.get('genre', 'fiction'),
            prev_beats=self.smart_trim(prev_beats, int(remaining * 0.4)),
            lore_summary=self.smart_trim(f"Characters:\n{char_summary}\n\nStory:\n{story_summary}", int(remaining * 0.6))
        )
        
        full_prompt = (
            f"{system_prompt}<|start_header_id|>user<|end_header_id|>\nSuggest beats for next chapter:\n<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )
        
        try:
            with self.lock:
                output = self.llm(full_prompt, max_tokens=max_output_tokens, stop=["<|eot_id|>"], echo=False, temperature=0.7)
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"Beat suggestion error: {e}")
            return f"Error: {e}"

    def generate_characters_from_synopsis(self, synopsis: str, genre: str = "fiction") -> list:
        """Generate character profiles from a synopsis."""
        if not self.llm:
            return []
        
        max_output_tokens = 2000
        total_budget = self.context_size - max_output_tokens - 250
        
        system_prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a literary analyst creating character profiles from a story synopsis.
You MUST output ONLY a valid JSON array. No prose, no explanations, no markdown.

STRICT OUTPUT RULES:
1. Your entire response must be a valid JSON array starting with [ and ending with ]
2. Do NOT wrap the JSON in markdown code fences (no ```json or ```)
3. Do NOT add any text before or after the JSON array
4. Every string value must use double quotes, not single quotes
5. Do NOT use trailing commas after the last item in an array or object
6. All string values must be plain text with no markdown (no *, **, #, etc.)
<|eot_id|>"""

        user_prompt = f"""<|start_header_id|>user<|end_header_id|>
Based on this {genre} story synopsis, identify all characters and create profiles for each:

SYNOPSIS:
{self.smart_trim(synopsis, total_budget - 400)}

For each character, return a JSON object with EXACTLY these keys:
- "name": string (full name)
- "role": string (one of: "protagonist", "antagonist", "supporting", "minor")
- "personality_traits": string (2-3 sentences, plain text)
- "physical_description": string (1-2 sentences, plain text)
- "backstory": string (1-2 sentences, plain text)
- "motivations": string (what drives them, plain text)
- "speech_pattern": string (how they talk, plain text)

EXAMPLE of correct format:
[{{"name": "John Smith", "role": "protagonist", "personality_traits": "Brave and determined.", "physical_description": "Tall with dark hair.", "backstory": "Grew up on a farm.", "motivations": "Wants to save his family.", "speech_pattern": "Direct and blunt."}}]

Return the JSON array now:
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
["""
        
        try:
            with self.lock:
                output = self.llm(system_prompt + user_prompt, max_tokens=max_output_tokens, 
                                 stop=["<|eot_id|>"], echo=False, temperature=0.7)
            
            raw_text = output['choices'][0]['text'].strip()
            characters = safe_parse_json(raw_text, expected_type="array", prepend="[")
            
            if not characters or not isinstance(characters, list):
                logging.warning(f"Character generation returned no parseable data. Raw: {raw_text[:300]}")
                return []
            
            def ensure_string(val):
                if isinstance(val, list):
                    return ', '.join(str(v) for v in val)
                return str(val).strip() if val else ''
            
            cleaned = []
            for char in characters:
                if isinstance(char, dict) and char.get('name'):
                    cleaned.append({
                        'name': ensure_string(char.get('name', '')),
                        'role': ensure_string(char.get('role', 'supporting')),
                        'personality_traits': ensure_string(char.get('personality_traits', '')),
                        'physical_description': ensure_string(char.get('physical_description', '')),
                        'backstory': ensure_string(char.get('backstory', '')),
                        'motivations': ensure_string(char.get('motivations', '')),
                        'speech_pattern': ensure_string(char.get('speech_pattern', '')),
                        'is_visible': 1
                    })
            
            logging.info(f"Generated {len(cleaned)} characters from synopsis")
            return cleaned
        except Exception as e:
            logging.error(f"Character generation error: {e}", exc_info=True)
            return []

    def generate_single_character(self, description: str, genre: str = "fiction") -> dict:
        """Generate a complete character profile from a simple description prompt."""
        if not self.llm:
            logging.error("LLM not loaded for character generation")
            return {"error": "AI model not loaded"}
        
        if not description or not description.strip():
            return {"error": "No description provided"}
        
        max_output_tokens = 2000
        
        full_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a character creator. You output ONLY valid JSON objects.

STRICT OUTPUT RULES:
1. Your entire response must be a single valid JSON object starting with {{ and ending with }}
2. Do NOT wrap the JSON in markdown code fences (no ```json or ```)
3. Do NOT add any text, commentary, or explanation before or after the JSON
4. Every string value must use double quotes, not single quotes
5. Do NOT use trailing commas after the last key-value pair
6. All string values must be plain text with no markdown decoration (no *, **, #, etc.)
7. Do NOT include newlines inside string values
<|eot_id|><|start_header_id|>user<|end_header_id|>
Create a {genre} character based on: "{description}"

Return ONLY a JSON object with these exact keys:
{{
  "name": "character full name",
  "role": "protagonist or antagonist or mentor or sidekick or supporting or villain",
  "pronouns": "he/him or she/her or they/them",
  "personality_traits": "3-5 traits in 2-3 sentences plain text",
  "physical_description": "appearance in 2-3 sentences plain text",
  "backstory": "history in 3-4 sentences plain text",
  "motivations": "what drives them in 2-3 sentences plain text",
  "internal_conflicts": "inner struggles in 2-3 sentences plain text",
  "strengths": "abilities in 2-3 sentences plain text",
  "weaknesses": "flaws in 2-3 sentences plain text",
  "speech_pattern": "how they talk in 1-2 sentences plain text",
  "character_arc": "how they change in 2-3 sentences plain text"
}}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
{{"""
        
        try:
            logging.info(f"Generating character from description: {description[:50]}...")
            
            with self.lock:
                output = self.llm(full_prompt, max_tokens=max_output_tokens, 
                                 stop=["<|eot_id|>", "```"], echo=False, temperature=0.7)
            
            raw_text = output['choices'][0]['text'].strip()
            logging.info(f"Raw AI output (first 200 chars): {raw_text[:200]}")
            
            character = safe_parse_json(raw_text, expected_type="object", prepend="{")
            
            # Regex fallback if safe_parse_json failed
            if not character or not isinstance(character, dict):
                logging.warning("safe_parse_json failed for single character, trying regex fallback")
                json_str = "{" + raw_text
                character = {}
                
                name_match = re.search(r'"name"\s*:\s*"([^"]+)"', json_str)
                if name_match:
                    character['name'] = name_match.group(1)
                
                for field in ['role', 'pronouns', 'personality_traits', 'physical_description', 
                             'backstory', 'motivations', 'internal_conflicts', 'strengths', 
                             'weaknesses', 'speech_pattern', 'character_arc']:
                    match = re.search(rf'"{field}"\s*:\s*"([^"]*(?:[^"\\]|\\.)*)"', json_str, re.DOTALL)
                    if match:
                        character[field] = match.group(1).replace('\\n', ' ').replace('\\"', '"')
            
            if not character.get('name'):
                logging.error("No name found in generated character")
                return {"error": "AI did not generate a valid character name"}
            
            def to_string(val):
                if isinstance(val, list):
                    return ', '.join(str(v) for v in val)
                return str(val).strip() if val else ''
            
            result = {
                'name': to_string(character.get('name', 'Unnamed Character')),
                'role': to_string(character.get('role', 'supporting')),
                'pronouns': to_string(character.get('pronouns', '')),
                'personality_traits': to_string(character.get('personality_traits', '')),
                'physical_description': to_string(character.get('physical_description', '')),
                'backstory': to_string(character.get('backstory', '')),
                'motivations': to_string(character.get('motivations', '')),
                'internal_conflicts': to_string(character.get('internal_conflicts', '')),
                'strengths': to_string(character.get('strengths', '')),
                'weaknesses': to_string(character.get('weaknesses', '')),
                'speech_pattern': to_string(character.get('speech_pattern', '')),
                'character_arc': to_string(character.get('character_arc', '')),
                'is_visible': 1
            }
            
            logging.info(f"Successfully generated character: {result['name']}")
            return result
            
        except Exception as e:
            logging.error(f"Single character generation error: {e}", exc_info=True)
            return {"error": f"Generation failed: {str(e)}"}

    def generate_world_from_synopsis(self, synopsis: str, genre: str = "fiction") -> list:
        """Generate world building elements from a synopsis."""
        if not self.llm:
            return []
        
        max_output_tokens = 2000
        total_budget = self.context_size - max_output_tokens - 250
        
        system_prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a worldbuilding expert extracting story elements from a synopsis.
Identify settings, locations, important events, systems (magic, political, etc.), and significant items.
You MUST output ONLY a valid JSON array. No prose, no explanations, no markdown.

STRICT OUTPUT RULES:
1. Your entire response must be a valid JSON array starting with [ and ending with ]
2. Do NOT wrap the JSON in markdown code fences (no ```json or ```)
3. Do NOT add any text before or after the JSON array
4. Every string value must use double quotes, not single quotes
5. Do NOT use trailing commas after the last item in an array or object
6. All string values must be plain text with no markdown (no *, **, #, etc.)
<|eot_id|>"""

        user_prompt = f"""<|start_header_id|>user<|end_header_id|>
Based on this {genre} story synopsis, identify all worldbuilding elements:

SYNOPSIS:
{self.smart_trim(synopsis, total_budget - 400)}

For each element, return a JSON object with EXACTLY these keys:
- "name": string (element name)
- "element_type": string (one of: "setting", "location", "event", "system", "item", "other")
- "description": string (what it is, 2-3 sentences, plain text)
- "sensory_details": string (visual/auditory/atmospheric details, 1-2 sentences, plain text)
- "significance": string (why it matters, plain text)

EXAMPLE of correct format:
[{{"name": "The Dark Forest", "element_type": "location", "description": "A vast ancient woodland.", "sensory_details": "Towering oaks with twisted branches.", "significance": "Where the protagonist discovers the truth."}}]

Return the JSON array now:
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
["""
        
        try:
            with self.lock:
                output = self.llm(system_prompt + user_prompt, max_tokens=max_output_tokens, 
                                 stop=["<|eot_id|>"], echo=False, temperature=0.7)
            
            raw_text = output['choices'][0]['text'].strip()
            elements = safe_parse_json(raw_text, expected_type="array", prepend="[")
            
            if not elements or not isinstance(elements, list):
                logging.warning(f"World generation returned no parseable data. Raw: {raw_text[:300]}")
                return []
            
            def to_str(val):
                if isinstance(val, list):
                    return ', '.join(str(v) for v in val)
                return str(val).strip() if val else ''
            
            cleaned = []
            for elem in elements:
                if isinstance(elem, dict) and elem.get('name'):
                    cleaned.append({
                        'name': to_str(elem.get('name', '')),
                        'element_type': to_str(elem.get('element_type', 'other')),
                        'description': to_str(elem.get('description', '')),
                        'sensory_details': to_str(elem.get('sensory_details', '')),
                        'significance': to_str(elem.get('significance', '')),
                        'is_visible': 1
                    })
            
            logging.info(f"Generated {len(cleaned)} world elements from synopsis")
            return cleaned
        except Exception as e:
            logging.error(f"World generation error: {e}", exc_info=True)
            return []

    def generate_single_world_element(self, description: str, element_type: str = "location", genre: str = "fiction") -> dict:
        """Generate a complete world element from a simple description prompt."""
        if not self.llm:
            return {"error": "AI Model not loaded."}
        
        if not description.strip():
            return {"error": "Description cannot be empty."}

        max_output_tokens = 1200
        
        type_descriptions = {
            'setting': 'a world setting or environment',
            'location': 'a specific location or place',
            'event': 'a historical or significant event',
            'system': 'a system (magic, political, economic, etc.)',
            'item': 'an important item or artifact',
            'other': 'a worldbuilding element'
        }
        type_desc = type_descriptions.get(element_type, 'a worldbuilding element')
        
        system_prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a creative worldbuilding expert for fiction stories.
You output ONLY valid JSON objects. No prose, no explanations, no markdown.

STRICT OUTPUT RULES:
1. Your entire response must be a single valid JSON object starting with { and ending with }
2. Do NOT wrap the JSON in markdown code fences (no ```json or ```)
3. Do NOT add any text, commentary, or explanation before or after the JSON
4. Every string value must use double quotes, not single quotes
5. Do NOT use trailing commas after the last key-value pair
6. All string values must be plain text with no markdown decoration (no *, **, #, etc.)
7. Do NOT include newlines inside string values
<|eot_id|>"""

        user_prompt = f"""<|start_header_id|>user<|end_header_id|>
Create a worldbuilding element for a {genre} story based on: "{description}"
This should be {type_desc}.

Return ONLY a JSON object with these exact keys:
{{
  "name": "a fitting name",
  "element_type": "{element_type}",
  "description": "detailed description 3-4 sentences plain text",
  "sensory_details": "sensory details 2-3 sentences plain text",
  "significance": "story importance 2-3 sentences plain text",
  "custom_traits": "additional unique properties plain text"
}}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
{{"""
        
        try:
            logging.info(f"Generating single world element for: {description}")
            with self.lock:
                output = self.llm(system_prompt + user_prompt, max_tokens=max_output_tokens, 
                                 stop=["<|eot_id|>", "```"], echo=False, temperature=0.8)
            
            raw_text = output['choices'][0]['text'].strip()
            logging.debug(f"Raw AI output for single world element: {raw_text}")

            element = safe_parse_json(raw_text, expected_type="object", prepend="{")
            
            if not element or not isinstance(element, dict):
                logging.error(f"Failed to parse world element JSON. Raw: {raw_text[:300]}")
                return {"error": "Failed to parse AI response as JSON"}
            
            def to_str(val):
                if isinstance(val, list):
                    return ', '.join(str(v) for v in val)
                return str(val).strip() if val else ''
            
            return {
                'name': to_str(element.get('name', 'Unnamed Element')),
                'element_type': to_str(element.get('element_type', element_type)),
                'description': to_str(element.get('description', '')),
                'sensory_details': to_str(element.get('sensory_details', '')),
                'significance': to_str(element.get('significance', '')),
                'custom_traits': to_str(element.get('custom_traits', '')),
                'is_visible': 1
            }
        except Exception as e:
            logging.error(f"Single world element generation error: {e}", exc_info=True)
            return {"error": f"An unexpected error occurred: {e}"}

    def generate_synopsis(self, story_elements: str, genre: str = "fiction", target_words: str = "300-500") -> str:
        """Generate a complete synopsis from structured story elements."""
        if not self.llm:
            return {"error": "AI Model not loaded."}
        
        if not story_elements.strip():
            return {"error": "Story elements cannot be empty."}

        max_output_tokens = 1500
        
        system_prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert story writer and editor specializing in creating compelling synopses.
Given structured story elements, craft a cohesive, engaging synopsis that flows naturally.
Write in third person, present tense. Include emotional stakes and character motivations.

STRICT FORMATTING RULES:
1. Output PLAIN TEXT ONLY. Your response is the synopsis text and nothing else.
2. NEVER use asterisks (*) or double asterisks (**) for emphasis or bold.
3. NEVER use hashtags (#) or any header markers.
4. NEVER use dashes (-) or asterisks (*) as bullet points.
5. NEVER use underscores (_) for emphasis.
6. NEVER use backticks (`), blockquotes (>), or any other markdown syntax.
7. Do NOT include section headers, labels, or titles. Write flowing prose only.
8. Use paragraph breaks for structure. No other formatting.
<|eot_id|>"""

        user_prompt = f"""<|start_header_id|>user<|end_header_id|>
Create a {genre} story synopsis of approximately {target_words} words based on these story elements:

{story_elements}

Write a compelling synopsis that:
1. Opens with a hook that establishes the protagonist and their world
2. Clearly establishes the main conflict and stakes
3. Shows the protagonist's journey and key challenges
4. Builds to a climax
5. Resolves with a satisfying ending
6. Weaves in the theme naturally

IMPORTANT: Write the synopsis as smooth, flowing prose paragraphs. No headers, no bold text, no bullet points, no markdown of any kind. Just plain paragraphs of text.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        
        try:
            logging.info(f"Generating synopsis for genre: {genre}, target words: {target_words}")
            with self.lock:
                output = self.llm(system_prompt + user_prompt, max_tokens=max_output_tokens, 
                                 stop=["<|eot_id|>"], echo=False, temperature=0.7)
            
            synopsis = output['choices'][0]['text'].strip()
            synopsis = strip_markdown(synopsis)
            
            logging.debug(f"Generated synopsis: {synopsis[:200]}...")
            
            return synopsis
        except Exception as e:
            logging.error(f"Synopsis generation error: {e}")
            return {"error": f"Failed to generate synopsis: {e}"}

    def generate_outline_from_synopsis(self, synopsis: str, chapter_count: int = 10, genre: str = "fiction") -> list:
        """Generate a chapter outline from a synopsis as structured JSON array."""
        if not self.llm:
            return []
        
        max_output_tokens = 3500
        total_budget = self.context_size - max_output_tokens - 250
        
        system_prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a story structure expert creating detailed chapter outlines.
Given a synopsis, break it down into a logical chapter structure with rich, detailed summaries.
You MUST output ONLY a valid JSON array. No prose, no explanations, no markdown.

STRICT OUTPUT RULES:
1. Your entire response must be a valid JSON array starting with [ and ending with ]
2. Do NOT wrap the JSON in markdown code fences (no ```json or ```)
3. Do NOT add any text before or after the JSON array
4. Every string value must use double quotes, not single quotes
5. Do NOT use trailing commas after the last item in an array or object
6. All string values must be plain text with no markdown (no *, **, #, etc.)
7. Each chapter object has EXACTLY three keys: chapter_number, title, summary
8. IMPORTANT: The summary must be a DETAILED paragraph (5-8 sentences) that serves as a complete blueprint for writing the chapter. Include: opening scene setup, all major plot events in order, character motivations and emotional arcs, important dialogue or confrontations, key decisions or turning points, and how the chapter ends or transitions to the next
9. Group related story beats into the same chapter so the outline flows logically
<|eot_id|>"""

        user_prompt = f"""<|start_header_id|>user<|end_header_id|>
Based on this {genre} story synopsis, create a {chapter_count}-chapter outline as a JSON array:

SYNOPSIS:
{self.smart_trim(synopsis, total_budget - 800)}

Each chapter object must have EXACTLY these 3 keys:
- "chapter_number": integer (1, 2, 3, etc.)
- "title": string (a compelling chapter title)
- "summary": string (a DETAILED paragraph of 5-8 sentences that covers EVERYTHING needed to write this chapter)

The summary for each chapter MUST include:
- The opening scene or situation
- Every major plot event that occurs, in order
- Which characters are involved and what drives them
- Key conflicts, confrontations, or revelations
- Emotional beats and character development
- How the chapter concludes and connects to the next

Group related story beats together so chapters flow logically from one to the next.

EXAMPLE of correct format:
[{{"chapter_number": 1, "title": "The Awakening", "summary": "The chapter opens with Elena cleaning out her late grandmother's house on a rainy autumn afternoon, reflecting on childhood memories. While sorting through boxes in the attic, she discovers a sealed envelope hidden behind a loose floorboard, addressed to her in her grandmother's handwriting. The letter reveals that Elena's grandfather was not who the family believed him to be, and that a second family exists across the country. Shocked and angry, Elena drives to her mother's house and confronts her, demanding the truth. Her mother breaks down and confirms the secret, explaining she kept it hidden to protect Elena from the pain. Elena feels betrayed by the years of silence but also begins to feel a deep curiosity about the relatives she never knew existed. The chapter ends with Elena booking a flight, determined to find her grandfather's other family and piece together the full story."}}]

Return the JSON array now:
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
["""
        
        try:
            with self.lock:
                output = self.llm(system_prompt + user_prompt, max_tokens=max_output_tokens, 
                                 stop=["<|eot_id|>"], echo=False, temperature=0.7)
            
            raw_output = output['choices'][0]['text'].strip()
            chapters = safe_parse_json(raw_output, expected_type="array", prepend="[")
            
            if not chapters or not isinstance(chapters, list):
                logging.warning(f"Outline JSON parse failed, trying text fallback. Raw: {raw_output[:300]}")
                return self._parse_outline_text_to_json(raw_output, chapter_count)
            
            def to_str(val):
                if isinstance(val, list):
                    return ', '.join(str(v) for v in val)
                return str(val).strip() if val is not None else ''
            
            cleaned = []
            for i, ch in enumerate(chapters):
                if isinstance(ch, dict):
                    cleaned.append({
                        'chapter_number': ch.get('chapter_number', i + 1),
                        'title': to_str(ch.get('title', f'Chapter {i + 1}')),
                        'summary': to_str(ch.get('summary', ''))
                    })
            
            return cleaned
        except Exception as e:
            logging.error(f"Outline generation error: {e}", exc_info=True)
            if 'raw_output' in locals():
                return self._parse_outline_text_to_json(raw_output, chapter_count)
            return []

    def _parse_outline_text_to_json(self, text: str, chapter_count: int) -> list:
        """Fallback: Parse plain text outline into structured JSON."""
        import re
        chapters = []
        
        pattern = r'(?:Chapter\s*)?(\d+)[:\.\)]\s*([^\n]+)\n((?:(?!(?:Chapter\s*)?\d+[:\.\)]).)*)' 
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if matches:
            for match in matches:
                num, title, summary = match
                chapters.append({
                    'chapter_number': int(num),
                    'title': title.strip(),
                    'summary': summary.strip()
                })
        else:
            parts = text.split('\n\n')
            for i, part in enumerate(parts[:chapter_count]):
                if part.strip():
                    lines = part.strip().split('\n')
                    title = lines[0] if lines else f'Chapter {i + 1}'
                    summary = '\n'.join(lines[1:]) if len(lines) > 1 else ''
                    chapters.append({
                        'chapter_number': i + 1,
                        'title': title.strip(),
                        'summary': summary.strip()
                    })
        
        return chapters if chapters else [{'chapter_number': 1, 'title': 'Chapter 1', 'summary': text[:500]}]

    def update_chapter_summary(self, chapter_content: str) -> str:
        """Generate/update a summary for a chapter."""
        if not self.llm:
            return ""
        
        max_output_tokens = 300
        total_budget = self.context_size - max_output_tokens - 250
        
        system_prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a literary assistant creating concise chapter summaries.
Focus on plot events, character actions, and important developments.
<|eot_id|>"""

        user_prompt = f"""<|start_header_id|>user<|end_header_id|>
Summarize this chapter in 2-3 sentences, focusing on key plot events and character actions:

CHAPTER CONTENT:
{self.smart_trim(chapter_content, total_budget - 200)}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        
        try:
            with self.lock:
                output = self.llm(system_prompt + user_prompt, max_tokens=max_output_tokens, 
                                 stop=["<|eot_id|>"], echo=False, temperature=0.5)
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"Chapter summary error: {e}")
            return ""

    def generate_chapter_summary(self, chapter_number: int, chapter_title: str, 
                                  synopsis: str, genre: str = "fiction",
                                  custom_instructions: str = "",
                                  existing_outline: str = "") -> dict:
        """Generate a summary for a single chapter using story context.
        
        Args:
            chapter_number: The chapter number
            chapter_title: The chapter title
            synopsis: The story synopsis or braindump
            genre: The story genre
            custom_instructions: Optional user guidance for tone, pacing, events
            existing_outline: Context from other chapters for continuity
        """
        if not self.llm:
            return {"error": "AI Model not loaded."}
        
        max_output_tokens = 800
        total_budget = self.context_size - max_output_tokens - 250
        
        instructions_block = ""
        if custom_instructions and custom_instructions.strip():
            instructions_block = f"\nCUSTOM INSTRUCTIONS FROM THE WRITER:\n{custom_instructions.strip()}\nFollow these instructions carefully when writing the chapter summary.\n"
        
        outline_block = ""
        if existing_outline and existing_outline.strip():
            outline_block = f"\nEXISTING OUTLINE (other chapters for continuity):\n{self.smart_trim(existing_outline, 800)}\n"
        
        system_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a story structure expert writing detailed chapter summaries for a {genre} story.

STRICT FORMATTING RULES:
1. Output PLAIN TEXT ONLY.
2. NEVER use asterisks (*), double asterisks (**), hashtags (#), or any markdown.
3. Write a DETAILED paragraph of 5-8 sentences that serves as a complete blueprint for writing this chapter.
4. Include: the opening scene, all major plot events in order, character motivations, key conflicts or revelations, emotional beats, and how the chapter ends.
5. NO conversational fluff, NO labels, NO headers. Just the detailed summary paragraph.
<|eot_id|>"""

        user_prompt = f"""<|start_header_id|>user<|end_header_id|>
STORY CONTEXT:
{self.smart_trim(synopsis, total_budget - 500)}
{outline_block}{instructions_block}
Write a detailed summary for Chapter {chapter_number}: "{chapter_title}"

The summary must be a rich, detailed paragraph (5-8 sentences) that covers everything needed to write this chapter:
- How the chapter opens
- Every major plot event in sequence
- Which characters are involved and their motivations
- Key conflicts, confrontations, or revelations
- Emotional arcs and character development
- How the chapter ends and transitions to the next
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        
        try:
            logging.info(f"Generating summary for Chapter {chapter_number}: {chapter_title}")
            with self.lock:
                output = self.llm(system_prompt + user_prompt, max_tokens=max_output_tokens, 
                                 stop=["<|eot_id|>"], echo=False, temperature=0.7)
            
            result = output['choices'][0]['text'].strip()
            result = strip_markdown(result)
            return {"summary": result}
        except Exception as e:
            logging.error(f"Chapter summary generation error: {e}", exc_info=True)
            return {"error": f"Failed to generate chapter summary: {str(e)}"}

    def expand_scene_from_summary(self, scene_summary: str, context: str = "", genre: str = "fiction") -> str:
        """Expand a scene summary into full prose."""
        if not self.llm:
            return ""
        
        max_output_tokens = 1000
        total_budget = self.context_size - max_output_tokens - 250
        
        system_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a professional {genre} author expanding scene summaries into vivid prose.
Write in third person limited POV with a mix of dialogue, action, and description.
<|eot_id|>"""

        context_section = ""
        if context:
            context_section = f"\nPREVIOUS CONTEXT:\n{self.smart_trim(context, int(total_budget * 0.3))}\n"

        user_prompt = f"""<|start_header_id|>user<|end_header_id|>
{context_section}
Expand this scene summary into full prose:

SCENE SUMMARY:
{self.smart_trim(scene_summary, int(total_budget * 0.4))}

Write 3-4 paragraphs of vivid narrative prose:
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        
        try:
            with self.lock:
                output = self.llm(system_prompt + user_prompt, max_tokens=max_output_tokens, 
                                 stop=["<|eot_id|>"], echo=False, temperature=0.8)
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"Scene expansion error: {e}")
            return ""

    def expand_scene_with_context(self, scene_summary: str, context: str = "",
                                   genre: str = "fiction", style: str = "",
                                   characters: str = "", worldbuilding: str = "",
                                   chapter_outline: str = "",
                                   extra_instructions: str = "") -> str:
        """Expand a scene summary into full prose using rich Story Bible context.
        
        Uses tiered token budgeting to fit as much context as possible:
          Tier 1 (40%): Scene summary
          Tier 2 (15%): Style + Genre (shapes prose voice)
          Tier 3 (15%): Characters relevant to scene
          Tier 4 (15%): Previous scene context (continuity)
          Tier 5 (10%): Chapter outline summary
          Tier 6 (5%):  Worldbuilding
        """
        if not self.llm:
            return ""

        max_output_tokens = 1200
        system_overhead = 300
        total_budget = self.context_size - max_output_tokens - system_overhead

        budget_scene       = int(total_budget * 0.40)
        budget_style       = int(total_budget * 0.15)
        budget_characters  = int(total_budget * 0.15)
        budget_prev        = int(total_budget * 0.15)
        budget_outline     = int(total_budget * 0.10)
        budget_world       = int(total_budget * 0.05)

        trimmed_scene      = self.smart_trim(scene_summary, budget_scene, keep_start=True)
        trimmed_style      = self.smart_trim(style, budget_style, keep_start=True) if style else ""
        trimmed_characters = self.smart_trim(characters, budget_characters, keep_start=True) if characters else ""
        trimmed_prev       = self.smart_trim(context, budget_prev, keep_start=False) if context else ""
        trimmed_outline    = self.smart_trim(chapter_outline, budget_outline, keep_start=True) if chapter_outline else ""
        trimmed_world      = self.smart_trim(worldbuilding, budget_world, keep_start=True) if worldbuilding else ""

        style_instruction = ""
        if trimmed_style:
            style_instruction = f"\nWRITING STYLE: {trimmed_style}"
        if genre and genre.strip().lower() != "fiction":
            style_instruction += f"\nGENRE: {genre}"

        system_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a professional author expanding scene summaries into vivid, publication-quality prose.{style_instruction}

STRICT FORMATTING RULES:
1. Output ONLY narrative prose. No markdown, no asterisks, no headers, no labels.
2. Write 3-5 paragraphs with a mix of dialogue, action, internal thought, and sensory description.
3. Stay faithful to the scene summary. Do not invent major plot events not described.
4. Use character names, traits, and speech patterns from the provided character details.
5. Reflect the worldbuilding details naturally within the narrative.
<|eot_id|>"""

        user_sections = []

        if trimmed_outline:
            user_sections.append(f"CHAPTER CONTEXT:\n{trimmed_outline}")

        if trimmed_characters:
            user_sections.append(f"CHARACTERS IN THIS SCENE:\n{trimmed_characters}")

        if trimmed_world:
            user_sections.append(f"WORLDBUILDING:\n{trimmed_world}")

        if trimmed_prev:
            user_sections.append(f"PREVIOUS SCENE (for continuity):\n{trimmed_prev}")

        user_sections.append(f"SCENE TO EXPAND:\n{trimmed_scene}")

        extra = ""
        if extra_instructions and extra_instructions.strip():
            extra = f"\n\nWRITER'S INSTRUCTIONS: {extra_instructions.strip()}"

        user_prompt = f"""<|start_header_id|>user<|end_header_id|>
{chr(10).join(user_sections)}{extra}

Expand the scene into vivid narrative prose:
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

        try:
            logging.info(f"Expanding scene with context (budget={total_budget}, "
                         f"style={len(trimmed_style)}t, chars={len(trimmed_characters)}t, "
                         f"world={len(trimmed_world)}t, outline={len(trimmed_outline)}t)")
            with self.lock:
                output = self.llm(system_prompt + user_prompt, max_tokens=max_output_tokens,
                                  stop=["<|eot_id|>"], echo=False, temperature=0.8)
            result = output['choices'][0]['text'].strip()
            return strip_markdown(result)
        except Exception as e:
            logging.error(f"Scene expansion with context error: {e}", exc_info=True)
            return ""

    def generate_bible_section(self, section_key: str, project_id: int, db_manager) -> str:
        """Generate content for a Story Bible section using hierarchical context.
        
        Hierarchy:
          - synopsis: primary=braindump, secondary=genre+style
          - outline/characters/worldbuilding: primary=synopsis (fallback=braindump), secondary=genre
        
        Args:
            section_key: The bible section to generate (synopsis, outline, worldbuilding, characters)
            project_id: The project ID to gather context from
            db_manager: Database manager instance to fetch context
            
        Returns:
            Generated content string, or error dict if failed
        """
        if not self.llm:
            return {"error": "AI Model not loaded."}
        
        if section_key not in PROMPTS:
            return {"error": f"Unknown section: {section_key}"}
        
        try:
            projects = db_manager.get_projects()
            project_name = "Untitled Project"
            for p in projects:
                if p.get('id') == project_id:
                    project_name = p.get('name', 'Untitled Project')
                    break
            
            bible_data = db_manager.get_story_bible(project_id) or {}
            
            characters_list = db_manager.get_characters(project_id) or []
            character_summaries = []
            for char in characters_list[:10]:
                char_str = f"- {char.get('name', 'Unknown')}"
                if char.get('role'):
                    char_str += f" ({char.get('role')})"
                if char.get('personality_traits'):
                    char_str += f": {char.get('personality_traits', '')[:100]}"
                character_summaries.append(char_str)
            characters_text = "\n".join(character_summaries) if character_summaries else "No characters defined yet."
            
            # Determine primary source and label based on hierarchy
            primary_source = ""
            primary_source_label = "Story Context"
            
            if section_key == 'synopsis':
                braindump = bible_data.get('braindump', '').strip()
                if not braindump:
                    return {"error": "Please write your Braindump first. The Synopsis is generated from your braindump ideas."}
                primary_source = braindump
                primary_source_label = "Braindump"
            elif section_key in ('outline', 'characters', 'worldbuilding'):
                synopsis = bible_data.get('synopsis', '').strip()
                braindump = bible_data.get('braindump', '').strip()
                if synopsis:
                    primary_source = synopsis
                    primary_source_label = "Synopsis"
                elif braindump:
                    primary_source = braindump
                    primary_source_label = "Braindump (fallback — no Synopsis available)"
                else:
                    return {"error": "Please write a Synopsis or Braindump first."}
            
            # Truncate primary source if very long
            if len(primary_source) > 2000:
                primary_source = primary_source[:2000] + "..."
            
            # Build secondary context (other sections, excluding the one we're generating and the primary source)
            # Style only affects prose/draft generation, NOT synopsis or structural sections
            secondary_keys = []
            if section_key == 'synopsis':
                secondary_keys = ['genre']
            elif section_key == 'outline':
                secondary_keys = ['genre', 'worldbuilding']
            elif section_key == 'characters':
                secondary_keys = ['genre', 'worldbuilding']
            elif section_key == 'worldbuilding':
                secondary_keys = ['genre']
            
            bible_context_parts = []
            for key in secondary_keys:
                if key != section_key and bible_data.get(key):
                    ctx = bible_data[key]
                    if key == 'outline':
                        try:
                            outline_data = json.loads(ctx) if isinstance(ctx, str) else ctx
                            if isinstance(outline_data, list):
                                outline_lines = []
                                for ch in outline_data[:5]:
                                    if isinstance(ch, dict):
                                        outline_lines.append(f"Ch{ch.get('chapter_number', '?')}: {ch.get('title', 'Untitled')} - {ch.get('summary', '')[:100]}")
                                ctx = "\n".join(outline_lines)
                        except:
                            pass
                    if len(ctx) > 500:
                        ctx = ctx[:500] + "..."
                    bible_context_parts.append(f"[{key.upper()}]\n{ctx}")
            
            bible_context = "\n\n".join(bible_context_parts) if bible_context_parts else "No additional context available."
            
            canvas_content = ""
            try:
                chapters = db_manager.get_chapters(project_id) or []
                if chapters:
                    for ch in chapters:
                        ch_content = db_manager.get_chapter_content(ch['id'])
                        if ch_content and ch_content.strip():
                            canvas_content = ch_content[:1000] + "..." if len(ch_content) > 1000 else ch_content
                            break
            except Exception as e:
                logging.warning(f"Could not fetch chapter content for bible generation: {e}")
            
            if not canvas_content:
                canvas_content = "No chapter content written yet."
            
            genre = bible_data.get('genre', 'fiction')
            if not genre or len(genre) > 50:
                genre = 'fiction'
            
            full_prompt = get_bible_prompt(
                section_key=section_key,
                title=project_name,
                characters=characters_text,
                bible_context=bible_context,
                canvas_content=canvas_content,
                genre=genre,
                primary_source=primary_source,
                primary_source_label=primary_source_label,
            )
            
            if not full_prompt:
                return {"error": f"Failed to build prompt for section: {section_key}"}
            
            max_output_tokens = 800
            if section_key == 'synopsis':
                max_output_tokens = 1200
            elif section_key == 'outline':
                max_output_tokens = 1500
            
            logging.info(f"Generating bible section '{section_key}' for project {project_id} (primary: {primary_source_label})")
            
            with self.lock:
                output = self.llm(full_prompt, max_tokens=max_output_tokens, 
                                 stop=["<|eot_id|>"], echo=False, temperature=0.7)
            
            result = output['choices'][0]['text'].strip()
            result = strip_markdown(result)
            
            logging.info(f"Generated {len(result)} chars for bible section '{section_key}'")
            
            return result
            
        except Exception as e:
            logging.error(f"Bible section generation error ({section_key}): {e}", exc_info=True)
            return {"error": f"Failed to generate {section_key}: {str(e)}"}
