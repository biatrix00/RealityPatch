from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Feature Flags
    ENABLE_USER_AUTH = True
    ENABLE_BENCHMARK_MODE = True
    ENABLE_FILE_UPLOAD = True
    ENABLE_CLAIM_GRAPH = True
    ENABLE_ENSEMBLE_MODE = True
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    
    # Database Settings
    DB_PATH = "data/realitypatch.db"
    
    # Session Settings
    SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "your-secret-key-here")
    SESSION_EXPIRY_DAYS = 7
    
    # Benchmark Settings
    BENCHMARK_FILE = "data/benchmark.json"
    
    # File Upload Settings
    ALLOWED_EXTENSIONS = {'.pdf', '.txt'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    # Agent Settings
    AGENT_CONFIDENCE_THRESHOLD = 0.7
    ENSEMBLE_WEIGHTS = {
        "gemini": 0.4,
        "openai": 0.3,
        "serper": 0.3
    }
    
    @classmethod
    def get_agent_config(cls) -> Dict[str, Any]:
        return {
            "confidence_threshold": cls.AGENT_CONFIDENCE_THRESHOLD,
            "ensemble_weights": cls.ENSEMBLE_WEIGHTS
        }
    
    @classmethod
    def is_feature_enabled(cls, feature_name: str) -> bool:
        return getattr(cls, f"ENABLE_{feature_name.upper()}", False) 