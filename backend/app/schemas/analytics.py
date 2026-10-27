from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.forecast import MatchedIntervalItem


class SummaryMetrics(BaseModel):
    totalIntervals: int
    matchedIntervals: int
    missingActualIntervals: int
    missingForecastIntervals: int
    dataCoveragePct: float
    maeMW: Optional[float] = None
    rmseMW: Optional[float] = None
    biasMW: Optional[float] = None  # Mean Error (F - A)
    wapePct: Optional[float] = None  # sum(|F-A|) / sum(A) * 100
    maxOverforecastMW: Optional[float] = None
    maxUnderforecastMW: Optional[float] = None
    overforecastCount: int = 0
    underforecastCount: int = 0
    exactMatchCount: int = 0
    overforecastFrequencyPct: float = 0.0
    underforecastFrequencyPct: float = 0.0
    meanActualMW: Optional[float] = None
    meanForecastMW: Optional[float] = None
    totalActualGWh: Optional[float] = None
    totalForecastGWh: Optional[float] = None


class TimeseriesPoint(BaseModel):
    timestamp: datetime
    actualMW: Optional[float] = None
    forecastMW: Optional[float] = None
    errorMW: Optional[float] = None  # F - A
    absErrorMW: Optional[float] = None
    forecastPublishTime: Optional[datetime] = None
    isOverforecast: Optional[bool] = None


class DailySummaryItem(BaseModel):
    date: str
    matchedIntervals: int
    totalExpectedIntervals: int = 24
    coveragePct: float
    maeMW: Optional[float] = None
    rmseMW: Optional[float] = None
    biasMW: Optional[float] = None
    wapePct: Optional[float] = None
    meanActualMW: Optional[float] = None
    meanForecastMW: Optional[float] = None
    totalActualMWh: Optional[float] = None
    totalForecastMWh: Optional[float] = None


class DiurnalAccuracyItem(BaseModel):
    hourOfDay: int  # 0 - 23
    count: int
    maeMW: float
    rmseMW: float
    biasMW: float
    meanActualMW: float
    meanForecastMW: float


class ErrorDistributionBucket(BaseModel):
    binStartMW: float
    binEndMW: float
    label: str
    count: int
    frequencyPct: float


class ProcurementImpact(BaseModel):
    totalOverforecastMWh: float
    totalUnderforecastMWh: float
    netImbalanceMWh: float  # Forecast MWh - Actual MWh
    overforecastRiskSummary: str
    underforecastRiskSummary: str
    guidanceNotes: List[str]


class AnalysisResponse(BaseModel):
    startDate: str
    endDate: str
    cutoffPreset: str
    cutoffEffectiveDescription: str
    resolution: str = "hourly"
    summary: SummaryMetrics
    procurementImpact: ProcurementImpact
    timeseries: List[TimeseriesPoint]
    dailySummary: List[DailySummaryItem]
    diurnalAccuracy: List[DiurnalAccuracyItem]
    errorDistribution: List[ErrorDistributionBucket]


class ForecastTableResponse(BaseModel):
    total: int
    page: int
    pageSize: int
    items: List[MatchedIntervalItem]
