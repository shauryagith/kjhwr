from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from app.schemas.analytics import (
    SummaryMetrics,
    TimeseriesPoint,
    DailySummaryItem,
    DiurnalAccuracyItem,
    ErrorDistributionBucket,
    ProcurementImpact,
    AnalysisResponse,
)
from app.schemas.forecast import MatchedIntervalItem


def calculate_metrics(df_matched: pd.DataFrame) -> Tuple[SummaryMetrics, ProcurementImpact]:
    """
    Calculate summary forecasting and procurement metrics from matched intervals dataframe.
    Required columns in df_matched: 'actualMW', 'forecastMW', 'errorMW', 'absErrorMW'.
    """
    total_intervals = len(df_matched)
    if total_intervals == 0:
        return (
            SummaryMetrics(
                totalIntervals=0,
                matchedIntervals=0,
                missingActualIntervals=0,
                missingForecastIntervals=0,
                dataCoveragePct=0.0
            ),
            ProcurementImpact(
                totalOverforecastMWh=0.0,
                totalUnderforecastMWh=0.0,
                netImbalanceMWh=0.0,
                overforecastRiskSummary="No data available to calculate volume risks.",
                underforecastRiskSummary="No data available to calculate volume risks.",
                guidanceNotes=[]
            )
        )
    
    # Valid matched pairs where both actual and forecast exist
    valid_mask = df_matched['actualMW'].notna() & df_matched['forecastMW'].notna()
    df_valid = df_matched[valid_mask]
    matched_count = len(df_valid)
    
    missing_actual = int(df_matched['actualMW'].isna().sum())
    missing_forecast = int(df_matched['forecastMW'].isna().sum())
    coverage_pct = round((matched_count / total_intervals) * 100.0, 2)
    
    if matched_count == 0:
        return (
            SummaryMetrics(
                totalIntervals=total_intervals,
                matchedIntervals=0,
                missingActualIntervals=missing_actual,
                missingForecastIntervals=missing_forecast,
                dataCoveragePct=coverage_pct
            ),
            ProcurementImpact(
                totalOverforecastMWh=0.0,
                totalUnderforecastMWh=0.0,
                netImbalanceMWh=0.0,
                overforecastRiskSummary="No valid matched actual and forecast records in interval range.",
                underforecastRiskSummary="No valid matched actual and forecast records in interval range.",
                guidanceNotes=["Ensure the selected date range has valid Elexon actual and forecast data."]
            )
        )
        
    actuals = df_valid['actualMW'].values
    forecasts = df_valid['forecastMW'].values
    errors = forecasts - actuals  # Error = F - A
    abs_errors = np.abs(errors)
    
    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    bias = float(np.mean(errors))
    
    # WAPE = sum(|F - A|) / sum(A) * 100
    sum_actual = float(np.sum(actuals))
    if sum_actual > 0:
        wape = round(float((np.sum(abs_errors) / sum_actual) * 100.0), 2)
    else:
        wape = None  # Zero actual generation across the entire range
        
    # Over / Under forecast counts
    # Using a 1 MW threshold to account for floating point exactness
    over_mask = errors > 1.0
    under_mask = errors < -1.0
    exact_mask = np.abs(errors) <= 1.0
    
    over_count = int(np.sum(over_mask))
    under_count = int(np.sum(under_mask))
    exact_count = int(np.sum(exact_mask))
    
    over_freq = round((over_count / matched_count) * 100.0, 2)
    under_freq = round((under_count / matched_count) * 100.0, 2)
    
    max_over = float(np.max(errors)) if len(errors) > 0 else 0.0
    min_error = float(np.min(errors)) if len(errors) > 0 else 0.0
    # max underforecast is magnitude of minimum negative error
    max_under = abs(min_error) if min_error < 0 else 0.0
    
    mean_actual = float(np.mean(actuals))
    mean_forecast = float(np.mean(forecasts))
    
    # Energy assuming 1 hour per interval (MW * 1h = MWh, / 1000 = GWh)
    total_actual_gwh = round(float(sum_actual / 1000.0), 2)
    total_forecast_gwh = round(float(np.sum(forecasts) / 1000.0), 2)
    
    # Procurement impact
    over_energy_mwh = float(np.sum(errors[over_mask]))
    under_energy_mwh = float(np.sum(abs_errors[under_mask]))
    net_imbalance_mwh = float(np.sum(forecasts) - np.sum(actuals))
    
    summary = SummaryMetrics(
        totalIntervals=total_intervals,
        matchedIntervals=matched_count,
        missingActualIntervals=missing_actual,
        missingForecastIntervals=missing_forecast,
        dataCoveragePct=coverage_pct,
        maeMW=round(mae, 2),
        rmseMW=round(rmse, 2),
        biasMW=round(bias, 2),
        wapePct=wape,
        maxOverforecastMW=round(max_over, 2),
        maxUnderforecastMW=round(max_under, 2),
        overforecastCount=over_count,
        underforecastCount=under_count,
        exactMatchCount=exact_count,
        overforecastFrequencyPct=over_freq,
        underforecastFrequencyPct=under_freq,
        meanActualMW=round(mean_actual, 2),
        meanForecastMW=round(mean_forecast, 2),
        totalActualGWh=total_actual_gwh,
        totalForecastGWh=total_forecast_gwh
    )
    
    guidance = [
        "Procurement Warning: Wind generation alone does NOT determine net utility procurement.",
        "Total procurement volume must account for consumer demand, thermal contracts, storage, and interconnector positions.",
        f"Overforecasting occurred in {over_freq}% of intervals, generating {over_energy_mwh:,.0f} MWh of prospective short positions.",
        f"Underforecasting occurred in {under_freq}% of intervals, generating {under_energy_mwh:,.0f} MWh of prospective long positions."
    ]
    
    procurement = ProcurementImpact(
        totalOverforecastMWh=round(over_energy_mwh, 1),
        totalUnderforecastMWh=round(under_energy_mwh, 1),
        netImbalanceMWh=round(net_imbalance_mwh, 1),
        overforecastRiskSummary=(
            f"Overforecasting ({over_freq}% frequency) creates risk of a short physical position in the day-ahead market. "
            "If actual wind falls short of day-ahead purchases, the utility faces expensive cash-out at National Grid ESO System Buy Price (SBP) "
            "or must buy intraday power at a premium."
        ),
        underforecastRiskSummary=(
            f"Underforecasting ({under_freq}% frequency) creates a prospective long position where more wind was generated than contracted. "
            "Excess power spills or is sold at System Sell Price (SSP) discounts or curtailment compensations."
        ),
        guidanceNotes=guidance
    )
    
    return summary, procurement


def calculate_daily_summary(df_matched: pd.DataFrame) -> List[DailySummaryItem]:
    """Calculate daily breakdown of forecasting performance."""
    if df_matched.empty:
        return []
        
    df = df_matched.copy()
    df['date'] = df['deliveryInterval'].dt.strftime('%Y-%m-%d')
    
    daily_items = []
    for date_str, group in df.groupby('date'):
        total_exp = len(group)
        valid = group[group['actualMW'].notna() & group['forecastMW'].notna()]
        matched = len(valid)
        coverage = round((matched / total_exp) * 100.0, 1) if total_exp > 0 else 0.0
        
        if matched > 0:
            act = valid['actualMW'].values
            fc = valid['forecastMW'].values
            err = fc - act
            abs_err = np.abs(err)
            mae = float(np.mean(abs_err))
            rmse = float(np.sqrt(np.mean(err ** 2)))
            bias = float(np.mean(err))
            sum_act = float(np.sum(act))
            wape = round((float(np.sum(abs_err)) / sum_act) * 100.0, 2) if sum_act > 0 else None
            
            daily_items.append(DailySummaryItem(
                date=date_str,
                matchedIntervals=matched,
                totalExpectedIntervals=total_exp,
                coveragePct=coverage,
                maeMW=round(mae, 2),
                rmseMW=round(rmse, 2),
                biasMW=round(bias, 2),
                wapePct=wape,
                meanActualMW=round(float(np.mean(act)), 2),
                meanForecastMW=round(float(np.mean(fc)), 2),
                totalActualMWh=round(sum_act, 1),
                totalForecastMWh=round(float(np.sum(fc)), 1)
            ))
        else:
            daily_items.append(DailySummaryItem(
                date=date_str,
                matchedIntervals=0,
                totalExpectedIntervals=total_exp,
                coveragePct=0.0
            ))
            
    return sorted(daily_items, key=lambda x: x.date)


def calculate_diurnal_accuracy(df_matched: pd.DataFrame) -> List[DiurnalAccuracyItem]:
    """Calculate diurnal accuracy profile by hour of the day (0-23)."""
    if df_matched.empty:
        return []
        
    df = df_matched.copy()
    valid = df[df['actualMW'].notna() & df['forecastMW'].notna()].copy()
    if valid.empty:
        return []
        
    valid['hourOfDay'] = valid['deliveryInterval'].dt.hour
    diurnal_items = []
    
    for h in range(24):
        sub = valid[valid['hourOfDay'] == h]
        if not sub.empty:
            act = sub['actualMW'].values
            fc = sub['forecastMW'].values
            err = fc - act
            abs_err = np.abs(err)
            
            diurnal_items.append(DiurnalAccuracyItem(
                hourOfDay=h,
                count=len(sub),
                maeMW=round(float(np.mean(abs_err)), 2),
                rmseMW=round(float(np.sqrt(np.mean(err ** 2))), 2),
                biasMW=round(float(np.mean(err)), 2),
                meanActualMW=round(float(np.mean(act)), 2),
                meanForecastMW=round(float(np.mean(fc)), 2)
            ))
        else:
            diurnal_items.append(DiurnalAccuracyItem(
                hourOfDay=h,
                count=0,
                maeMW=0.0,
                rmseMW=0.0,
                biasMW=0.0,
                meanActualMW=0.0,
                meanForecastMW=0.0
            ))
            
    return diurnal_items


def calculate_error_distribution(df_matched: pd.DataFrame) -> List[ErrorDistributionBucket]:
    """Calculate histogram distribution buckets for signed error (F - A)."""
    valid = df_matched[df_matched['actualMW'].notna() & df_matched['forecastMW'].notna()]
    if valid.empty:
        return []
        
    errors = (valid['forecastMW'] - valid['actualMW']).values
    total_valid = len(errors)
    
    # Standard energy industry error buckets in MW
    bucket_defs = [
        (-float('inf'), -4000.0, "Severe Under (< -4 GW)"),
        (-4000.0, -2000.0, "-4 GW to -2 GW"),
        (-2000.0, -1000.0, "-2 GW to -1 GW"),
        (-1000.0, -500.0, "-1 GW to -500 MW"),
        (-500.0, 500.0, "Accurate (-500 to +500 MW)"),
        (500.0, 1000.0, "+500 MW to +1 GW"),
        (1000.0, 2000.0, "+1 GW to +2 GW"),
        (2000.0, 4000.0, "+2 GW to +4 GW"),
        (4000.0, float('inf'), "Severe Over (> +4 GW)")
    ]
    
    distribution = []
    for low, high, label in bucket_defs:
        if low == -float('inf'):
            count = int(np.sum(errors < high))
        elif high == float('inf'):
            count = int(np.sum(errors >= low))
        else:
            count = int(np.sum((errors >= low) & (errors < high)))
            
        freq = round((count / total_valid) * 100.0, 2) if total_valid > 0 else 0.0
        distribution.append(ErrorDistributionBucket(
            binStartMW=-99999.0 if math.isinf(low) else low,
            binEndMW=99999.0 if math.isinf(high) else high,
            label=label,
            count=count,
            frequencyPct=freq
        ))
        
    return distribution
