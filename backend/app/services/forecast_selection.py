from datetime import datetime, timezone, timedelta, time
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
from app.schemas.common import CutoffPreset
from app.schemas.forecast import ForecastItem, MatchedIntervalItem


def ensure_utc(dt: datetime) -> datetime:
    """Ensure a datetime object is timezone-aware and set to UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def calculate_decision_cutoff(
    delivery_interval: datetime,
    cutoff_preset: CutoffPreset | str = CutoffPreset.DA_1100,
    custom_cutoff: Optional[datetime] = None
) -> datetime:
    """
    Calculate the effective decision cutoff timestamp for a specific delivery interval.
    
    UK Market Rules & Conventions:
    - DA_1100: EPEX SPOT & Nord Pool GB Day-Ahead Auction order book closure at 11:00 GMT on D-1.
    - DA_1200: European standard Day-Ahead locking cutoff (12:00 GMT on D-1).
    - DA_1700: End of standard trading business day on D-1 (17:00 GMT).
    - DA_2300: Midnight prior to delivery day (23:00 GMT on D-1).
    - ROLLING_XH: X hours prior to delivery interval start.
    - CUSTOM: User-provided explicit timestamp.
    """
    delivery_utc = ensure_utc(delivery_interval)
    delivery_date = delivery_utc.date()
    d_minus_one = delivery_date - timedelta(days=1)
    
    preset_str = cutoff_preset.value if isinstance(cutoff_preset, CutoffPreset) else str(cutoff_preset)
    
    if preset_str == "DA_1100":
        return datetime.combine(d_minus_one, time(11, 0, 0), tzinfo=timezone.utc)
    elif preset_str == "DA_1200":
        return datetime.combine(d_minus_one, time(12, 0, 0), tzinfo=timezone.utc)
    elif preset_str == "DA_1700":
        return datetime.combine(d_minus_one, time(17, 0, 0), tzinfo=timezone.utc)
    elif preset_str == "DA_2300":
        return datetime.combine(d_minus_one, time(23, 0, 0), tzinfo=timezone.utc)
    elif preset_str == "ROLLING_24H":
        return delivery_utc - timedelta(hours=24)
    elif preset_str == "ROLLING_12H":
        return delivery_utc - timedelta(hours=12)
    elif preset_str == "ROLLING_6H":
        return delivery_utc - timedelta(hours=6)
    elif preset_str == "ROLLING_2H":
        return delivery_utc - timedelta(hours=2)
    elif preset_str == "CUSTOM" and custom_cutoff is not None:
        return ensure_utc(custom_cutoff)
    else:
        # Default fallback to DA_1100
        return datetime.combine(d_minus_one, time(11, 0, 0), tzinfo=timezone.utc)


def select_forecast_as_of(
    forecasts: List[Dict[str, Any]] | pd.DataFrame,
    delivery_interval: datetime,
    decision_cutoff: datetime
) -> Optional[Dict[str, Any]]:
    """
    Select the latest eligible wind forecast for a given delivery interval published
    on or before the decision cutoff.
    
    Args:
        forecasts: Collection of forecast records with 'startTime', 'publishTime', 'generation'.
        delivery_interval: Target delivery interval start time.
        decision_cutoff: Decision cutoff timestamp. Forecasts published after this cutoff are excluded.
        
    Returns:
        The selected forecast record dictionary with metadata (publishTime, generation, age, lead time),
        or None if no eligible forecast exists.
    """
    delivery_utc = ensure_utc(delivery_interval)
    cutoff_utc = ensure_utc(decision_cutoff)
    
    if isinstance(forecasts, pd.DataFrame):
        if forecasts.empty:
            return None
        
        # Filter by delivery interval
        df_target = forecasts[forecasts['startTime'] == delivery_utc]
        if df_target.empty:
            return None
            
        # Point-in-time filter: publishTime <= decision_cutoff
        eligible = df_target[df_target['publishTime'] <= cutoff_utc]
        if eligible.empty:
            return None
            
        # Select latest eligible publication (break ties by highest index/generation)
        if len(eligible) == 1:
            latest_record = eligible.iloc[0]
        else:
            latest_record = eligible.sort_values(by=['publishTime', 'generation'], ascending=[True, True]).iloc[-1]
        
        raw_pub = latest_record['publishTime']
        pub_time = ensure_utc(raw_pub.to_pydatetime() if isinstance(raw_pub, pd.Timestamp) else raw_pub)
        gen_mw = float(latest_record['generation'])
        forecast_age_h = max(0.0, (cutoff_utc - pub_time).total_seconds() / 3600.0)
        lead_time_h = (delivery_utc - pub_time).total_seconds() / 3600.0
        
        return {
            "startTime": delivery_utc,
            "publishTime": pub_time,
            "generation": gen_mw,
            "forecastAgeHours": round(forecast_age_h, 2),
            "leadTimeHours": round(lead_time_h, 2),
            "dataset": "WINDFOR"
        }
    
    # List of dicts / items fallback
    candidates = []
    for f in forecasts:
        if isinstance(f, dict):
            st = ensure_utc(f["startTime"] if isinstance(f["startTime"], datetime) else pd.to_datetime(f["startTime"]).to_pydatetime())
            pt = ensure_utc(f["publishTime"] if isinstance(f["publishTime"], datetime) else pd.to_datetime(f["publishTime"]).to_pydatetime())
            gen = float(f["generation"])
        else:
            st = ensure_utc(f.startTime)
            pt = ensure_utc(f.publishTime)
            gen = float(f.generation)
            
        if st == delivery_utc and pt <= cutoff_utc:
            candidates.append((pt, gen, f))
            
    if not candidates:
        return None
        
    # Sort by publish time ascending, pick the latest
    candidates.sort(key=lambda x: (x[0], x[1]))
    best_pt, best_gen, raw_obj = candidates[-1]
    
    forecast_age_h = max(0.0, (cutoff_utc - best_pt).total_seconds() / 3600.0)
    lead_time_h = (delivery_utc - best_pt).total_seconds() / 3600.0
    
    return {
        "startTime": delivery_utc,
        "publishTime": best_pt,
        "generation": best_gen,
        "forecastAgeHours": round(forecast_age_h, 2),
        "leadTimeHours": round(lead_time_h, 2),
        "dataset": "WINDFOR"
    }
