import os
import glob
from dataclasses import dataclass
from typing import Optional

@dataclass
class AIConfig:
    model_path: str
    n_ctx: int = 4096
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
        
        if models_path:
            # Production: use path provided by Electron
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
        
        print(f"ConfigManager: models_dir = {self.models_dir}")
        print(f"ConfigManager: found_models = {found_models}")
        print(f"ConfigManager: model_path = {model_path}")
        
        self.ai_config = AIConfig(
            model_path=model_path,
            n_ctx=4096,
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
