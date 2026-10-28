from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
import io
import csv
import pandas as pd

from app.schemas.common import (
    HealthResponse,
    MetadataResponse,
    CutoffPreset,
    APIError
)
from app.schemas.analytics import (
    AnalysisResponse,
    SummaryMetrics,
    TimeseriesPoint,
    DailySummaryItem,
    DiurnalAccuracyItem,
    ErrorDistributionBucket,
    ProcurementImpact,
    ForecastTableResponse
)
from app.schemas.forecast import ForecastItem, ActualItem, MatchedIntervalItem
from app.services.ingestion import ingestion_service
from app.services.analysis import (
    calculate_metrics,
    calculate_daily_summary,
    calculate_diurnal_accuracy,
    calculate_error_distribution
)
from app.services.elexon_client import ElexonClient
from app.repositories.data_store import data_store
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/api/v1", tags=["Wind Forecast Analytics"])
elexon_client = ElexonClient()

# In-memory query cache for matched intervals: (start_date, end_date, preset_str, custom_cutoff) -> DataFrame
_matched_cache: Dict[Tuple[str, str, str, Optional[str]], pd.DataFrame] = {}


def clear_matched_cache() -> None:
    """Clear in-memory matched DataFrame cache."""
    global _matched_cache
    _matched_cache.clear()


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """System health check and upstream Elexon status."""
    is_live = await elexon_client.ping_health()
    stats = data_store.get_stats()
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
        elexon_live_accessible=is_live,
        data_cache_available=data_store.has_data(),
        data_points_cached={
            "actuals": stats["actualsCount"],
            "forecasts": stats["forecastsCount"]
        }
    )


@router.get("/health/live")
async def get_health_live():
    """Fast, lightweight liveness check for container orchestrators without external dependency checks."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cache_ready": data_store.has_data()
    }


@router.get("/metadata", response_model=MetadataResponse)
async def get_metadata():
    """Application metadata, market rules, and supported configuration."""
    return MetadataResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        dataset_actual="FUELHH (fuelType=WIND, national GB sum)",
        dataset_forecast="WINDFOR (national GB wind generation forecast)",
        settlement_interval_minutes=30,
        forecast_interval_minutes=60,
        default_date_range={"start": settings.default_start_date, "end": settings.default_end_date},
        supported_cutoff_presets=[
            {"id": "DA_1100", "label": "Day-Ahead 11:00 UK Time", "description": "Standard EPEX SPOT & Nord Pool GB Day-Ahead Auction gate closure."},
            {"id": "DA_1200", "label": "Day-Ahead 12:00 UK Time", "description": "Standard European Day-Ahead portfolio locking deadline."},
            {"id": "DA_1700", "label": "Day-Ahead 17:00 UK Time", "description": "End of business day prior to delivery."},
            {"id": "DA_2300", "label": "Day-Ahead 23:00 UK Time", "description": "Midnight prior to delivery day."},
            {"id": "ROLLING_24H", "label": "Rolling 24h Before Delivery", "description": "Strict 24-hour lookahead horizon."},
            {"id": "ROLLING_12H", "label": "Rolling 12h Before Delivery", "description": "Intraday initial planning cutoff."},
            {"id": "ROLLING_6H", "label": "Rolling 6h Before Delivery", "description": "Near-term operational gate."},
            {"id": "ROLLING_2H", "label": "Rolling 2h Before Delivery", "description": "Balancing Mechanism pre-gate closure."}
        ],
        market_notes=(
            "Analysis focuses exclusively on official Elexon FUELHH and WINDFOR streams. "
            "Wind forecasts are matched with actual generation at 1-hour resolution (arithmetic mean of settlement half-hours). "
            "No synthetic pricing, consumer demand, or financial forecasts are fabricated."
        )
    )


def _get_matched_df(
    start_date: str,
    end_date: str,
    cutoff_preset: CutoffPreset | str,
    custom_cutoff: Optional[str] = None
) -> pd.DataFrame:
    """Helper to validate dates and retrieve matched DataFrame with LRU in-memory caching."""
    try:
        s_dt = datetime.strptime(start_date, "%Y-%m-%d")
        e_dt = datetime.strptime(end_date, "%Y-%m-%d")
        if s_dt > e_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be less than or equal to end_date."
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dates must be in YYYY-MM-DD format."
        )

    c_dt = None
    if custom_cutoff:
        try:
            c_dt = datetime.fromisoformat(custom_cutoff.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="custom_cutoff must be an ISO-8601 formatted datetime string."
            )

    preset_key = cutoff_preset.value if isinstance(cutoff_preset, CutoffPreset) else str(cutoff_preset)
    cache_key = (start_date, end_date, preset_key, custom_cutoff)
    if cache_key in _matched_cache:
        return _matched_cache[cache_key].copy()

    matched_df = ingestion_service.match_intervals(
        start_date=start_date,
        end_date=end_date,
        cutoff_preset=cutoff_preset,
        custom_cutoff=c_dt
    )

    # Store bounded cache entry
    if len(_matched_cache) >= 64:
        # Evict oldest entry
        first_key = next(iter(_matched_cache))
        del _matched_cache[first_key]
    _matched_cache[cache_key] = matched_df

    return matched_df.copy()


@router.get("/analysis/summary", response_model=Dict[str, Any])
async def get_analysis_summary(
    start_date: str = Query(settings.default_start_date, description="Start date YYYY-MM-DD"),
    end_date: str = Query(settings.default_end_date, description="End date YYYY-MM-DD"),
    cutoff_preset: CutoffPreset = Query(CutoffPreset.DA_1100, description="Decision cutoff preset"),
    custom_cutoff: Optional[str] = Query(None, description="Optional custom ISO cutoff datetime")
):
    """Retrieve high-level summary KPIs (MAE, RMSE, Bias, WAPE, volume risks)."""
    df_matched = _get_matched_df(start_date, end_date, cutoff_preset, custom_cutoff)
    summary, procurement = calculate_metrics(df_matched)
    return {
        "startDate": start_date,
        "endDate": end_date,
        "cutoffPreset": cutoff_preset.value,
        "summary": summary,
        "procurementImpact": procurement
    }


@router.get("/analysis/timeseries", response_model=List[TimeseriesPoint])
async def get_analysis_timeseries(
    start_date: str = Query(settings.default_start_date, description="Start date YYYY-MM-DD"),
    end_date: str = Query(settings.default_end_date, description="End date YYYY-MM-DD"),
    cutoff_preset: CutoffPreset = Query(CutoffPreset.DA_1100, description="Decision cutoff preset"),
    custom_cutoff: Optional[str] = Query(None, description="Optional custom ISO cutoff datetime")
):
    """Retrieve actual vs forecast time-series points with errors and publication timestamps."""
    df_matched = _get_matched_df(start_date, end_date, cutoff_preset, custom_cutoff)
    points = [
        TimeseriesPoint(
            timestamp=row.deliveryInterval,
            actualMW=row.actualMW if pd.notna(row.actualMW) else None,
            forecastMW=row.forecastMW if pd.notna(row.forecastMW) else None,
            errorMW=row.errorMW if pd.notna(row.errorMW) else None,
            absErrorMW=row.absErrorMW if pd.notna(row.absErrorMW) else None,
            forecastPublishTime=row.forecastPublishTime if pd.notna(row.forecastPublishTime) else None,
            isOverforecast=bool(row.errorMW > 1.0) if (pd.notna(row.errorMW) and row.errorMW is not None) else None
        )
        for row in df_matched.itertuples(index=False)
    ]
    return points


@router.get("/analysis/daily", response_model=List[DailySummaryItem])
async def get_analysis_daily(
    start_date: str = Query(settings.default_start_date, description="Start date YYYY-MM-DD"),
    end_date: str = Query(settings.default_end_date, description="End date YYYY-MM-DD"),
    cutoff_preset: CutoffPreset = Query(CutoffPreset.DA_1100, description="Decision cutoff preset"),
    custom_cutoff: Optional[str] = Query(None, description="Optional custom ISO cutoff datetime")
):
    """Retrieve daily accuracy summaries across the requested month."""
    df_matched = _get_matched_df(start_date, end_date, cutoff_preset, custom_cutoff)
    return calculate_daily_summary(df_matched)


@router.get("/analysis/diurnal", response_model=List[DiurnalAccuracyItem])
async def get_analysis_diurnal(
    start_date: str = Query(settings.default_start_date, description="Start date YYYY-MM-DD"),
    end_date: str = Query(settings.default_end_date, description="End date YYYY-MM-DD"),
    cutoff_preset: CutoffPreset = Query(CutoffPreset.DA_1100, description="Decision cutoff preset"),
    custom_cutoff: Optional[str] = Query(None, description="Optional custom ISO cutoff datetime")
):
    """Retrieve 24-hour diurnal accuracy breakdown (hour-of-day bias and MAE)."""
    df_matched = _get_matched_df(start_date, end_date, cutoff_preset, custom_cutoff)
    return calculate_diurnal_accuracy(df_matched)


@router.get("/analysis/errors", response_model=List[ErrorDistributionBucket])
async def get_analysis_errors(
    start_date: str = Query(settings.default_start_date, description="Start date YYYY-MM-DD"),
    end_date: str = Query(settings.default_end_date, description="End date YYYY-MM-DD"),
    cutoff_preset: CutoffPreset = Query(CutoffPreset.DA_1100, description="Decision cutoff preset"),
    custom_cutoff: Optional[str] = Query(None, description="Optional custom ISO cutoff datetime")
):
    """Retrieve error histogram distribution buckets around zero baseline."""
    df_matched = _get_matched_df(start_date, end_date, cutoff_preset, custom_cutoff)
    return calculate_error_distribution(df_matched)


@router.get("/analysis/forecast-table", response_model=ForecastTableResponse)
async def get_forecast_table(
    start_date: str = Query(settings.default_start_date, description="Start date YYYY-MM-DD"),
    end_date: str = Query(settings.default_end_date, description="End date YYYY-MM-DD"),
    cutoff_preset: CutoffPreset = Query(CutoffPreset.DA_1100, description="Decision cutoff preset"),
    custom_cutoff: Optional[str] = Query(None, description="Optional custom ISO cutoff datetime"),
    status_filter: Optional[str] = Query(None, description="Filter by status: OVERFORECAST, UNDERFORECAST, etc."),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Page size"),
    sort_by: str = Query("deliveryInterval", description="Column to sort by"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$", description="Sort direction")
):
    """Paginated, sortable and filterable table of individual delivery intervals."""
    df_matched = _get_matched_df(start_date, end_date, cutoff_preset, custom_cutoff)

    if status_filter:
        df_matched = df_matched[df_matched["status"] == status_filter]

    ascending = (sort_dir == "asc")
    if sort_by in df_matched.columns:
        df_matched = df_matched.sort_values(by=sort_by, ascending=ascending)

    total_count = len(df_matched)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    df_slice = df_matched.iloc[start_idx:end_idx]

    items = [
        MatchedIntervalItem(
            deliveryInterval=row.deliveryInterval,
            actualMW=row.actualMW if pd.notna(row.actualMW) else None,
            forecastMW=row.forecastMW if pd.notna(row.forecastMW) else None,
            forecastPublishTime=row.forecastPublishTime if pd.notna(row.forecastPublishTime) else None,
            forecastAgeHours=row.forecastAgeHours if pd.notna(row.forecastAgeHours) else None,
            leadTimeHours=row.leadTimeHours if pd.notna(row.leadTimeHours) else None,
            errorMW=row.errorMW if pd.notna(row.errorMW) else None,
            absErrorMW=row.absErrorMW if pd.notna(row.absErrorMW) else None,
            pctError=row.pctError if pd.notna(row.pctError) else None,
            status=str(row.status),
            isEligible=bool(row.isEligible)
        )
        for row in df_slice.itertuples(index=False)
    ]

    return ForecastTableResponse(
        total=total_count,
        page=page,
        pageSize=page_size,
        items=items
    )


@router.get("/analysis/export-csv")
async def export_analysis_csv(
    start_date: str = Query(settings.default_start_date, description="Start date YYYY-MM-DD"),
    end_date: str = Query(settings.default_end_date, description="End date YYYY-MM-DD"),
    cutoff_preset: CutoffPreset = Query(CutoffPreset.DA_1100, description="Decision cutoff preset"),
    custom_cutoff: Optional[str] = Query(None, description="Optional custom ISO cutoff datetime")
):
    """Export matched wind forecast and actual observations as a CSV file."""
    df_matched = _get_matched_df(start_date, end_date, cutoff_preset, custom_cutoff)

    stream = io.StringIO()
    writer = csv.writer(stream)

    # Headers
    writer.writerow([
        "Delivery Interval (UTC)",
        "Actual Wind Generation (MW)",
        "Selected Forecast Generation (MW)",
        "Forecast Publish Time (UTC)",
        "Forecast Age at Cutoff (Hours)",
        "Lead Time to Delivery (Hours)",
        "Signed Error (Forecast - Actual, MW)",
        "Absolute Error (MW)",
        "Percentage Error (%)",
        "Interval Status"
    ])

    for row in df_matched.itertuples(index=False):
        writer.writerow([
            row.deliveryInterval.isoformat() if pd.notna(row.deliveryInterval) else "",
            row.actualMW if pd.notna(row.actualMW) else "",
            row.forecastMW if pd.notna(row.forecastMW) else "",
            row.forecastPublishTime.isoformat() if pd.notna(row.forecastPublishTime) else "",
            row.forecastAgeHours if pd.notna(row.forecastAgeHours) else "",
            row.leadTimeHours if pd.notna(row.leadTimeHours) else "",
            row.errorMW if pd.notna(row.errorMW) else "",
            row.absErrorMW if pd.notna(row.absErrorMW) else "",
            row.pctError if pd.notna(row.pctError) else "",
            row.status
        ])

    stream.seek(0)
    filename = f"gridbricks_wind_analysis_{start_date}_{end_date}_{cutoff_preset.value}.csv"
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/analysis/refresh")
async def refresh_dataset(
    year: int = Query(2026, ge=2020, le=2030),
    month: int = Query(1, ge=1, le=12)
):
    """Trigger manual re-ingestion of wind actuals and forecasts from Elexon BMRS."""
    try:
        clear_matched_cache()
        act_count, fc_count = await ingestion_service.fetch_month_data(year=year, month=month, force_refresh=True)
        return {
            "status": "success",
            "message": f"Successfully re-ingested data for {year}-{month:02d}.",
            "actualsCached": act_count,
            "forecastsCached": fc_count,
            "refreshedAt": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to refresh dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch updated data from upstream Elexon API: {str(e)}"
        )
