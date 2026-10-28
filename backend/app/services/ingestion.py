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
        custom_cutoff: Optional[datetime] = None,
        df_actuals: Optional[pd.DataFrame] = None,
        df_forecasts: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Match actual generation with point-in-time forecasts across the requested date range.
        Resolution: 1-hour intervals (standard WINDFOR native resolution).

        Optimized implementation:
        - Uses precomputed indexed lookup tables when default datasets are used.
        - Falls back to vectorized grouping and binary search if custom DataFrames are provided.
        - Binary search (numpy.searchsorted) selects the latest publication on or before the cutoff.
        - Preserves exact point-in-time rules, tie-breaking, schema, and column types.
        """
        start_dt = ensure_utc(datetime.strptime(start_date, "%Y-%m-%d"))
        # End date is inclusive of the full day, so end_dt is next day 00:00:00
        end_dt = ensure_utc(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))

        # Create continuous hourly intervals grid
        hourly_index = pd.date_range(start=start_dt, end=end_dt, freq="1h", inclusive="left", tz=timezone.utc)
        N = len(hourly_index)
        if N == 0:
            return pd.DataFrame(columns=[
                "deliveryInterval", "actualMW", "forecastMW", "forecastPublishTime",
                "forecastAgeHours", "leadTimeHours", "errorMW", "absErrorMW",
                "pctError", "status", "isEligible"
            ])

        # 1. Obtain hourly actuals map and forecast index
        if df_actuals is None and df_forecasts is None:
            actual_hourly_map = data_store.get_actual_hourly_map()
            forecast_index = data_store.get_forecast_index()
        else:
            # Custom datasets provided (e.g., custom unit test fixtures)
            actual_source = df_actuals if df_actuals is not None else data_store.get_actuals(copy=False)
            forecast_source = df_forecasts if df_forecasts is not None else data_store.get_forecasts(copy=False)

            actual_hourly_map: Dict[datetime, float] = {}
            if not actual_source.empty:
                hour_bins = actual_source['startTime'].dt.floor('h')
                grouped_act = actual_source.groupby(hour_bins)['generation'].mean().to_dict()
                actual_hourly_map = {
                    ensure_utc(k.to_pydatetime() if isinstance(k, pd.Timestamp) else k): round(float(v), 2)
                    for k, v in grouped_act.items()
                }

            forecast_index: Dict[datetime, Tuple[np.ndarray, np.ndarray, List[datetime]]] = {}
            if not forecast_source.empty:
                df_fc_sorted = forecast_source.sort_values(
                    by=['startTime', 'publishTime', 'generation'],
                    ascending=[True, True, True]
                )
                for st, group in df_fc_sorted.groupby('startTime'):
                    st_utc = ensure_utc(st.to_pydatetime() if isinstance(st, pd.Timestamp) else st)
                    pub_times_np = group['publishTime'].values.astype('datetime64[ns]')
                    gens_np = group['generation'].values.astype(np.float64)
                    pub_times_dt = [
                        ensure_utc(pt.to_pydatetime() if isinstance(pt, pd.Timestamp) else pt)
                        for pt in group['publishTime']
                    ]
                    forecast_index[st_utc] = (pub_times_np, gens_np, pub_times_dt)

        # 2. Preallocate arrays for O(1) interval population
        act_mw_arr = [None] * N
        fc_mw_arr = [None] * N
        pub_time_arr = [None] * N
        age_h_arr = [None] * N
        lead_h_arr = [None] * N
        is_eligible_arr = [False] * N
        dt_utc_list = [dt.to_pydatetime() for dt in hourly_index]

        # 3. Match each delivery interval
        for i, dt_utc in enumerate(dt_utc_list):
            act = actual_hourly_map.get(dt_utc)
            if act is not None:
                act_mw_arr[i] = act

            cutoff_dt = calculate_decision_cutoff(dt_utc, cutoff_preset, custom_cutoff)
            # Use Timestamp to cleanly match numpy datetime64[ns] in UTC
            cutoff_np = pd.Timestamp(cutoff_dt).to_datetime64()

            group_data = forecast_index.get(dt_utc)
            if group_data is not None:
                pub_times_np, gens_np, pub_times_dt = group_data
                # Binary search finds the latest publication <= cutoff_dt
                # side='right' finds index after all matches, -1 gives the latest eligible index
                idx = np.searchsorted(pub_times_np, cutoff_np, side='right') - 1
                if idx >= 0:
                    fc_mw_arr[i] = float(gens_np[idx])
                    pt = pub_times_dt[idx]
                    pub_time_arr[i] = pt
                    age_h_arr[i] = round(max(0.0, (cutoff_dt - pt).total_seconds() / 3600.0), 2)
                    lead_h_arr[i] = round((dt_utc - pt).total_seconds() / 3600.0, 2)
                    is_eligible_arr[i] = True

        # 4. Vectorized/fast calculation of errors and market statuses
        err_mw_arr = [None] * N
        abs_err_mw_arr = [None] * N
        pct_err_arr = [None] * N
        status_arr = ["VALID"] * N

        for i in range(N):
            act = act_mw_arr[i]
            fc = fc_mw_arr[i]
            if act is not None and fc is not None:
                err = round(fc - act, 2)
                err_mw_arr[i] = err
                abs_err = round(abs(err), 2)
                abs_err_mw_arr[i] = abs_err

                if act > 0:
                    pct_err_arr[i] = round((abs_err / act) * 100.0, 2)
                    if err > 1.0:
                        status_arr[i] = "OVERFORECAST"
                    elif err < -1.0:
                        status_arr[i] = "UNDERFORECAST"
                    else:
                        status_arr[i] = "EXACT_MATCH"
                else:
                    status_arr[i] = "ZERO_ACTUAL"
            elif act is None and fc is None:
                status_arr[i] = "MISSING_BOTH"
            elif act is None:
                status_arr[i] = "MISSING_ACTUAL"
            else:
                status_arr[i] = "MISSING_FORECAST"

        return pd.DataFrame({
            "deliveryInterval": dt_utc_list,
            "actualMW": act_mw_arr,
            "forecastMW": fc_mw_arr,
            "forecastPublishTime": pub_time_arr,
            "forecastAgeHours": age_h_arr,
            "leadTimeHours": lead_h_arr,
            "errorMW": err_mw_arr,
            "absErrorMW": abs_err_mw_arr,
            "pctError": pct_err_arr,
            "status": status_arr,
            "isEligible": is_eligible_arr
        })


ingestion_service = IngestionService()
