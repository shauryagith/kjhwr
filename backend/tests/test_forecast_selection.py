import pytest
from datetime import datetime, timezone, timedelta, time
import pandas as pd
from app.services.forecast_selection import (
    select_forecast_as_of,
    calculate_decision_cutoff,
    ensure_utc
)
from app.schemas.common import CutoffPreset


def test_ensure_utc():
    naive = datetime(2026, 1, 1, 12, 0, 0)
    aware = ensure_utc(naive)
    assert aware.tzinfo == timezone.utc
    assert aware.hour == 12

    # Already aware UTC
    same = ensure_utc(aware)
    assert same == aware


def test_calculate_decision_cutoff_da_1100():
    # Delivery on Jan 5 at 14:00 UTC
    delivery = datetime(2026, 1, 5, 14, 0, 0, tzinfo=timezone.utc)
    cutoff = calculate_decision_cutoff(delivery, CutoffPreset.DA_1100)
    # Expected D-1 (Jan 4) at 11:00 UTC
    expected = datetime(2026, 1, 4, 11, 0, 0, tzinfo=timezone.utc)
    assert cutoff == expected


def test_calculate_decision_cutoff_da_presets():
    delivery = datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
    
    # DA_1200
    c12 = calculate_decision_cutoff(delivery, CutoffPreset.DA_1200)
    assert c12 == datetime(2026, 1, 9, 12, 0, 0, tzinfo=timezone.utc)
    
    # DA_1700
    c17 = calculate_decision_cutoff(delivery, CutoffPreset.DA_1700)
    assert c17 == datetime(2026, 1, 9, 17, 0, 0, tzinfo=timezone.utc)
    
    # DA_2300
    c23 = calculate_decision_cutoff(delivery, CutoffPreset.DA_2300)
    assert c23 == datetime(2026, 1, 9, 23, 0, 0, tzinfo=timezone.utc)


def test_calculate_decision_cutoff_rolling_presets():
    delivery = datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
    
    r24 = calculate_decision_cutoff(delivery, CutoffPreset.ROLLING_24H)
    assert r24 == datetime(2026, 1, 9, 18, 0, 0, tzinfo=timezone.utc)
    
    r12 = calculate_decision_cutoff(delivery, CutoffPreset.ROLLING_12H)
    assert r12 == datetime(2026, 1, 10, 6, 0, 0, tzinfo=timezone.utc)
    
    r6 = calculate_decision_cutoff(delivery, CutoffPreset.ROLLING_6H)
    assert r6 == datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)


def test_calculate_decision_cutoff_custom():
    delivery = datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
    custom = datetime(2026, 1, 8, 9, 30, 0, tzinfo=timezone.utc)
    cutoff = calculate_decision_cutoff(delivery, CutoffPreset.CUSTOM, custom_cutoff=custom)
    assert cutoff == custom


def test_select_forecast_as_of_latest_eligible():
    delivery = datetime(2026, 1, 2, 14, 0, 0, tzinfo=timezone.utc)
    cutoff = datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
    
    forecasts = [
        {"startTime": delivery, "publishTime": datetime(2026, 1, 1, 6, 0, 0, tzinfo=timezone.utc), "generation": 12000.0},
        {"startTime": delivery, "publishTime": datetime(2026, 1, 1, 9, 30, 0, tzinfo=timezone.utc), "generation": 13500.0},
        {"startTime": delivery, "publishTime": datetime(2026, 1, 1, 10, 45, 0, tzinfo=timezone.utc), "generation": 14200.0},
        # Published after cutoff (must be excluded)
        {"startTime": delivery, "publishTime": datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc), "generation": 15000.0},
    ]
    
    selected = select_forecast_as_of(forecasts, delivery, cutoff)
    assert selected is not None
    assert selected["publishTime"] == datetime(2026, 1, 1, 10, 45, 0, tzinfo=timezone.utc)
    assert selected["generation"] == 14200.0
    assert selected["forecastAgeHours"] == 0.25  # 15 minutes = 0.25 hours
    assert selected["leadTimeHours"] == 27.25


def test_select_forecast_as_of_excludes_future_publications():
    delivery = datetime(2026, 1, 2, 14, 0, 0, tzinfo=timezone.utc)
    cutoff = datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
    
    # All forecasts published strictly after cutoff
    forecasts = [
        {"startTime": delivery, "publishTime": datetime(2026, 1, 1, 11, 1, 0, tzinfo=timezone.utc), "generation": 14000.0},
        {"startTime": delivery, "publishTime": datetime(2026, 1, 1, 15, 0, 0, tzinfo=timezone.utc), "generation": 14500.0},
    ]
    
    selected = select_forecast_as_of(forecasts, delivery, cutoff)
    assert selected is None


def test_select_forecast_as_of_with_dataframe():
    delivery = datetime(2026, 1, 2, 14, 0, 0, tzinfo=timezone.utc)
    cutoff = datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
    
    df = pd.DataFrame([
        {"startTime": delivery, "publishTime": datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc), "generation": 11000.0},
        {"startTime": delivery, "publishTime": datetime(2026, 1, 1, 10, 30, 0, tzinfo=timezone.utc), "generation": 12500.0},
        {"startTime": delivery, "publishTime": datetime(2026, 1, 1, 14, 0, 0, tzinfo=timezone.utc), "generation": 16000.0},
    ])
    
    selected = select_forecast_as_of(df, delivery, cutoff)
    assert selected is not None
    assert selected["generation"] == 12500.0
    assert selected["publishTime"] == datetime(2026, 1, 1, 10, 30, 0, tzinfo=timezone.utc)


def test_select_forecast_as_of_duplicate_publications():
    delivery = datetime(2026, 1, 2, 14, 0, 0, tzinfo=timezone.utc)
    cutoff = datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
    
    # Two records with exact same publishTime
    forecasts = [
        {"startTime": delivery, "publishTime": datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc), "generation": 13000.0},
        {"startTime": delivery, "publishTime": datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc), "generation": 13500.0},
    ]
    
    selected = select_forecast_as_of(forecasts, delivery, cutoff)
    assert selected is not None
    # Deterministic tie-breaker
    assert selected["generation"] in [13000.0, 13500.0]
