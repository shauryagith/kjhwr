from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class CutoffPreset(str, Enum):
    DA_1100 = "DA_1100"  # Day-Ahead 11:00 UK Time (Default GB Auction Cutoff)
    DA_1200 = "DA_1200"  # Day-Ahead 12:00 UK Time (Noon Cutoff)
    DA_1700 = "DA_1700"  # Day-Ahead 17:00 UK Time (Close of Business D-1)
    DA_2300 = "DA_2300"  # Day-Ahead 23:00 UK Time (Midnight D-1)
    ROLLING_24H = "ROLLING_24H"  # 24 Hours prior to interval start
    ROLLING_12H = "ROLLING_12H"  # 12 Hours prior to interval start
    ROLLING_6H = "ROLLING_6H"    # 6 Hours prior to interval start
    ROLLING_2H = "ROLLING_2H"    # 2 Hours prior to interval start
    CUSTOM = "CUSTOM"            # Custom ISO timestamp


class APIError(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    timestamp: datetime
    elexon_live_accessible: bool
    data_cache_available: bool
    data_points_cached: Dict[str, int]


class MetadataResponse(BaseModel):
    app_name: str
    version: str
    dataset_actual: str = "FUELHH (fuelType=WIND)"
    dataset_forecast: str = "WINDFOR"
    settlement_interval_minutes: int = 30
    forecast_interval_minutes: int = 60
    default_date_range: Dict[str, str] = {
        "start": "2026-01-01",
        "end": "2026-01-31"
    }
    supported_cutoff_presets: List[Dict[str, str]]
    market_notes: str
