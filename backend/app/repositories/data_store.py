import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from app.core.config import settings
from app.core.logging import logger


class DataStore:
    """
    In-memory and file-based data repository for Elexon actuals and forecasts.
    Provides fast, non-blocking data access, disk persistence, and cache management.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or settings.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.actuals_file = self.cache_dir / "fuelhh_wind_actuals.json"
        self.forecasts_file = self.cache_dir / "windfor_forecasts.json"
        
        self.df_actuals: pd.DataFrame = pd.DataFrame()
        self.df_forecasts: pd.DataFrame = pd.DataFrame()
        self._load_from_cache()

    def _load_from_cache(self) -> None:
        """Load cached data from disk if available."""
        if self.actuals_file.exists():
            try:
                with open(self.actuals_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
                    if records:
                        df = pd.DataFrame(records)
                        df['startTime'] = pd.to_datetime(df['startTime'], utc=True)
                        if 'publishTime' in df.columns:
                            df['publishTime'] = pd.to_datetime(df['publishTime'], utc=True)
                        self.df_actuals = df
                        logger.info(f"Loaded {len(self.df_actuals)} actual wind records from cache.")
            except Exception as e:
                logger.error(f"Failed to load actuals cache: {e}")

        if self.forecasts_file.exists():
            try:
                with open(self.forecasts_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
                    if records:
                        df = pd.DataFrame(records)
                        df['startTime'] = pd.to_datetime(df['startTime'], utc=True)
                        df['publishTime'] = pd.to_datetime(df['publishTime'], utc=True)
                        self.df_forecasts = df
                        logger.info(f"Loaded {len(self.df_forecasts)} wind forecast records from cache.")
            except Exception as e:
                logger.error(f"Failed to load forecasts cache: {e}")

    def save_actuals(self, records: List[Dict[str, Any]]) -> None:
        """Save actual records to memory and disk cache."""
        if not records:
            return
            
        try:
            with open(self.actuals_file, "w", encoding="utf-8") as f:
                json.dump(records, f)
            df = pd.DataFrame(records)
            df['startTime'] = pd.to_datetime(df['startTime'], utc=True)
            if 'publishTime' in df.columns:
                df['publishTime'] = pd.to_datetime(df['publishTime'], utc=True)
            self.df_actuals = df
            logger.info(f"Saved and cached {len(records)} FUELHH WIND records.")
        except Exception as e:
            logger.error(f"Failed to save actuals to disk: {e}")

    def save_forecasts(self, records: List[Dict[str, Any]]) -> None:
        """Save forecast records to memory and disk cache."""
        if not records:
            return
            
        try:
            with open(self.forecasts_file, "w", encoding="utf-8") as f:
                json.dump(records, f)
            df = pd.DataFrame(records)
            df['startTime'] = pd.to_datetime(df['startTime'], utc=True)
            df['publishTime'] = pd.to_datetime(df['publishTime'], utc=True)
            self.df_forecasts = df
            logger.info(f"Saved and cached {len(records)} WINDFOR records.")
        except Exception as e:
            logger.error(f"Failed to save forecasts to disk: {e}")

    def get_actuals(self) -> pd.DataFrame:
        return self.df_actuals.copy()

    def get_forecasts(self) -> pd.DataFrame:
        return self.df_forecasts.copy()

    def has_data(self) -> bool:
        return not self.df_actuals.empty and not self.df_forecasts.empty

    def get_stats(self) -> Dict[str, Any]:
        return {
            "actualsCount": len(self.df_actuals),
            "forecastsCount": len(self.df_forecasts),
            "actualsDateMin": str(self.df_actuals['startTime'].min()) if not self.df_actuals.empty else None,
            "actualsDateMax": str(self.df_actuals['startTime'].max()) if not self.df_actuals.empty else None,
            "forecastsDateMin": str(self.df_forecasts['startTime'].min()) if not self.df_forecasts.empty else None,
            "forecastsDateMax": str(self.df_forecasts['startTime'].max()) if not self.df_forecasts.empty else None,
        }


# Global singleton instance
data_store = DataStore()
