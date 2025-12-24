import logging
import sys
import queue
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

class AIEngine:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.llm: Optional[Llama] = None
        self.status_message = "Initializing..."
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
                verbose=False
            )
            self.status_message = "Model Loaded: Llama 3.1 8B (GPU)"
            logging.info("Model loaded successfully.")
        except Exception as e:
            self.status_message = f"Error: Failed to load model ({e})"
            logging.error(f"Failed to load model: {e}")
            self.llm = None

    def stream_response(self, instruction: str, response_queue: queue.Queue, bible_data: str = "", current_text: str = "", character_context: dict = None) -> None:
        """
        Streams response tokens into the provided queue.
        Uses Llama 3 Header format.
        """
        if not self.llm:
            response_queue.put("Error: AI Model is not loaded check logs.")
            response_queue.put("[[END]]")
            return

        # Choose System Prompt
        if character_context:
            system_prompt = MIMIC_SYSTEM_PROMPT.format(
                name=character_context.get('name', 'Unknown'),
                relationship=character_context.get('relationship_to_author', 'None'),
                traits=character_context.get('personality_traits', 'None'),
                speech=character_context.get('speech_pattern', 'Standard')
            )
        else:
            system_prompt = PROSE_SYSTEM_PROMPT

        # Construct Prompt
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
            f"Summarize the following scene into 2-3 concise sentences capturing the key physical actions and plot progression. Do not analyze, just report.\n"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"{text}\n"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )

        try:
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
You are the OMNISCIENT LORE KEEPER for the book '{project_name}'.
You have perfect memory. You are the ultimate authority on this story's continuity.

DATABASE ACCESS:
{project_memory}

INSTRUCTIONS:
1. Analyze the provided Database Access thoroughly.
2. If asked about a character's history, cite the specific chapter they appeared in.
3. If the author is about to make a mistake (e.g., changing an eye color or a dead character appearing), WARN THEM.
4. Be the "Brain" of this project. Do not guess. If the data is in the history, find it.
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
