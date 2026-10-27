from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ForecastItem(BaseModel):
    startTime: datetime
    publishTime: datetime
    generation: float
    dataset: str = "WINDFOR"


class ActualItem(BaseModel):
    startTime: datetime
    publishTime: Optional[datetime] = None
    settlementDate: Optional[str] = None
    settlementPeriod: Optional[int] = None
    fuelType: str = "WIND"
    generation: float
    dataset: str = "FUELHH"


class MatchedIntervalItem(BaseModel):
    deliveryInterval: datetime
    actualMW: Optional[float] = None
    forecastMW: Optional[float] = None
    forecastPublishTime: Optional[datetime] = None
    forecastAgeHours: Optional[float] = None
    leadTimeHours: Optional[float] = None
    errorMW: Optional[float] = None  # F - A
    absErrorMW: Optional[float] = None  # |F - A|
    pctError: Optional[float] = None  # (|F - A| / A) * 100
    status: str
    isEligible: bool = True
