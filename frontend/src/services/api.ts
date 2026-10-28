import {
  HealthResponse,
  MetadataResponse,
  SummaryMetrics,
  ProcurementImpact,
  TimeseriesPoint,
  DailySummaryItem,
  DiurnalAccuracyItem,
  ErrorDistributionBucket,
  ForecastTableResponse,
  CutoffPresetId,
} from '../types';

export const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/+$/, '');

async function handleResponse<T>(res: Response, fallbackError: string): Promise<T> {
  if (!res.ok) {
    let detail = '';
    try {
      const errJson = await res.json();
      detail = errJson?.detail || errJson?.message || '';
    } catch {
      // Non-JSON response
    }
    throw new Error(detail ? `${fallbackError}: ${detail}` : `${fallbackError} (${res.status} ${res.statusText})`);
  }
  return res.json();
}

export interface QueryFilters {
  startDate: string;
  endDate: string;
  cutoffPreset: CutoffPresetId;
  customCutoff?: string;
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<HealthResponse>(res, 'Health check failed');
  },

  async getMetadata(): Promise<MetadataResponse> {
    const res = await fetch(`${API_BASE}/metadata`);
    return handleResponse<MetadataResponse>(res, 'Failed to load metadata');
  },

  async getSummary(filters: QueryFilters): Promise<{
    startDate: string;
    endDate: string;
    cutoffPreset: string;
    summary: SummaryMetrics;
    procurementImpact: ProcurementImpact;
  }> {
    const params = new URLSearchParams({
      start_date: filters.startDate,
      end_date: filters.endDate,
      cutoff_preset: filters.cutoffPreset,
    });
    if (filters.customCutoff) {
      params.append('custom_cutoff', filters.customCutoff);
    }
    const res = await fetch(`${API_BASE}/analysis/summary?${params.toString()}`);
    return handleResponse(res, 'Failed to fetch summary');
  },

  async getTimeseries(filters: QueryFilters): Promise<TimeseriesPoint[]> {
    const params = new URLSearchParams({
      start_date: filters.startDate,
      end_date: filters.endDate,
      cutoff_preset: filters.cutoffPreset,
    });
    if (filters.customCutoff) {
      params.append('custom_cutoff', filters.customCutoff);
    }
    const res = await fetch(`${API_BASE}/analysis/timeseries?${params.toString()}`);
    return handleResponse<TimeseriesPoint[]>(res, 'Failed to fetch timeseries');
  },

  async getDaily(filters: QueryFilters): Promise<DailySummaryItem[]> {
    const params = new URLSearchParams({
      start_date: filters.startDate,
      end_date: filters.endDate,
      cutoff_preset: filters.cutoffPreset,
    });
    if (filters.customCutoff) {
      params.append('custom_cutoff', filters.customCutoff);
    }
    const res = await fetch(`${API_BASE}/analysis/daily?${params.toString()}`);
    return handleResponse<DailySummaryItem[]>(res, 'Failed to fetch daily summary');
  },

  async getDiurnal(filters: QueryFilters): Promise<DiurnalAccuracyItem[]> {
    const params = new URLSearchParams({
      start_date: filters.startDate,
      end_date: filters.endDate,
      cutoff_preset: filters.cutoffPreset,
    });
    if (filters.customCutoff) {
      params.append('custom_cutoff', filters.customCutoff);
    }
    const res = await fetch(`${API_BASE}/analysis/diurnal?${params.toString()}`);
    return handleResponse<DiurnalAccuracyItem[]>(res, 'Failed to fetch diurnal breakdown');
  },

  async getErrors(filters: QueryFilters): Promise<ErrorDistributionBucket[]> {
    const params = new URLSearchParams({
      start_date: filters.startDate,
      end_date: filters.endDate,
      cutoff_preset: filters.cutoffPreset,
    });
    if (filters.customCutoff) {
      params.append('custom_cutoff', filters.customCutoff);
    }
    const res = await fetch(`${API_BASE}/analysis/errors?${params.toString()}`);
    return handleResponse<ErrorDistributionBucket[]>(res, 'Failed to fetch error distribution');
  },

  async getForecastTable(
    filters: QueryFilters,
    page: number = 1,
    pageSize: number = 50,
    statusFilter?: string,
    sortBy: string = 'deliveryInterval',
    sortDir: 'asc' | 'desc' = 'asc'
  ): Promise<ForecastTableResponse> {
    const params = new URLSearchParams({
      start_date: filters.startDate,
      end_date: filters.endDate,
      cutoff_preset: filters.cutoffPreset,
      page: page.toString(),
      page_size: pageSize.toString(),
      sort_by: sortBy,
      sort_dir: sortDir,
    });
    if (filters.customCutoff) {
      params.append('custom_cutoff', filters.customCutoff);
    }
    if (statusFilter && statusFilter !== 'ALL') {
      params.append('status_filter', statusFilter);
    }
    const res = await fetch(`${API_BASE}/analysis/forecast-table?${params.toString()}`);
    return handleResponse<ForecastTableResponse>(res, 'Failed to fetch forecast table');
  },

  getExportCsvUrl(filters: QueryFilters): string {
    const params = new URLSearchParams({
      start_date: filters.startDate,
      end_date: filters.endDate,
      cutoff_preset: filters.cutoffPreset,
    });
    if (filters.customCutoff) {
      params.append('custom_cutoff', filters.customCutoff);
    }
    return `${API_BASE}/analysis/export-csv?${params.toString()}`;
  },

  async refreshDataset(year: number = 2026, month: number = 1): Promise<{
    status: string;
    message: string;
    actualsCached: number;
    forecastsCached: number;
  }> {
    const res = await fetch(`${API_BASE}/analysis/refresh?year=${year}&month=${month}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`Failed to trigger re-ingestion: ${res.statusText}`);
    return res.json();
  },
};
