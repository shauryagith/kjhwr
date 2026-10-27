export type CutoffPresetId = 
  | 'DA_1100'
  | 'DA_1200'
  | 'DA_1700'
  | 'DA_2300'
  | 'ROLLING_24H'
  | 'ROLLING_12H'
  | 'ROLLING_6H'
  | 'ROLLING_2H'
  | 'CUSTOM';

export interface CutoffPresetOption {
  id: CutoffPresetId;
  label: string;
  description: string;
}

export interface SummaryMetrics {
  totalIntervals: number;
  matchedIntervals: number;
  missingActualIntervals: number;
  missingForecastIntervals: number;
  dataCoveragePct: number;
  maeMW: number | null;
  rmseMW: number | null;
  biasMW: number | null;
  wapePct: number | null;
  maxOverforecastMW: number | null;
  maxUnderforecastMW: number | null;
  overforecastCount: number;
  underforecastCount: number;
  exactMatchCount: number;
  overforecastFrequencyPct: number;
  underforecastFrequencyPct: number;
  meanActualMW: number | null;
  meanForecastMW: number | null;
  totalActualGWh: number | null;
  totalForecastGWh: number | null;
}

export interface ProcurementImpact {
  totalOverforecastMWh: number;
  totalUnderforecastMWh: number;
  netImbalanceMWh: number;
  overforecastRiskSummary: string;
  underforecastRiskSummary: string;
  guidanceNotes: string[];
}

export interface TimeseriesPoint {
  timestamp: string;
  actualMW: number | null;
  forecastMW: number | null;
  errorMW: number | null;
  absErrorMW: number | null;
  forecastPublishTime: string | null;
  isOverforecast: boolean | null;
}

export interface DailySummaryItem {
  date: string;
  matchedIntervals: number;
  totalExpectedIntervals: number;
  coveragePct: number;
  maeMW: number | null;
  rmseMW: number | null;
  biasMW: number | null;
  wapePct: number | null;
  meanActualMW: number | null;
  meanForecastMW: number | null;
  totalActualMWh: number | null;
  totalForecastMWh: number | null;
}

export interface DiurnalAccuracyItem {
  hourOfDay: number;
  count: number;
  maeMW: number;
  rmseMW: number;
  biasMW: number;
  meanActualMW: number;
  meanForecastMW: number;
}

export interface ErrorDistributionBucket {
  binStartMW: number;
  binEndMW: number;
  label: string;
  count: number;
  frequencyPct: number;
}

export interface MatchedIntervalItem {
  deliveryInterval: string;
  actualMW: number | null;
  forecastMW: number | null;
  forecastPublishTime: string | null;
  forecastAgeHours: number | null;
  leadTimeHours: number | null;
  errorMW: number | null;
  absErrorMW: number | null;
  pctError: number | null;
  status: string;
  isEligible: boolean;
}

export interface ForecastTableResponse {
  total: number;
  page: number;
  pageSize: number;
  items: MatchedIntervalItem[];
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  elexon_live_accessible: boolean;
  data_cache_available: boolean;
  data_points_cached: {
    actuals: number;
    forecasts: number;
  };
}

export interface MetadataResponse {
  app_name: string;
  version: string;
  dataset_actual: string;
  dataset_forecast: string;
  settlement_interval_minutes: number;
  forecast_interval_minutes: number;
  default_date_range: {
    start: string;
    end: string;
  };
  supported_cutoff_presets: CutoffPresetOption[];
  market_notes: string;
}
