from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from app.core.config import settings
from app.core.logging import logger


def _ensure_utc(dt: Any) -> datetime:
    """Ensure a timestamp is a timezone-aware UTC datetime."""
    if isinstance(dt, pd.Timestamp):
        pdt = dt.to_pydatetime()
        if pdt.tzinfo is None:
            return pdt.replace(tzinfo=timezone.utc)
        return pdt.astimezone(timezone.utc)
    elif isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    p = pd.to_datetime(dt, utc=True).to_pydatetime()
    return p


class DataStore:
    """
    In-memory and file-based data repository for Elexon actuals and forecasts.
    Provides fast, non-blocking data access, disk persistence, and cache management.
    Precomputes indexed lookups to eliminate repeated per-request grouping and sorting.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or settings.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.actuals_file = self.cache_dir / "fuelhh_wind_actuals.json"
        self.forecasts_file = self.cache_dir / "windfor_forecasts.json"

        self.df_actuals: pd.DataFrame = pd.DataFrame()
        self.df_forecasts: pd.DataFrame = pd.DataFrame()

        # Precomputed fast-lookup structures
        self._forecast_index: Dict[datetime, Tuple[np.ndarray, np.ndarray, List[datetime]]] = {}
        self._actual_hourly_map: Dict[datetime, float] = {}

        self._load_from_cache()

    def _rebuild_indexes(self) -> None:
        """Rebuild internal fast-lookup indexes whenever datasets are updated."""
        # 1. Hourly aggregated actuals map
        if not self.df_actuals.empty:
            try:
                hour_bins = self.df_actuals['startTime'].dt.floor('h')
                grouped_act = self.df_actuals.groupby(hour_bins)['generation'].mean().to_dict()
                self._actual_hourly_map = {
                    _ensure_utc(k): round(float(v), 2) for k, v in grouped_act.items()
                }
            except Exception as e:
                logger.error(f"Failed to build actuals hourly index: {e}")
                self._actual_hourly_map = {}
        else:
            self._actual_hourly_map = {}

        # 2. Forecasts grouped by startTime and pre-sorted by (publishTime, generation)
        if not self.df_forecasts.empty:
            try:
                # Pre-sort once globally: guarantees ascending publishTime, then ascending generation
                # for deterministic latest-publication and tie-breaking
                df_sorted = self.df_forecasts.sort_values(
                    by=['startTime', 'publishTime', 'generation'],
                    ascending=[True, True, True]
                )

                fc_index: Dict[datetime, Tuple[np.ndarray, np.ndarray, List[datetime]]] = {}
                for st, group in df_sorted.groupby('startTime'):
                    st_utc = _ensure_utc(st)
                    # Convert to datetime64[ns] in UTC for fast np.searchsorted
                    pub_times_np = group['publishTime'].values.astype('datetime64[ns]')
                    gens_np = group['generation'].values.astype(np.float64)
                    pub_times_dt = [_ensure_utc(pt) for pt in group['publishTime']]
                    fc_index[st_utc] = (pub_times_np, gens_np, pub_times_dt)

                self._forecast_index = fc_index
            except Exception as e:
                logger.error(f"Failed to build forecast index: {e}")
                self._forecast_index = {}
        else:
            self._forecast_index = {}

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

        self._rebuild_indexes()

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
            self._rebuild_indexes()
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
            self._rebuild_indexes()
            logger.info(f"Saved and cached {len(records)} WINDFOR records.")
        except Exception as e:
            logger.error(f"Failed to save forecasts to disk: {e}")

    def get_actuals(self, copy: bool = True) -> pd.DataFrame:
        return self.df_actuals.copy() if copy else self.df_actuals

    def get_forecasts(self, copy: bool = True) -> pd.DataFrame:
        return self.df_forecasts.copy() if copy else self.df_forecasts

    def get_forecast_index(self) -> Dict[datetime, Tuple[np.ndarray, np.ndarray, List[datetime]]]:
        """Return precomputed map: deliveryInterval (UTC) -> (pub_times_np, gens_np, pub_times_dt)."""
        return self._forecast_index

    def get_actual_hourly_map(self) -> Dict[datetime, float]:
        """Return precomputed map: deliveryInterval (UTC) -> hourly average actual generation (MW)."""
        return self._actual_hourly_map

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
