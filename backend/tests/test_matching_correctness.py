import pytest
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np

from app.services.ingestion import ingestion_service
from app.services.forecast_selection import calculate_decision_cutoff, select_forecast_as_of, ensure_utc
from app.schemas.common import CutoffPreset
from app.services.analysis import calculate_metrics


def test_hourly_aggregation_fuelhh():
    """Verify that half-hourly FUELHH records within the same hour are averaged correctly."""
    # Two settlement periods for 2026-01-01 10:00:
    # 10:00: 1000.0 MW, 10:30: 2000.0 MW -> Expected mean = 1500.0 MW
    df_actuals = pd.DataFrame([
        {
            "startTime": datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            "settlementPeriod": 21,
            "fuelType": "WIND",
            "generation": 1000.0
        },
        {
            "startTime": datetime(2026, 1, 1, 10, 30, 0, tzinfo=timezone.utc),
            "settlementPeriod": 22,
            "fuelType": "WIND",
            "generation": 2000.0
        }
    ])

    df_forecasts = pd.DataFrame([
        {
            "startTime": datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            "publishTime": datetime(2025, 12, 31, 10, 0, 0, tzinfo=timezone.utc),
            "generation": 1600.0
        }
    ])

    matched = ingestion_service.match_intervals(
        start_date="2026-01-01",
        end_date="2026-01-01",
        cutoff_preset=CutoffPreset.DA_1100,
        df_actuals=df_actuals,
        df_forecasts=df_forecasts
    )

    # Interval 10:00 should have actualMW = 1500.0, forecastMW = 1600.0, errorMW = +100.0
    row_10 = matched[matched["deliveryInterval"] == datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)].iloc[0]
    assert row_10["actualMW"] == 1500.0
    assert row_10["forecastMW"] == 1600.0
    assert row_10["errorMW"] == 100.0
    assert row_10["status"] == "OVERFORECAST"


def test_missing_intervals_classification():
    """Verify correct status classification for missing actual, forecast, or both."""
    dt_1 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    dt_2 = datetime(2026, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
    dt_3 = datetime(2026, 1, 1, 2, 0, 0, tzinfo=timezone.utc)

    # dt_1 has both, dt_2 has actual only, dt_3 has forecast only, dt_4 has neither
    df_actuals = pd.DataFrame([
        {"startTime": dt_1, "generation": 1000.0},
        {"startTime": dt_2, "generation": 2000.0},
    ])
    df_forecasts = pd.DataFrame([
        {"startTime": dt_1, "publishTime": datetime(2025, 12, 31, 10, 0, 0, tzinfo=timezone.utc), "generation": 1000.0},
        {"startTime": dt_3, "publishTime": datetime(2025, 12, 31, 10, 0, 0, tzinfo=timezone.utc), "generation": 3000.0},
    ])

    matched = ingestion_service.match_intervals(
        start_date="2026-01-01",
        end_date="2026-01-01",
        cutoff_preset=CutoffPreset.DA_1100,
        df_actuals=df_actuals,
        df_forecasts=df_forecasts
    )

    r1 = matched[matched["deliveryInterval"] == dt_1].iloc[0]
    assert r1["status"] == "EXACT_MATCH"

    r2 = matched[matched["deliveryInterval"] == dt_2].iloc[0]
    assert r2["status"] == "MISSING_FORECAST"
    assert r2["actualMW"] == 2000.0
    assert pd.isna(r2["forecastMW"])

    r3 = matched[matched["deliveryInterval"] == dt_3].iloc[0]
    assert r3["status"] == "MISSING_ACTUAL"
    assert pd.isna(r3["actualMW"])
    assert r3["forecastMW"] == 3000.0

    r4 = matched[matched["deliveryInterval"] == datetime(2026, 1, 1, 3, 0, 0, tzinfo=timezone.utc)].iloc[0]
    assert r4["status"] == "MISSING_BOTH"
    assert pd.isna(r4["actualMW"])
    assert pd.isna(r4["forecastMW"])


def test_tie_breaking_highest_generation():
    """Verify that multiple publications with the exact same publishTime pick the highest generation."""
    dt = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    pub = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

    forecasts = pd.DataFrame([
        {"startTime": dt, "publishTime": pub, "generation": 5000.0},
        {"startTime": dt, "publishTime": pub, "generation": 9500.0},
        {"startTime": dt, "publishTime": pub, "generation": 7000.0},
    ])

    selected = select_forecast_as_of(forecasts, dt, datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc))
    assert selected is not None
    assert selected["generation"] == 9500.0


def test_correct_date_boundaries_and_length():
    """Verify that start_date to end_date includes 24 intervals per full day."""
    matched = ingestion_service.match_intervals(
        start_date="2026-01-01",
        end_date="2026-01-03",  # 3 days = 72 hours
        cutoff_preset=CutoffPreset.DA_1100
    )
    assert len(matched) == 72
    assert matched.iloc[0]["deliveryInterval"] == datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert matched.iloc[-1]["deliveryInterval"] == datetime(2026, 1, 3, 23, 0, 0, tzinfo=timezone.utc)


def test_expected_output_schema_and_types():
    """Verify column names and expected types match exactly."""
    matched = ingestion_service.match_intervals("2026-01-01", "2026-01-01", CutoffPreset.DA_1100)
    expected_cols = [
        "deliveryInterval", "actualMW", "forecastMW", "forecastPublishTime",
        "forecastAgeHours", "leadTimeHours", "errorMW", "absErrorMW",
        "pctError", "status", "isEligible"
    ]
    assert list(matched.columns) == expected_cols
    assert isinstance(matched.iloc[0]["isEligible"], (bool, np.bool_))


def test_mathematical_consistency_with_metrics():
    """Verify summary metrics and time-series error calculations are 100% mathematically aligned."""
    matched = ingestion_service.match_intervals("2026-01-01", "2026-01-07", CutoffPreset.DA_1100)
    summary, procurement = calculate_metrics(matched)

    valid = matched[matched["actualMW"].notna() & matched["forecastMW"].notna()]
    assert summary.matchedIntervals == len(valid)

    # MAE check
    expected_mae = round(float(valid["absErrorMW"].mean()), 2)
    assert summary.maeMW == pytest.approx(expected_mae, abs=0.01)

    # Imbalance check
    expected_imbalance = round(float(valid["forecastMW"].sum() - valid["actualMW"].sum()), 1)
    assert procurement.netImbalanceMWh == pytest.approx(expected_imbalance, abs=0.1)


def test_different_delivery_intervals_select_own_forecasts():
    """Ensure delivery intervals do not leak forecasts across different hours."""
    dt1 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    dt2 = datetime(2026, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

    df_forecasts = pd.DataFrame([
        {"startTime": dt1, "publishTime": datetime(2025, 12, 31, 10, 0, 0, tzinfo=timezone.utc), "generation": 4000.0},
        {"startTime": dt2, "publishTime": datetime(2025, 12, 31, 10, 0, 0, tzinfo=timezone.utc), "generation": 8000.0},
    ])

    matched = ingestion_service.match_intervals(
        start_date="2026-01-01",
        end_date="2026-01-01",
        cutoff_preset=CutoffPreset.DA_1100,
        df_forecasts=df_forecasts
    )

    r1 = matched[matched["deliveryInterval"] == dt1].iloc[0]
    r2 = matched[matched["deliveryInterval"] == dt2].iloc[0]
    assert r1["forecastMW"] == 4000.0
    assert r2["forecastMW"] == 8000.0


def test_empty_forecast_dataset():
    """Verify empty forecast dataset is handled gracefully without exception."""
    df_empty = pd.DataFrame(columns=["startTime", "publishTime", "generation"])
    matched = ingestion_service.match_intervals(
        start_date="2026-01-01",
        end_date="2026-01-01",
        df_forecasts=df_empty
    )
    assert len(matched) == 24
    assert matched["forecastMW"].isna().all()
    assert (matched["isEligible"] == False).all()
