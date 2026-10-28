from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
import os
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "Gridbricks UK Wind Forecast Analytics"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Elexon BMRS API
    elexon_base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"
    request_timeout_seconds: float = 30.0
    max_retries: int = 3
    backoff_factor: float = 1.5
    
    # Cache and Storage
    cache_dir: str = str(Path(__file__).resolve().parent.parent.parent / "data" / "cache")
    enable_cache: bool = True
    
    # Analytical defaults
    default_start_date: str = "2026-01-01"
    default_end_date: str = "2026-01-31"
    default_cutoff_type: str = "DA_1100"  # Day-Ahead 11:00 GMT (EPEX SPOT / Nord Pool UK Day-Ahead gate closure)
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "https://gridbricks-wind-forecast-analytics.vercel.app",
        "https://gridbricks-wind-forecast-analytics.onrender.com",
        "*"
    ]

    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }


settings = Settings()
