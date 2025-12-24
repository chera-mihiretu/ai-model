import os
import glob
from dataclasses import dataclass
from typing import Optional

@dataclass
class AIConfig:
    model_path: str
    n_ctx: int = 2048
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
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.models_dir = os.path.join(self.base_dir, "models", "llama")
        
        # Auto-detect first .gguf file
        found_models = glob.glob(os.path.join(self.models_dir, "*.gguf"))
        model_path = found_models[0] if found_models else None
        
        self.ai_config = AIConfig(
            model_path=model_path,
            n_ctx=2048,
            temperature=0.7,
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
