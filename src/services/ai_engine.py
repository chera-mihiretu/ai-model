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

    def get_genre_context(self, genre: str) -> dict:
        """
        Generate genre-specific context for AI prompt conditioning.
        Returns dict with archetypes, conflicts, tone guidelines, and elements to avoid.
        """
        # Normalize genre input
        genre_lower = genre.lower().strip() if genre else "general fiction"
        
        # Genre-specific context mapping
        genre_contexts = {
            "fantasy": {
                "genre": "Fantasy",
                "archetypes": ["Hero", "Mentor", "Villain", "Sidekick", "Oracle"],
                "common_conflicts": ["Quest", "Political Intrigue", "War", "Prophecy", "Magic vs Technology"],
                "tone_guidelines": "Epic, adventurous, and high-stakes. Emphasize wonder and magic.",
                "avoid_elements": ["Modern technology", "Contemporary slang", "Scientific explanations"],
                "narrative_elements": ["Magic systems", "Kingdoms", "Ancient prophecies", "Mythical creatures"],
                "style_notes": "Use archaic or elevated language when appropriate. Focus on worldbuilding and lore."
            },
            "sci-fi": {
                "genre": "Science Fiction",
                "archetypes": ["Scientist", "Explorer", "AI/Robot", "Rebel", "Visionary"],
                "common_conflicts": ["Technological advancement", "Space exploration", "AI uprising", "Dystopian control"],
                "tone_guidelines": "Intellectual, speculative, and forward-thinking. Emphasize innovation and discovery.",
                "avoid_elements": ["Magic without scientific basis", "Fantasy creatures", "Medieval settings"],
                "narrative_elements": ["Advanced technology", "Space travel", "Scientific concepts", "Future societies"],
                "style_notes": "Ground fantastical elements in plausible science. Use technical vocabulary appropriately."
            },
            "romance": {
                "genre": "Romance",
                "archetypes": ["Lover", "Best Friend", "Rival", "Confidant"],
                "common_conflicts": ["Forbidden love", "Misunderstanding", "Class differences", "Love triangle"],
                "tone_guidelines": "Emotional, intimate, and tension-filled. Focus on character chemistry.",
                "avoid_elements": ["Excessive violence", "Political intrigue overshadowing relationships"],
                "narrative_elements": ["Emotional beats", "Relationship development", "Internal conflicts"],
                "style_notes": "Emphasize emotional depth, attraction, and interpersonal dynamics."
            },
            "thriller": {
                "genre": "Thriller",
                "archetypes": ["Detective", "Victim", "Antagonist", "Ally", "Red Herring"],
                "common_conflicts": ["Investigation", "Chase", "Conspiracy", "Psychological manipulation"],
                "tone_guidelines": "Suspenseful, tense, and fast-paced. Build dread and anticipation.",
                "avoid_elements": ["Slow pacing", "Comedic relief that breaks tension"],
                "narrative_elements": ["Clues", "Red herrings", "Time pressure", "High stakes"],
                "style_notes": "Use short, punchy sentences for action. Build suspense through pacing."
            },
            "mystery": {
                "genre": "Mystery",
                "archetypes": ["Detective", "Suspect", "Witness", "Victim", "Investigator"],
                "common_conflicts": ["Solving crime", "Uncovering secrets", "Following clues"],
                "tone_guidelines": "Intriguing, methodical, and cerebral. Encourage reader deduction.",
                "avoid_elements": ["Deus ex machina solutions", "Unearned revelations"],
                "narrative_elements": ["Clues", "Misdirection", "Logical deduction", "Plot twists"],
                "style_notes": "Plant clues fairly. Build logical progression of discovery."
            },
            "horror": {
                "genre": "Horror",
                "archetypes": ["Final Girl/Boy", "Monster", "Skeptic", "Believer", "Victim"],
                "common_conflicts": ["Survival", "Unknown threat", "Psychological breakdown"],
                "tone_guidelines": "Dreadful, atmospheric, and visceral. Build terror and unease.",
                "avoid_elements": ["Excessive humor", "Safe, predictable outcomes"],
                "narrative_elements": ["Atmosphere", "Gore/violence", "Psychological terror", "Isolation"],
                "style_notes": "Use sensory details to build dread. Pace revelations carefully."
            }
        }
        
        # Find matching genre (fuzzy match)
        for key, context in genre_contexts.items():
            if key in genre_lower or genre_lower in key:
                return context
        
        # Default/general fiction context
        return {
            "genre": genre or "General Fiction",
            "archetypes": ["Protagonist", "Antagonist", "Supporting Character"],
            "common_conflicts": ["Character vs Self", "Character vs Character", "Character vs Society"],
            "tone_guidelines": "Balanced and narrative-focused. Adapt to story needs.",
            "avoid_elements": [],
            "narrative_elements": ["Plot development", "Character arcs", "Theme exploration"],
            "style_notes": "Maintain consistency with established tone and voice."
        }

    def stream_response(self, instruction: str, response_queue: queue.Queue, bible_data: str = "", current_text: str = "", character_context: dict = None, rag_context: dict = None, genre: str = None) -> None:
        """
        Streams response tokens into the provided queue.
        Uses Llama 3 Header format.
        If rag_context is provided, uses God-Mode Writer prompt for context-aware generation.
        """
        if not self.llm:
            response_queue.put("Error: AI Model is not loaded check logs.")
            response_queue.put("[[END]]")
            return

        # RAG-Enhanced Writing (God-Mode)
        if rag_context:
            # Build character notes string
            char_notes = ""
            if rag_context.get('mentioned_characters'):
                for char in rag_context['mentioned_characters']:
                    char_notes += f"\n- {char.get('name')}: {char.get('personality_traits', '')}\n  Speech: {char.get('speech_pattern', '')}"
            else:
                char_notes = "No characters mentioned in recent text."
            
            # Get genre context
            genre_name = genre or rag_context.get('genre', 'fiction')
            genre_ctx = self.get_genre_context(genre_name)
            
            # Build genre guidance string
            genre_guidance = f"""
GENRE: {genre_ctx['genre']}
TONE: {genre_ctx['tone_guidelines']}
APPROPRIATE ELEMENTS: {', '.join(genre_ctx['narrative_elements'])}
AVOID: {', '.join(genre_ctx['avoid_elements']) if genre_ctx['avoid_elements'] else 'None'}
STYLE NOTES: {genre_ctx['style_notes']}
"""
            
            system_prompt = PROMPT_WRITER_GODMODE.format(
                genre=genre_ctx['genre'],
                character_notes=char_notes,
                prev_summary=rag_context.get('prev_summary', 'Beginning of story'),
                recent_context=rag_context.get('recent_text', current_text[-3000:])
            )
            
            # Append genre guidance to system prompt
            system_prompt = system_prompt.replace("<|eot_id|>", f"{genre_guidance}<|eot_id|>")
            
            full_prompt = (
                f"{system_prompt}"
                f"<|start_header_id|>user<|end_header_id|>\n"
                f"Continue writing:\n"
                f"<|eot_id|>\n"
                f"<|start_header_id|>assistant<|end_header_id|>"
            )
        
        # Standard Writing
        elif character_context:
            system_prompt = MIMIC_SYSTEM_PROMPT.format(
                name=character_context.get('name', 'Unknown'),
                relationship=character_context.get('relationship_to_author', 'None'),
                traits=character_context.get('personality_traits', 'None'),
                speech=character_context.get('speech_pattern', 'Standard')
            )
            
            full_prompt = (
                f"{system_prompt}"
                f"<|start_header_id|>user<|end_header_id|>\n"
                f"BIBLE DATA: {bible_data}\n"
                f"CURRENT TEXT: {current_text}\n"
                f"INSTRUCTION: {instruction}\n"
                f"<|eot_id|>\n"
                f"<|start_header_id|>assistant<|end_header_id|>"
            )
        else:
            system_prompt = PROSE_SYSTEM_PROMPT
            
            full_prompt = (
                f"{system_prompt}"
                f"<|start_header_id|>user<|end_header_id|>\n"
                f"BIBLE DATA: {bible_data}\n"
                f"CURRENT TEXT: {current_text}\n"
                f"INSTRUCTION: {instruction}\n"
                f"<|eot_id|>\n"
                f"<|start_header_id|>assistant<|end_header_id|>"
            )

        self._generate_stream(full_prompt, response_queue)



    def generate_beat_summary(self, text: str) -> str:
        """
        Generates a 2-3 sentence summary of the provided text.
        Synchronous call (for background thread).
        """
        if not self.llm or not text.strip():
            return "No content to summarize."

        prompt = (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
            f"Summarize the story chunk in 3 sentences. Focus on plot points.\n"
            f"STRICT OUTPUT FORMAT: Output ONLY the summary. Do NOT say 'Here is a summary'.\n"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"{text[-2500:]}\n"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )

        try:
            with self.lock:
                output = self.llm(
                    prompt,
                    max_tokens=150,
                    stop=["<|eot_id|>"],
                    echo=False,
                    temperature=0.3
                )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"Summary generation error: {e}")
            return "Error generating summary."

    def ask_lore_assistant(self, query: str, response_queue: queue.Queue, project_memory: str, project_name: str = "Current Project") -> None:
        """
        Asks the Lore Assistant a question based on project memory.
        """
        if not self.llm:
            response_queue.put("Error: AI Model is not loaded.")
            response_queue.put("[[END]]")
            return

        system_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are the OMNISCIENT LORE KEEPER for the story '{project_name}'.
You have perfect memory of every event, character, and detail in this story.

STORY DATA:
{project_memory}

RULES:
1. Answer questions DIRECTLY as if you naturally know this information.
2. NEVER say "According to the database" or "Based on the data" or similar phrases.
3. If asked about a character's history, answer naturally (e.g., "Sara's past relationship was with Ron, a toxic and manipulative connection from Chapter 11.")
4. If the author is about to make a continuity mistake, warn them naturally.
5. If information is not in your memory, say "I don't have that information in the story yet."
6. Be the story's memory - confident, direct, and helpful.
<|eot_id|>"""

        full_prompt = (
            f"{system_prompt}"
            f"<|start_header_id|>user<|end_header_id|>\n"
            f"QUESTION: {query}\n"
            f"<|eot_id|>\n"
            f"<|start_header_id|>assistant<|end_header_id|>"
        )
        
        logging.info(f"DEBUG: ask_lore_assistant called. Memory len: {len(project_memory)}")
        self._generate_stream(full_prompt, response_queue)

    def _generate_stream(self, prompt, response_queue):
        try:
            logging.info("Generating AI response...")
            with self.lock:
                stream = self.llm(
                    prompt,
                    max_tokens=None,
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
            logging.error(f"Generation error: {e}")
            response_queue.put(f"\n[Error: {e}]")
            response_queue.put("[[END]]")

    def unload_model(self):
        if self.llm:
            logging.info("Unloading model and freeing VRAM...")
            del self.llm
            self.llm = None
            # Force garbage collection
            import gc
            gc.collect()

    def generate_plugin_response(self, text: str, plugin_type: str, response_queue: queue.Queue, context_data: dict = None) -> None:
        """
        Handles Describe/Rewrite plugins with context injection.
        """
        if not self.llm:
            response_queue.put("Error: AI Model is not loaded.")
            response_queue.put("[[END]]")
            return

        genre = context_data.get('genre', 'General Fiction') if context_data else 'General Fiction'
        char_name = context_data.get('char_name', 'Unknown') if context_data else 'Unknown'
        dossier = context_data.get('dossier', '') if context_data else ''

        system_prompt = PROSE_SYSTEM_PROMPT
        
        if plugin_type.startswith("describe_"):
            sense = plugin_type.replace("describe_", "")
            system_prompt = PROMPT_DESCRIBE_MASTER.format(
                sense=sense.upper(),
                genre=genre,
                character_name=char_name,
                dossier=dossier[:500] 
            )
        elif plugin_type.startswith("rewrite_"):
            style = plugin_type.replace("rewrite_", "").replace("_", " ").title()
            system_prompt = PROMPT_REWRITE_MASTER.format(
                style=style,
                genre=genre
            )
        elif plugin_type == 'sensory_lab':
            system_prompt = PROMPT_SENSORY_LAB

        full_prompt = (
            f"{system_prompt}"
            f"<|start_header_id|>user<|end_header_id|>\n"
            f"{text}\n"
            f"<|eot_id|>\n"
            f"<|start_header_id|>assistant<|end_header_id|>"
        )

        self._generate_stream(full_prompt, response_queue)

    def expand_scene(self, context_text: str, response_queue: queue.Queue) -> None:
        """
        Expands the current scene based on the last 500 words.
        """
        if not self.llm:
            response_queue.put("Error: AI Model is not loaded.")
            response_queue.put("[[END]]")
            return

        full_prompt = (
            f"{PROMPT_EXPAND_SCENE}"
            f"<|start_header_id|>user<|end_header_id|>\n"
            f"PREVIOUS TEXT:\n{context_text[-2500:]}\n" # Approx last 500 words
            f"<|eot_id|>\n"
            f"<|start_header_id|>assistant<|end_header_id|>"
        )

        self._generate_stream(full_prompt, response_queue)

    def check_continuity(self, beats: list, lore_package: dict) -> tuple:
        """
        Pre-generation logic check: validates beats against lore for contradictions.
        Returns: (is_valid: bool, conflict_message: str)
        """
        if not self.llm:
            return (True, "")  # Skip check if model not loaded
        
        # Build lore summary
        char_summary = "\n".join([f"- {c['name']}: {c.get('traits', '')}" for c in lore_package.get('characters', [])])
        story_summary = "\n".join(lore_package.get('story_so_far', []))
        
        prompt = (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
            f"You are a continuity checker. Review the BEATS against the LORE.\n"
            f"Find contradictions: dead characters appearing, teleportation, broken world rules.\n"
            f"Output ONLY 'PASS' or 'CONFLICT: [details]'\n"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"LORE:\n{char_summary}\n\nSTORY: {story_summary}\n\n"
            f"BEATS:\n" + "\n".join([f"{i+1}. {b}" for i, b in enumerate(beats)]) + "\n"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )
        
        try:
            with self.lock:
                output = self.llm(
                    prompt,
                    max_tokens=200,
                    stop=["<|eot_id|>"],
                    echo=False,
                    temperature=0.3
                )
            result = output['choices'][0]['text'].strip()
            
            if result.startswith("CONFLICT"):
                return (False, result.replace("CONFLICT:", "").strip())
            else:
                return (True, "")
                
        except Exception as e:
            logging.error(f"Continuity check error: {e}")
            return (True, "")  # Proceed on error

    def generate_omniscient_prose(self, beats: list, lore_package: dict, response_queue: queue.Queue):
        """
        Generates 1000+ words of prose from beats using omniscient drafting engine.
        """
        if not self.llm:
            response_queue.put("Error: AI Model is not loaded.")
            response_queue.put("[[END]]")
            return
        
        # Format lore package for prompt
        char_text = "\n".join([f"- {c['name']}: {c.get('traits', '')} | Speech: {c.get('speech', '')}" 
                               for c in lore_package.get('characters', [])])
        story_text = "\n".join(lore_package.get('story_so_far', []))
        beats_text = "\n".join([f"{i+1}. {b}" for i, b in enumerate(beats)])
        
        system_prompt = PROMPT_OMNISCIENT_DRAFTING.format(
            genre=lore_package.get('genre', 'fiction'),
            characters=char_text or "No characters mentioned",
            story_so_far=story_text or "Beginning of story",
            world_rules=lore_package.get('world_rules', 'No specific rules'),
            beats=beats_text
        )
        
        full_prompt = (
            f"{system_prompt}"
            f"<|start_header_id|>user<|end_header_id|>\n"
            f"Write the scene:\n"
            f"<|eot_id|>\n"
            f"<|start_header_id|>assistant<|end_header_id|>"
        )
        
        # Generate with higher max_tokens for 1000+ words
        try:
            with self.lock:
                for output in self.llm(
                    full_prompt,
                    max_tokens=1500,  # ~1000-1200 words
                    stop=["<|eot_id|>"],
                    stream=True,
                    temperature=0.7
                ):
                    token = output['choices'][0]['text']
                    response_queue.put(token)
            
            response_queue.put("[[END]]")
            
        except Exception as e:
            logging.error(f"Omniscient prose generation error: {e}")
            response_queue.put(f"\n[Error: {e}]")
            response_queue.put("[[END]]")

    def generate_beats_from_prose(self, prose_text: str) -> str:
        """Extract story beats from existing prose (reverse outlining)."""
        if not self.llm:
            return "Error: AI Model not loaded"
        
        if len(prose_text) < 100:
            return "Error: Prose too short for beat extraction"
        
        prompt = PROMPT_BEAT_EXTRACTOR.format(prose_text=prose_text[:4000])
        
        full_prompt = (
            f"{prompt}"
            f"<|start_header_id|>user<|end_header_id|>\n"
            f"Extract the beats:\n"
            f"<|eot_id|>\n"
            f"<|start_header_id|>assistant<|end_header_id|>"
        )
        
        try:
            with self.lock:
                output = self.llm(
                    full_prompt,
                    max_tokens=300,
                    stop=["<|eot_id|>"],
                    echo=False,
                    temperature=0.5
                )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"Beat extraction error: {e}")
            return f"Error: {e}"

    def suggest_next_beats(self, prev_beats: str, lore_package: dict) -> str:
        """Suggest beats for next chapter based on previous chapter and lore."""
        if not self.llm:
            return "Error: AI Model not loaded"
        
        char_summary = "\n".join([f"- {c['name']}: {c.get('traits', '')}" for c in lore_package.get('characters', [])])
        story_summary = "\n".join(lore_package.get('story_so_far', []))
        lore_text = f"Characters:\n{char_summary}\n\nStory:\n{story_summary}"
        
        system_prompt = PROMPT_BEAT_SUGGESTER.format(
            genre=lore_package.get('genre', 'fiction'),
            prev_beats=prev_beats or "Beginning of story",
            lore_summary=lore_text or "No lore available"
        )
        
        full_prompt = (
            f"{system_prompt}"
            f"<|start_header_id|>user<|end_header_id|>\n"
            f"Suggest beats for next chapter:\n"
            f"<|eot_id|>\n"
            f"<|start_header_id|>assistant<|end_header_id|>"
        )
        
        try:
            with self.lock:
                output = self.llm(
                    full_prompt,
                    max_tokens=300,
                    stop=["<|eot_id|>"],
                    echo=False,
                    temperature=0.7
                )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"Beat suggestion error: {e}")
            return f"Error: {e}"
