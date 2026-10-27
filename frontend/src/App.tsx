import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  Scale,
  Table,
  AlertCircle,
} from 'lucide-react';
import { Header } from './components/layout/Header';
import { FilterBar } from './components/controls/FilterBar';
import { SummaryCards } from './components/analytics/SummaryCards';
import { ActualVsForecastChart } from './components/charts/ActualVsForecastChart';
import { ErrorChart } from './components/charts/ErrorChart';
import { DailySummaryChart } from './components/charts/DailySummaryChart';
import { ErrorDistributionChart } from './components/charts/ErrorDistributionChart';
import { DiurnalChart } from './components/charts/DiurnalChart';
import { ProcurementDecisionSupport } from './components/procurement/ProcurementDecisionSupport';
import { ForecastTable } from './components/explorer/ForecastTable';
import { MethodologyModal } from './components/methodology/MethodologyModal';

import {
  HealthResponse,
  MetadataResponse,
  SummaryMetrics,
  ProcurementImpact,
  TimeseriesPoint,
  DailySummaryItem,
  DiurnalAccuracyItem,
  ErrorDistributionBucket,
  CutoffPresetOption,
} from './types';
import { api, QueryFilters } from './services/api';

const DEFAULT_CUTOFF_PRESETS: CutoffPresetOption[] = [
  { id: 'DA_1100', label: 'Day-Ahead 11:00 UK Time (Auction Default)', description: 'EPEX SPOT & Nord Pool GB Day-Ahead gate closure.' },
  { id: 'DA_1200', label: 'Day-Ahead 12:00 UK Time', description: 'European standard noon position locking.' },
  { id: 'DA_1700', label: 'Day-Ahead 17:00 UK Time', description: 'End of business day-ahead cutoff.' },
  { id: 'DA_2300', label: 'Day-Ahead 23:00 UK Time', description: 'Midnight prior to delivery day.' },
  { id: 'ROLLING_24H', label: 'Rolling 24h Before Delivery', description: 'Strict 24-hour lookahead horizon.' },
  { id: 'ROLLING_12H', label: 'Rolling 12h Before Delivery', description: 'Intraday planning milestone.' },
  { id: 'ROLLING_6H', label: 'Rolling 6h Before Delivery', description: 'Near-term operational gate.' },
  { id: 'ROLLING_2H', label: 'Rolling 2h Before Delivery', description: 'Balancing Mechanism pre-gate.' },
];

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);

  const [filters, setFilters] = useState<QueryFilters>({
    startDate: '2026-01-01',
    endDate: '2026-01-31',
    cutoffPreset: 'DA_1100',
  });

  const [summary, setSummary] = useState<SummaryMetrics | null>(null);
  const [procurement, setProcurement] = useState<ProcurementImpact | null>(null);
  const [timeseries, setTimeseries] = useState<TimeseriesPoint[]>([]);
  const [daily, setDaily] = useState<DailySummaryItem[]>([]);
  const [diurnal, setDiurnal] = useState<DiurnalAccuracyItem[]>([]);
  const [errors, setErrors] = useState<ErrorDistributionBucket[]>([]);

  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'procurement' | 'explorer'>('dashboard');
  const [isMethodologyOpen, setIsMethodologyOpen] = useState(false);

  // Load initial health and metadata
  useEffect(() => {
    const fetchInit = async () => {
      try {
        const [h, m] = await Promise.all([api.getHealth(), api.getMetadata()]);
        setHealth(h);
        setMetadata(m);
      } catch (err) {
        console.warn('Backend not yet reachable on initial load, retrying:', err);
      }
    };
    fetchInit();
  }, []);

  // Fetch analytical data on filter change
  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [sumRes, tsRes, dailyRes, diurnalRes, errRes] = await Promise.all([
        api.getSummary(filters),
        api.getTimeseries(filters),
        api.getDaily(filters),
        api.getDiurnal(filters),
        api.getErrors(filters),
      ]);

      setSummary(sumRes.summary);
      setProcurement(sumRes.procurementImpact);
      setTimeseries(tsRes);
      setDaily(dailyRes);
      setDiurnal(diurnalRes);
      setErrors(errRes);
    } catch (err: any) {
      console.error('Error fetching analytics:', err);
      setErrorMessage(err.message || 'Failed to load analytics data from backend.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const handleFilterChange = (newFilters: Partial<QueryFilters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  };

  const handleExportCsv = () => {
    window.location.href = api.getExportCsvUrl(filters);
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await api.refreshDataset(2026, 1);
      const h = await api.getHealth();
      setHealth(h);
      await loadAnalytics();
    } catch (err: any) {
      alert(`Re-sync failed: ${err.message}`);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Header */}
      <Header health={health} onOpenMethodology={() => setIsMethodologyOpen(true)} />

      {/* Filter and Control Bar */}
      <FilterBar
        filters={filters}
        onFilterChange={handleFilterChange}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
        onExportCsv={handleExportCsv}
        cutoffPresets={metadata?.supported_cutoff_presets || DEFAULT_CUTOFF_PRESETS}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Navigation Tabs */}
        <div className="flex items-center space-x-1 border-b border-slate-200 mb-6 pb-px">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
              activeTab === 'dashboard'
                ? 'border-cyan-600 text-cyan-900 bg-white shadow-xs'
                : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-100/50'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Executive Dashboard</span>
          </button>

          <button
            onClick={() => setActiveTab('procurement')}
            className={`flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
              activeTab === 'procurement'
                ? 'border-cyan-600 text-cyan-900 bg-white shadow-xs'
                : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-100/50'
            }`}
          >
            <Scale className="w-4 h-4" />
            <span>Procurement Decision Support</span>
          </button>

          <button
            onClick={() => setActiveTab('explorer')}
            className={`flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
              activeTab === 'explorer'
                ? 'border-cyan-600 text-cyan-900 bg-white shadow-xs'
                : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-100/50'
            }`}
          >
            <Table className="w-4 h-4" />
            <span>Forecast Explorer (Table)</span>
          </button>
        </div>

        {/* Global Error Banner if any */}
        {errorMessage && (
          <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start space-x-3 text-xs">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-semibold block mb-0.5">API Request Error</span>
              <p>{errorMessage}</p>
            </div>
            <button
              onClick={loadAnalytics}
              className="px-2.5 py-1 bg-white border border-rose-300 rounded font-medium hover:bg-rose-100 transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {/* Executive Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div>
            {/* KPI Summary Cards */}
            <SummaryCards metrics={summary} loading={loading} />

            {/* Actual vs Forecast Time Series */}
            <ActualVsForecastChart data={timeseries} loading={loading} />

            {/* Signed Error Bar Chart */}
            <ErrorChart data={timeseries} loading={loading} />

            {/* 3 Secondary Analytical Charts: Daily Summary, Error Distribution, Diurnal Profile */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-6">
              <DailySummaryChart data={daily} loading={loading} />
              <ErrorDistributionChart data={errors} loading={loading} />
              <DiurnalChart data={diurnal} loading={loading} />
            </div>

            {/* Condensed Decision Support Preview */}
            <ProcurementDecisionSupport impact={procurement} metrics={summary} loading={loading} />
          </div>
        )}

        {/* Procurement Support Tab */}
        {activeTab === 'procurement' && (
          <div>
            <ProcurementDecisionSupport impact={procurement} metrics={summary} loading={loading} />
            <SummaryCards metrics={summary} loading={loading} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-6">
              <ErrorDistributionChart data={errors} loading={loading} />
              <DiurnalChart data={diurnal} loading={loading} />
            </div>
          </div>
        )}

        {/* Forecast Explorer Tab */}
        {activeTab === 'explorer' && (
          <div>
            <ForecastTable filters={filters} onExportCsv={handleExportCsv} />
          </div>
        )}
      </main>

      {/* Methodology Modal */}
      <MethodologyModal isOpen={isMethodologyOpen} onClose={() => setIsMethodologyOpen(false)} />

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-700">Gridbricks Submission</span>
            <span>•</span>
            <span>UK Wind Forecast & Day-Ahead Procurement Platform</span>
          </div>
          <div className="flex items-center space-x-4 text-slate-400">
            <span>Official Elexon BMRS Datasets (FUELHH & WINDFOR)</span>
            <span>•</span>
            <button
              onClick={() => setIsMethodologyOpen(true)}
              className="hover:text-slate-600 underline transition-colors"
            >
              Methodology & Conventions
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
