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

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface QueryFilters {
  startDate: string;
  endDate: string;
  cutoffPreset: CutoffPresetId;
  customCutoff?: string;
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
  },

  async getMetadata(): Promise<MetadataResponse> {
    const res = await fetch(`${API_BASE}/metadata`);
    if (!res.ok) throw new Error(`Failed to load metadata: ${res.statusText}`);
    return res.json();
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
    if (!res.ok) throw new Error(`Failed to fetch summary: ${res.statusText}`);
    return res.json();
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
    if (!res.ok) throw new Error(`Failed to fetch timeseries: ${res.statusText}`);
    return res.json();
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
    if (!res.ok) throw new Error(`Failed to fetch daily summary: ${res.statusText}`);
    return res.json();
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
    if (!res.ok) throw new Error(`Failed to fetch diurnal breakdown: ${res.statusText}`);
    return res.json();
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
    if (!res.ok) throw new Error(`Failed to fetch error distribution: ${res.statusText}`);
    return res.json();
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
    if (!res.ok) throw new Error(`Failed to fetch forecast table: ${res.statusText}`);
    return res.json();
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
