import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AETHER Capital - Institutional AI Hedge Fund"
    VERSION: str = "4.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Environment & Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o")
    
    # Quantitative Risk Constraints
    MAX_VOLATILITY_THRESHOLD: float = 0.65       # Hard veto threshold (65% ann. vol)
    MAX_SINGLE_POSITION_WEIGHT: float = 0.35     # Max 35% in a single equity
    RISK_FREE_RATE: float = 0.04                # 4.0% US Treasury Benchmark
    DEFAULT_SLIPPAGE_BPS: float = 5.0           # 5 basis points execution slippage
    
    # Caching & Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CACHE_TTL_SECONDS: int = 3600               # 1-hour cache expiry

    class Config:
        case_sensitive = True

settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
