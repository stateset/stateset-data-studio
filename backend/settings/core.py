from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings

DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BACKEND_DIR = DEFAULT_PROJECT_ROOT / "backend"
DEFAULT_DATA_DIR = DEFAULT_PROJECT_ROOT / "data"

class Settings(BaseSettings):
    # Database settings
    database_url: str = "sqlite:///./synthetic_data.db"
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    
    # API settings
    api_base_url: str = "/api/v1"
    
    # LLM settings
    vllm_api_base: str = "http://localhost:8000/v1"
    vllm_model: str = "meta-llama/Llama-3.3-70B-Instruct"
    
    # Generation settings
    generation_temperature: float = 0.7
    generation_chunk_size: int = 4000
    generation_num_pairs: int = 25
    
    # Curation settings
    curation_threshold: float = 7.0
    curation_batch_size: int = 8
    
    # System settings
    sdk_bin: str = "synthetic-data-kit"
    data_dir: Path = DEFAULT_DATA_DIR
    project_root: Path = DEFAULT_PROJECT_ROOT
    backend_dir: Path = DEFAULT_BACKEND_DIR
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

settings = Settings()
