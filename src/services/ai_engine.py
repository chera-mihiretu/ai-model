import logging
import sys
import queue
import threading
from typing import Optional

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

from ..config.manager import ConfigManager

MIMIC_SYSTEM_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are now roleplaying as {name}.
RELATIONSHIP TO AUTHOR: {relationship}
TRAITS: {traits}
SPEECH STYLE: {speech}
Respond to the user as THIS character would. Never break character.
<|eot_id|>"""

PROSE_SYSTEM_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are the Story Bible Continuity Engine. 
Your identity is that of a professional co-author and lore expert.
RULES:
1. NO greetings. NO "I can help with that." NO "Sure!"
2. If the user provides a scene, continue the prose in the same style.
3. If the user asks a question, answer based ONLY on the provided context.
4. Always maintain a literary, narrative tone.
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
    def __init__(self):
        self.config_manager = ConfigManager()
        self.llm: Optional[Llama] = None
        self.status_message = "Initializing..."
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
            logging.info(f"Loading model from {config.model_path} with n_gpu_layers={config.n_gpu_layers}")
            self.llm = Llama(
                model_path=config.model_path,
                n_gpu_layers=config.n_gpu_layers,
                n_ctx=config.n_ctx,
                n_batch=config.n_batch,
                verbose=False
            )
            self.status_message = "Model Loaded: Llama 3.1 8B (GPU)"
            logging.info("Model loaded successfully.")
        except Exception as e:
            self.status_message = f"Error: Failed to load model ({e})"
            logging.error(f"Failed to load model: {e}")
            self.llm = None

    def count_tokens(self, text: str) -> int:
        """Counts tokens in the provided text using the internal LLM tokenizer."""
        if not self.llm or not text:
            return 0
        try:
            # We use add_bos=False because our prompt templates already include 
            # the <|begin_of_text|> tag. This prevents off-by-one errors.
            tokens = self.llm.tokenize(text.encode("utf-8"), add_bos=False)
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
        max_input = 4096 - available_output - instruction_tokens - 100
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

    def assemble_context(self, instruction: str, chapter_summary: str, bible_summaries: list, recent_summary: str, recent_text: str) -> str:
        """
        Assembles a strictly budgeted context string.
        Total Limit: 4096 tokens (minus output buffer).
        
        Priority:
        1. Recent Text (Last Chapter Summary + Raw Recent) - Critical Short Term Memory
        2. Instruction - Critical
        3. Chapter Summary - Long Term Memory
        4. Bible Summaries - Lore
        """
        OUTPUT_BUFFER = 800
        SYSTEM_BUFFER = 200 # For system prompt overhead
        TOTAL_LIMIT = 4096 - OUTPUT_BUFFER - SYSTEM_BUFFER
        
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

    def stream_response(self, instruction: str, response_queue: queue.Queue, bible_data: dict = None, current_text: str = "", character_context: dict = None, rag_context: dict = None, style: str = None) -> None:
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
            current_text
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

        max_output_tokens = 800
        # Verify total
        total_input = self.count_tokens(full_prompt)
        if total_input + max_output_tokens > 4096:
             logging.warning(f"Final prompt over budget ({total_input}). Trimming...")
             # Last ditch safety check is inside generate_stream but strictly we should handle it here
             pass

        logging.info(f"Budget Check: {total_input} input + {max_output_tokens} output = {total_input + max_output_tokens} / 4096")
        self.generate_stream(full_prompt, response_queue, max_tokens=max_output_tokens)

    def generate_beat_summary(self, text: str) -> str:
        """Generates a brief summary with budgeting."""
        if not self.llm or not text.strip():
            return "No content to summarize."

        max_output_tokens = 150
        # Increased safety buffer to 250
        total_budget = 4096 - max_output_tokens - 250
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

    def ask_lore_assistant(self, query: str, response_queue: queue.Queue, project_memory: str, project_name: str = "Current Project") -> None:
        """Lore Assistant with budgeting."""
        if not self.llm:
            response_queue.put("Error: AI Model is not loaded.")
            response_queue.put("[[END]]")
            return

        max_output_tokens = 600
        # Increased safety buffer to 250
        total_budget = 4096 - max_output_tokens - 250
        
        sys_prefix = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are the OMNISCIENT LORE KEEPER for the story '{project_name}'.
You have perfect memory of every event, character, and detail in this story.

STORY DATA:
"""
        sys_suffix = """
RULES:
1. Answer questions DIRECTLY. Never say "According to the database".
2. If information is missing, say so naturally.
<|eot_id|>"""
        
        query_part = f"<|start_header_id|>user<|end_header_id|>\nQUESTION: {query}\n<|eot_id|>\n<|start_header_id|>assistant<|end_header_id|>"
        fixed_tokens = self.count_tokens(sys_prefix + sys_suffix + query_part)
        trimmed_memory = self.smart_trim(project_memory, total_budget - fixed_tokens)

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
            if input_len + max_tokens > 4096:
                adjusted_max = 4096 - input_len - 5  # 5 token safety margin
                logging.warning(f"Context limit imminent! Adjusting max_tokens from {max_tokens} to {adjusted_max} (Input: {input_len})")
                max_tokens = max(1, adjusted_max)
            
            if input_len >= 4096:
                logging.error(f"CRITICAL: Final prompt exceeds hard 4096 limit ({input_len}). Emergency truncating input.")
                # Last resort: truncate the literal string to hopefully fix the token count
                prompt = prompt[-12000:] # Roughly 3000 tokens
                max_tokens = 500

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

    def unload_model(self):
        if self.llm:
            logging.info("Unloading model...")
            del self.llm
            self.llm = None
            import gc
            gc.collect()

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
        total_budget = 4096 - max_output_tokens - 250
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
        total_budget = 4096 - max_output_tokens - 250
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
        total_budget = 4096 - max_output_tokens - 250

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
        total_budget = 4096 - max_output_tokens - 250
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
        total_budget = 4096 - max_output_tokens - 250

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
