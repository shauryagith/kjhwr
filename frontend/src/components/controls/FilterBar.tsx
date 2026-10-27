import React from 'react';
import { Calendar, Clock, RefreshCw, Download, Info } from 'lucide-react';
import { CutoffPresetId, CutoffPresetOption } from '../../types';
import { QueryFilters } from '../../services/api';

interface FilterBarProps {
  filters: QueryFilters;
  onFilterChange: (filters: Partial<QueryFilters>) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
  onExportCsv: () => void;
  cutoffPresets: CutoffPresetOption[];
}

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  onFilterChange,
  onRefresh,
  isRefreshing,
  onExportCsv,
  cutoffPresets,
}) => {
  const currentPreset = cutoffPresets.find((p) => p.id === filters.cutoffPreset);

  const handleQuickPreset = (start: string, end: string) => {
    onFilterChange({ startDate: start, endDate: end });
  };

  return (
    <div className="bg-white border-b border-slate-200 px-4 sm:px-6 lg:px-8 py-3.5 shadow-sm">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Left Side: Date Range & Cutoff Selector */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Date Range Group */}
          <div className="flex items-center space-x-1.5 bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 shadow-xs">
            <Calendar className="w-4 h-4 text-slate-500" />
            <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Delivery:</span>
            <input
              type="date"
              value={filters.startDate}
              min="2026-01-01"
              max="2026-01-31"
              onChange={(e) => onFilterChange({ startDate: e.target.value })}
              className="bg-transparent text-xs font-medium text-slate-800 border-none focus:outline-none focus:ring-0 cursor-pointer"
            />
            <span className="text-xs text-slate-400">to</span>
            <input
              type="date"
              value={filters.endDate}
              min="2026-01-01"
              max="2026-01-31"
              onChange={(e) => onFilterChange({ endDate: e.target.value })}
              className="bg-transparent text-xs font-medium text-slate-800 border-none focus:outline-none focus:ring-0 cursor-pointer"
            />
          </div>

          {/* Quick Date Presets */}
          <div className="hidden xl:flex items-center space-x-1">
            <button
              onClick={() => handleQuickPreset('2026-01-01', '2026-01-31')}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                filters.startDate === '2026-01-01' && filters.endDate === '2026-01-31'
                  ? 'bg-cyan-100 text-cyan-800 font-semibold'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Full Jan
            </button>
            <button
              onClick={() => handleQuickPreset('2026-01-01', '2026-01-07')}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                filters.startDate === '2026-01-01' && filters.endDate === '2026-01-07'
                  ? 'bg-cyan-100 text-cyan-800 font-semibold'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Week 1
            </button>
            <button
              onClick={() => handleQuickPreset('2026-01-08', '2026-01-14')}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                filters.startDate === '2026-01-08' && filters.endDate === '2026-01-14'
                  ? 'bg-cyan-100 text-cyan-800 font-semibold'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Week 2
            </button>
            <button
              onClick={() => handleQuickPreset('2026-01-15', '2026-01-21')}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                filters.startDate === '2026-01-15' && filters.endDate === '2026-01-21'
                  ? 'bg-cyan-100 text-cyan-800 font-semibold'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Week 3
            </button>
            <button
              onClick={() => handleQuickPreset('2026-01-22', '2026-01-31')}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                filters.startDate === '2026-01-22' && filters.endDate === '2026-01-31'
                  ? 'bg-cyan-100 text-cyan-800 font-semibold'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Week 4+
            </button>
          </div>

          {/* Decision Cutoff Selector */}
          <div className="flex items-center space-x-1.5 bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 shadow-xs">
            <Clock className="w-4 h-4 text-cyan-600" />
            <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Cutoff:</span>
            <select
              value={filters.cutoffPreset}
              onChange={(e) => onFilterChange({ cutoffPreset: e.target.value as CutoffPresetId })}
              className="bg-transparent text-xs font-semibold text-slate-800 border-none focus:outline-none focus:ring-0 cursor-pointer pr-1"
            >
              {cutoffPresets.map((preset) => (
                <option key={preset.id} value={preset.id}>
                  {preset.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Right Side: Rationale badge, Export CSV & Refresh */}
        <div className="flex items-center space-x-2.5">
          {currentPreset && (
            <div className="hidden lg:flex items-center space-x-1 text-xs text-slate-500 bg-slate-100/80 px-2.5 py-1 rounded border border-slate-200">
              <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span className="truncate max-w-xs">{currentPreset.description}</span>
            </div>
          )}

          {/* Export CSV */}
          <button
            onClick={onExportCsv}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium rounded-md shadow-xs transition-colors"
            title="Download Matched Interval Observations as CSV"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span className="hidden sm:inline">Export</span> CSV
          </button>

          {/* Refresh / Re-sync */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-navy-800 hover:bg-navy-700 disabled:opacity-50 text-white text-xs font-medium rounded-md shadow-xs transition-colors"
            title="Trigger Elexon re-ingestion"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Re-syncing...' : 'Sync Elexon'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
