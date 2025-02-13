import os
from typing import Optional
from pathlib import Path
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Note: python-dotenv not installed. Will not load from .env file.")


class Config:
    DEFAULT_CONFIG = {
        "ollama_base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "model": "deepseek-r1:14b",
        "timeout": 10,
        "safe_mode": True,
        "shell": os.name == 'posix'
    }

    def __init__(self, **kwargs):
        self.ollama_base_url = kwargs.get("ollama_base_url", self.DEFAULT_CONFIG["ollama_base_url"])
        self.api_key = kwargs.get("api_key", self.DEFAULT_CONFIG["api_key"])
        self.model = kwargs.get("model", self.DEFAULT_CONFIG["model"])
        self.timeout = kwargs.get("timeout", self.DEFAULT_CONFIG["timeout"])
        self.safe_mode = kwargs.get("safe_mode", self.DEFAULT_CONFIG["safe_mode"])
        self.shell = kwargs.get("shell", self.DEFAULT_CONFIG["shell"])

    @classmethod
    def load(cls, env_file: Optional[str] = None) -> 'Config':
        """
        Load configuration from multiple sources in order of precedence:
        1. .env file (if exists)
        2. Environment variables
        3. Default values (only for non-required variables)
        
        Args:
            env_file: Optional path to .env file. If None, will look for .env in current directory
            
        Raises:
            ValueError: If a required configuration value is not set in either .env or environment
        """
        config_dict = {}
        
        # Step 1: Try to load from .env file
        if env_file is None:
            script_dir = Path(__file__).parent
            env_file = str(script_dir / '.env')
        
        if os.path.exists(env_file):
            if DOTENV_AVAILABLE:
                load_dotenv(env_file)
            else:
                print("Warning: python-dotenv not installed. Cannot load from .env file.")
        else:
            print(f"Warning: .env file not found at {env_file}")
        
        # Step 2: Load from environment variables (overrides .env)
        env_mapping = {
            "OLLAMA_BASE_URL": "ollama_base_url",
            "API_KEY": "api_key",
            "MODEL": "model",
            "TIMEOUT": "timeout",
            "SAFE_MODE": "safe_mode",
            "SHELL": "shell"
        }
        
        required_vars = ["OLLAMA_BASE_URL", "API_KEY", "MODEL"]
        missing_vars = []
        
        for env_var, config_key in env_mapping.items():
            # First check .env loaded values
            value = os.getenv(env_var)
            
            if value is not None:
                # Convert types as needed
                if config_key == "timeout":
                    value = int(value)
                elif config_key == "safe_mode":
                    value = value.lower() == "true"
                elif config_key == "shell":
                    value = value.lower() == "true"
                    
                config_dict[config_key] = value
            elif env_var in required_vars:
                missing_vars.append(env_var)
        
        if missing_vars:
            raise ValueError(
                f"Required environment variables not set: {', '.join(missing_vars)}. "
                "Please set them in .env file or environment variables."
            )
        
        # Fill in any remaining values with defaults
        for key, default_value in cls.DEFAULT_CONFIG.items():
            if key not in config_dict:
                config_dict[key] = default_value
        
        return cls(**config_dict)

    def __str__(self) -> str:
        """Return a string representation of the current configuration"""
        return "\n".join([
            "Current Configuration:",
            f"  Ollama Base URL: {self.ollama_base_url}",
            f"  Model: {self.model}",
            f"  Command Timeout: {self.timeout}s",
            f"  Safe Mode: {'Enabled' if self.safe_mode else 'Disabled'}",
            f"  Shell: {'Posix' if self.shell else 'Windows'}"
        ])