from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import asyncio
from app.core.config import settings
from app.core.logging import logger
from app.services.elexon_client import ElexonClient
from app.services.forecast_selection import calculate_decision_cutoff, select_forecast_as_of, ensure_utc
from app.repositories.data_store import data_store
from app.schemas.common import CutoffPreset
from app.schemas.forecast import MatchedIntervalItem


class IngestionService:
    def __init__(self, client: Optional[ElexonClient] = None):
        self.client = client or ElexonClient()

    async def fetch_month_data(
        self,
        year: int = 2026,
        month: int = 1,
        force_refresh: bool = False
    ) -> Tuple[int, int]:
        """
        Fetch January 2026 wind actuals and forecasts from Elexon BMRS.
        Chunks requests by 3-day windows to prevent stream timeouts.
        """
        if not force_refresh and data_store.has_data():
            logger.info("DataStore already populated. Skipping live fetch.")
            stats = data_store.get_stats()
            return stats["actualsCount"], stats["forecastsCount"]

        logger.info(f"Initiating Elexon data ingestion for {year}-{month:02d}...")
        
        # Delivery range
        start_dt = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
        # 31 days in Jan -> end at Feb 1
        end_dt = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        # Forecast publication window needs to start ~3 days earlier (Dec 29) to capture
        # D-1 forecasts for Jan 1st delivery
        fc_start_dt = start_dt - timedelta(days=3)
        fc_end_dt = end_dt + timedelta(hours=12)
        
        actual_records: List[Dict[str, Any]] = []
        forecast_records: List[Dict[str, Any]] = []
        
        # 1. Fetch FUELHH in 3-day chunks
        curr = start_dt
        chunk_days = 3
        while curr < end_dt:
            next_curr = min(curr + timedelta(days=chunk_days), end_dt)
            try:
                # Add buffer for publication delays
                pub_to = next_curr + timedelta(hours=4)
                chunk_actuals = await self.client.fetch_fuelhh_wind_stream(curr, pub_to)
                actual_records.extend(chunk_actuals)
            except Exception as e:
                logger.error(f"Error fetching FUELHH chunk {curr} to {next_curr}: {e}")
            curr = next_curr
            await asyncio.sleep(0.1)  # Mild rate-limiting
            
        # Deduplicate FUELHH by (startTime, settlementPeriod)
        seen_fuelhh = set()
        unique_actuals = []
        for r in actual_records:
            key = (r.get("startTime"), r.get("settlementPeriod"))
            if key not in seen_fuelhh:
                seen_fuelhh.add(key)
                unique_actuals.append(r)
                
        data_store.save_actuals(unique_actuals)
        
        # 2. Fetch WINDFOR in 3-day chunks
        curr_fc = fc_start_dt
        while curr_fc < fc_end_dt:
            next_curr_fc = min(curr_fc + timedelta(days=chunk_days), fc_end_dt)
            try:
                chunk_forecasts = await self.client.fetch_windfor_stream(curr_fc, next_curr_fc)
                forecast_records.extend(chunk_forecasts)
            except Exception as e:
                logger.error(f"Error fetching WINDFOR chunk {curr_fc} to {next_curr_fc}: {e}")
            curr_fc = next_curr_fc
            await asyncio.sleep(0.1)

        # Deduplicate WINDFOR by (startTime, publishTime)
        seen_windfor = set()
        unique_forecasts = []
        for r in forecast_records:
            key = (r.get("startTime"), r.get("publishTime"))
            if key not in seen_windfor:
                seen_windfor.add(key)
                unique_forecasts.append(r)
                
        data_store.save_forecasts(unique_forecasts)
        
        logger.info(
            f"Ingestion completed: {len(unique_actuals)} actuals, {len(unique_forecasts)} forecasts."
        )
        return len(unique_actuals), len(unique_forecasts)

    def match_intervals(
        self,
        start_date: str = "2026-01-01",
        end_date: str = "2026-01-31",
        cutoff_preset: CutoffPreset | str = CutoffPreset.DA_1100,
        custom_cutoff: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Match actual generation with point-in-time forecasts across the requested date range.
        Resolution: 1-hour intervals (standard WINDFOR native resolution).
        """
        df_actuals = data_store.get_actuals()
        df_forecasts = data_store.get_forecasts()
        
        start_dt = ensure_utc(datetime.strptime(start_date, "%Y-%m-%d"))
        # End date is inclusive of the full day, so end_dt is next day 00:00:00
        end_dt = ensure_utc(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
        
        # Create continuous hourly intervals grid
        hourly_index = pd.date_range(start=start_dt, end=end_dt, freq="1h", inclusive="left", tz=timezone.utc)
        
        # Process Actuals: aggregate half-hourly FUELHH to hourly average
        actual_hourly_map: Dict[datetime, float] = {}
        if not df_actuals.empty:
            # Floor startTime to hour
            df_act = df_actuals.copy()
            df_act['hour_bin'] = df_act['startTime'].dt.floor('h')
            # Group by hour and take mean of the settlement periods in that hour
            grouped_act = df_act.groupby('hour_bin')['generation'].mean().to_dict()
            actual_hourly_map = {ensure_utc(k.to_pydatetime()): round(float(v), 2) for k, v in grouped_act.items()}
            
        rows = []
        for delivery_interval in hourly_index:
            dt_utc = delivery_interval.to_pydatetime()
            
            # 1. Actual generation
            act_mw = actual_hourly_map.get(dt_utc)
            
            # 2. Decision cutoff for this delivery interval
            cutoff_dt = calculate_decision_cutoff(dt_utc, cutoff_preset, custom_cutoff)
            
            # 3. Select point-in-time forecast
            selected_fc = select_forecast_as_of(df_forecasts, dt_utc, cutoff_dt)
            
            if selected_fc is not None:
                fc_mw = selected_fc["generation"]
                pub_time = selected_fc["publishTime"]
                age_h = selected_fc["forecastAgeHours"]
                lead_h = selected_fc["leadTimeHours"]
                is_eligible = True
            else:
                fc_mw = None
                pub_time = None
                age_h = None
                lead_h = None
                is_eligible = False
                
            # 4. Error metrics
            err_mw = None
            abs_err_mw = None
            pct_err = None
            status = "VALID"
            
            if act_mw is not None and fc_mw is not None:
                err_mw = round(fc_mw - act_mw, 2)
                abs_err_mw = round(abs(err_mw), 2)
                
                if act_mw > 0:
                    pct_err = round((abs_err_mw / act_mw) * 100.0, 2)
                else:
                    status = "ZERO_ACTUAL"
                    
                if status != "ZERO_ACTUAL":
                    if err_mw > 1.0:
                        status = "OVERFORECAST"
                    elif err_mw < -1.0:
                        status = "UNDERFORECAST"
                    else:
                        status = "EXACT_MATCH"
            elif act_mw is None and fc_mw is None:
                status = "MISSING_BOTH"
            elif act_mw is None:
                status = "MISSING_ACTUAL"
            else:
                status = "MISSING_FORECAST"
                
            rows.append({
                "deliveryInterval": dt_utc,
                "actualMW": act_mw,
                "forecastMW": fc_mw,
                "forecastPublishTime": pub_time,
                "forecastAgeHours": age_h,
                "leadTimeHours": lead_h,
                "errorMW": err_mw,
                "absErrorMW": abs_err_mw,
                "pctError": pct_err,
                "status": status,
                "isEligible": is_eligible
            })
            
        return pd.DataFrame(rows)


ingestion_service = IngestionService()
