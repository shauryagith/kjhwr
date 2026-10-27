import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from app.services.analysis import (
    calculate_metrics,
    calculate_daily_summary,
    calculate_diurnal_accuracy,
    calculate_error_distribution
)


def test_calculate_metrics_standard():
    # 4 hourly intervals:
    # A = [1000, 2000, 3000, 4000]
    # F = [1200, 1800, 3300, 4000]
    # Errors: F - A = [+200, -200, +300, 0]
    # Abs errors: [200, 200, 300, 0] -> sum = 700, mean = 175.0 (MAE)
    # Squared errors: [40000, 40000, 90000, 0] -> sum = 170000, mean = 42500 -> RMSE = sqrt(42500) ~= 206.16
    # Bias: (200 - 200 + 300 + 0) / 4 = 75.0 MW
    # WAPE: 700 / 10000 * 100 = 7.0%
    
    dates = [datetime(2026, 1, 1, h, 0, 0, tzinfo=timezone.utc) for h in range(4)]
    df = pd.DataFrame({
        "deliveryInterval": dates,
        "actualMW": [1000.0, 2000.0, 3000.0, 4000.0],
        "forecastMW": [1200.0, 1800.0, 3300.0, 4000.0],
        "errorMW": [200.0, -200.0, 300.0, 0.0],
        "absErrorMW": [200.0, 200.0, 300.0, 0.0]
    })
    
    summary, procurement = calculate_metrics(df)
    
    assert summary.matchedIntervals == 4
    assert summary.totalIntervals == 4
    assert summary.dataCoveragePct == 100.0
    assert summary.maeMW == 175.0
    assert summary.rmseMW == pytest.approx(206.16, abs=0.01)
    assert summary.biasMW == 75.0
    assert summary.wapePct == 7.0
    assert summary.overforecastCount == 2
    assert summary.underforecastCount == 1
    assert summary.exactMatchCount == 1
    assert procurement.totalOverforecastMWh == 500.0
    assert procurement.totalUnderforecastMWh == 200.0
    assert procurement.netImbalanceMWh == 300.0


def test_calculate_metrics_zero_actual():
    # If actual generation is zero, WAPE should handle division by zero cleanly
    dates = [datetime(2026, 1, 1, h, 0, 0, tzinfo=timezone.utc) for h in range(2)]
    df = pd.DataFrame({
        "deliveryInterval": dates,
        "actualMW": [0.0, 0.0],
        "forecastMW": [100.0, 200.0],
        "errorMW": [100.0, 200.0],
        "absErrorMW": [100.0, 200.0]
    })
    
    summary, procurement = calculate_metrics(df)
    assert summary.matchedIntervals == 2
    assert summary.wapePct is None  # Avoid ZeroDivisionError
    assert summary.maeMW == 150.0


def test_calculate_metrics_missing_intervals():
    dates = [datetime(2026, 1, 1, h, 0, 0, tzinfo=timezone.utc) for h in range(4)]
    df = pd.DataFrame({
        "deliveryInterval": dates,
        "actualMW": [1000.0, np.nan, 3000.0, np.nan],
        "forecastMW": [1100.0, 2200.0, np.nan, np.nan],
        "errorMW": [100.0, np.nan, np.nan, np.nan],
        "absErrorMW": [100.0, np.nan, np.nan, np.nan]
    })
    
    summary, procurement = calculate_metrics(df)
    assert summary.totalIntervals == 4
    assert summary.matchedIntervals == 1  # Only row 0 has both
    assert summary.missingActualIntervals == 2
    assert summary.missingForecastIntervals == 2
    assert summary.dataCoveragePct == 25.0


def test_calculate_daily_summary():
    # Two days with 2 intervals each
    dates = [
        datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 2, 1, 0, tzinfo=timezone.utc),
    ]
    df = pd.DataFrame({
        "deliveryInterval": dates,
        "actualMW": [1000.0, 1000.0, 2000.0, 2000.0],
        "forecastMW": [1100.0, 900.0, 2500.0, 1500.0]
    })
    
    daily = calculate_daily_summary(df)
    assert len(daily) == 2
    assert daily[0].date == "2026-01-01"
    assert daily[0].maeMW == 100.0
    assert daily[1].date == "2026-01-02"
    assert daily[1].maeMW == 500.0


def test_calculate_diurnal_accuracy():
    # 2 days of hour 0 and hour 1
    dates = [
        datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 2, 1, 0, tzinfo=timezone.utc),
    ]
    df = pd.DataFrame({
        "deliveryInterval": dates,
        "actualMW": [1000.0, 1000.0, 1200.0, 800.0],
        "forecastMW": [1100.0, 1200.0, 1300.0, 1000.0]
    })
    
    diurnal = calculate_diurnal_accuracy(df)
    assert len(diurnal) == 24
    h0 = diurnal[0]
    assert h0.count == 2
    assert h0.hourOfDay == 0
    assert h0.maeMW == 100.0  # |1100-1000|=100, |1300-1200|=100 -> mean 100


def test_calculate_error_distribution():
    dates = [datetime(2026, 1, 1, h, 0, tzinfo=timezone.utc) for h in range(5)]
    df = pd.DataFrame({
        "deliveryInterval": dates,
        "actualMW": [1000.0, 1000.0, 1000.0, 1000.0, 1000.0],
        "forecastMW": [
            6000.0,  # +5000 (Severe Over)
            2500.0,  # +1500 (+1 to +2 GW)
            1100.0,  # +100 (Accurate)
            -500.0,  # -1500 (-2 to -1 GW)
            -4000.0  # -5000 (Severe Under)
        ]
    })
    
    buckets = calculate_error_distribution(df)
    assert len(buckets) == 9
    
    # Severe Over count should be 1
    severe_over = next(b for b in buckets if "Severe Over" in b.label)
    assert severe_over.count == 1
    
    # Accurate count should be 1
    accurate = next(b for b in buckets if "Accurate" in b.label)
    assert accurate.count == 1
