import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger


class ElexonClient:
    """
    Client for Elexon BMRS API endpoints.
    Endpoints:
      - FUELHH/stream: Half-hourly generation by fuel type (actuals)
      - WINDFOR/stream: Wind generation forecasts
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None
    ):
        self.base_url = (base_url or settings.elexon_base_url).rstrip("/")
        self.timeout = timeout or settings.request_timeout_seconds
        self.max_retries = max_retries or settings.max_retries
        self.backoff_factor = backoff_factor or settings.backoff_factor

        # Health cache & lock to prevent thundering herd and slow synchronous health requests
        self._cached_live_status: Optional[bool] = None
        self._last_live_check: Optional[datetime] = None
        self._cache_ttl_seconds: float = 60.0

    async def _fetch_with_retry(self, endpoint: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute HTTP GET with bounded retries and exponential backoff."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "User-Agent": "Gridbricks-Wind-Analytics/1.0",
            "Accept": "application/json"
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.debug(f"Requesting {url} with params {params} (Attempt {attempt})")
                    resp = await client.get(url, params=params, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()

                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "data" in data:
                        return data["data"]
                    return []
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = exc
                logger.warning(
                    f"Elexon request failed (Attempt {attempt}/{self.max_retries}) to {url}: {exc}"
                )
                if attempt < self.max_retries:
                    sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                    await asyncio.sleep(sleep_time)
            except Exception as exc:
                logger.error(f"Unexpected error while fetching from Elexon: {exc}")
                raise exc

        logger.error(f"Failed to fetch from Elexon after {self.max_retries} attempts: {last_error}")
        raise last_error or RuntimeError("Elexon request failed.")

    async def fetch_fuelhh_wind_stream(
        self,
        from_time: datetime,
        to_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch FUELHH stream data and filter strictly for fuelType == 'WIND'.
        Dates must be ISO-8601 UTC strings.
        """
        from_str = from_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        to_str = to_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        endpoint = "/datasets/FUELHH/stream"
        params = {
            "publishDateTimeFrom": from_str,
            "publishDateTimeTo": to_str
        }

        raw_records = await self._fetch_with_retry(endpoint, params)
        # Filter for national wind generation
        wind_records = [
            r for r in raw_records
            if r.get("fuelType") == "WIND" and "generation" in r and "startTime" in r
        ]
        logger.info(f"Retrieved {len(wind_records)} FUELHH WIND records for {from_str} to {to_str}")
        return wind_records

    async def fetch_windfor_stream(
        self,
        from_time: datetime,
        to_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch WINDFOR wind forecast stream data.
        Dates must be ISO-8601 UTC strings.
        """
        from_str = from_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        to_str = to_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        endpoint = "/datasets/WINDFOR/stream"
        params = {
            "publishDateTimeFrom": from_str,
            "publishDateTimeTo": to_str
        }

        raw_records = await self._fetch_with_retry(endpoint, params)
        valid_records = [
            r for r in raw_records
            if "generation" in r and "startTime" in r and "publishTime" in r
        ]
        logger.info(f"Retrieved {len(valid_records)} WINDFOR forecast records for {from_str} to {to_str}")
        return valid_records

    async def ping_health(self, force: bool = False, timeout_seconds: float = 2.5) -> bool:
        """
        Check if upstream Elexon API is reachable with short, bounded connection timeouts.
        Caches health status for 60 seconds to prevent blocking frequent liveness probes.
        """
        now = datetime.now(timezone.utc)
        if not force and self._cached_live_status is not None and self._last_live_check is not None:
            age = (now - self._last_live_check).total_seconds()
            if age < self._cache_ttl_seconds:
                return self._cached_live_status

        try:
            # Query 1-hour interval for health ping with strict bounded timeout
            from_t = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
            to_t = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            url = f"{self.base_url}/datasets/FUELHH/stream"

            client_timeout = httpx.Timeout(
                connect=min(2.0, timeout_seconds),
                read=timeout_seconds,
                write=2.0,
                pool=2.0
            )
            async with httpx.AsyncClient(timeout=client_timeout) as client:
                resp = await client.get(url, params={"publishDateTimeFrom": from_t, "publishDateTimeTo": to_t})
                is_live = (resp.status_code == 200)
                self._cached_live_status = is_live
                self._last_live_check = now
                return is_live
        except Exception as e:
            logger.warning(f"Elexon health ping failed (non-blocking): {e}")
            self._cached_live_status = False
            self._last_live_check = now
            return False
