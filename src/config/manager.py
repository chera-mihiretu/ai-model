import os
import glob
import logging
from dataclasses import dataclass
from typing import Optional

@dataclass
class AIConfig:
    model_path: str
    n_ctx: int = 4096  # Safe default; 0 = auto-detect causes OOM with large-context models
    n_batch: int = 512
    temperature: float = 0.7
    n_gpu_layers: int = -1

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._init_config()
        return cls._instance

    def _init_config(self):
        import sys
        
        # Check for environment variable paths first (set by Electron)
        models_path = os.environ.get('EXELSIAS_MODELS_PATH')
        llm_models_path = os.environ.get('EXELSIAS_LLM_MODELS_PATH')
        
        if llm_models_path:
            # Production: use LLM path provided by Electron (user's app data)
            self.base_dir = os.path.dirname(os.path.dirname(llm_models_path))
            self.models_dir = llm_models_path
        elif models_path:
            # Fallback: use general models path with llama subfolder
            self.base_dir = os.path.dirname(models_path)
            self.models_dir = os.path.join(models_path, "llama")
        elif getattr(sys, 'frozen', False):
            # Frozen (PyInstaller) without Electron env var
            self.base_dir = os.path.dirname(sys.executable)
            self.models_dir = os.path.join(self.base_dir, "models", "llama")
        else:
            # Development mode
            self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.models_dir = os.path.join(self.base_dir, "models", "llama")
        
        # Ensure models directory exists
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Auto-detect first .gguf file
        found_models = glob.glob(os.path.join(self.models_dir, "*.gguf"))
        model_path = found_models[0] if found_models else None
        
        logging.info(f"ConfigManager: models_dir = {self.models_dir}")
        logging.info(f"ConfigManager: found_models = {found_models}")
        logging.info(f"ConfigManager: model_path = {model_path}")
        
        # IMPORTANT: n_ctx=0 auto-detects from model metadata, but LLaMA 3.1 reports
        # 131072 (128K) tokens which allocates ~8 GB of KV cache RAM on top of model weights.
        # On a 14GB system this causes OOM kills. Use 4096 as a safe default.
        self.ai_config = AIConfig(
            model_path=model_path,
            n_ctx=4096,  # Safe default; 128K auto-detect causes OOM on most machines
            n_batch=512,
            temperature=0.5,  # Lower temperature for more coherent output
            n_gpu_layers=-1
        )

    def get_ai_config(self) -> AIConfig:
        return self.ai_config

    def validate_model_path(self) -> tuple[bool, str]:
        if not self.ai_config.model_path:
            return False, f"No .gguf model found in {self.models_dir}"
        if not os.path.exists(self.ai_config.model_path):
            return False, f"Model file not found at {self.ai_config.model_path}"
        return True, "Model found"

    def list_available_models(self) -> list:
        """Return all .gguf files in the models directory with metadata."""
        found = glob.glob(os.path.join(self.models_dir, "*.gguf"))
        models = []
        for path in sorted(found):
            try:
                size_bytes = os.path.getsize(path)
                size_gb = round(size_bytes / (1024 ** 3), 2)
            except OSError:
                size_gb = 0
            models.append({
                'name': os.path.basename(path),
                'path': path,
                'size_gb': size_gb,
                'is_active': path == self.ai_config.model_path,
            })
        return models

    def set_model_path(self, model_path: str) -> tuple[bool, str]:
        """Update the AI config to use a different model file."""
        if not model_path:
            return False, "No model path provided"
        if not os.path.exists(model_path):
            return False, f"File not found: {model_path}"
        if not model_path.lower().endswith('.gguf'):
            return False, "File must be a .gguf model"
        self.ai_config.model_path = model_path
        return True, f"Model path set to {os.path.basename(model_path)}"
