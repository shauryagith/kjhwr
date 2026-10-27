import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  Target,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Gauge
} from 'lucide-react';
import { SummaryMetrics } from '../../types';
import { formatNumber, formatPercent } from '../../utils/format';

interface SummaryCardsProps {
  metrics: SummaryMetrics | null;
  loading: boolean;
}

export const SummaryCards: React.FC<SummaryCardsProps> = ({ metrics, loading }) => {
  if (loading || !metrics) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5 mb-6">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs animate-pulse">
            <div className="h-3.5 bg-slate-200 rounded w-20 mb-3" />
            <div className="h-7 bg-slate-200 rounded w-28 mb-2" />
            <div className="h-3 bg-slate-100 rounded w-16" />
          </div>
        ))}
      </div>
    );
  }

  const isOverforecastBias = (metrics.biasMW ?? 0) > 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5 mb-6">
      {/* 1. MAE Card */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
        <div className="flex items-center justify-between text-slate-500 mb-1.5">
          <span className="text-xs font-semibold uppercase tracking-wider">MAE (Mean Error)</span>
          <Target className="w-4 h-4 text-cyan-600" />
        </div>
        <div className="flex items-baseline space-x-1.5">
          <span className="text-2xl font-bold tracking-tight text-slate-900">
            {formatNumber(metrics.maeMW, 2)}
          </span>
          <span className="text-xs font-semibold text-slate-500">MW</span>
        </div>
        <p className="text-[11px] text-slate-500 mt-1">Mean absolute magnitude</p>
      </div>

      {/* 2. RMSE Card */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
        <div className="flex items-center justify-between text-slate-500 mb-1.5">
          <span className="text-xs font-semibold uppercase tracking-wider">RMSE (Penalty)</span>
          <Gauge className="w-4 h-4 text-blue-600" />
        </div>
        <div className="flex items-baseline space-x-1.5">
          <span className="text-2xl font-bold tracking-tight text-slate-900">
            {formatNumber(metrics.rmseMW, 2)}
          </span>
          <span className="text-xs font-semibold text-slate-500">MW</span>
        </div>
        <p className="text-[11px] text-slate-500 mt-1">Penalizes large outlier misses</p>
      </div>

      {/* 3. Bias Card */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
        <div className="flex items-center justify-between text-slate-500 mb-1.5">
          <span className="text-xs font-semibold uppercase tracking-wider">Mean Bias</span>
          {isOverforecastBias ? (
            <TrendingUp className="w-4 h-4 text-amber-500" />
          ) : (
            <TrendingDown className="w-4 h-4 text-cyan-500" />
          )}
        </div>
        <div className="flex items-baseline space-x-1.5">
          <span className={`text-2xl font-bold tracking-tight ${isOverforecastBias ? 'text-amber-700' : 'text-cyan-700'}`}>
            {metrics.biasMW !== null ? (metrics.biasMW > 0 ? `+${formatNumber(metrics.biasMW, 1)}` : formatNumber(metrics.biasMW, 1)) : '—'}
          </span>
          <span className="text-xs font-semibold text-slate-500">MW</span>
        </div>
        <div className="mt-1 flex items-center space-x-1">
          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
            isOverforecastBias ? 'bg-amber-100 text-amber-800' : 'bg-cyan-100 text-cyan-800'
          }`}>
            {isOverforecastBias ? 'Overforecast' : 'Underforecast'}
          </span>
        </div>
      </div>

      {/* 4. WAPE Card */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
        <div className="flex items-center justify-between text-slate-500 mb-1.5">
          <span className="text-xs font-semibold uppercase tracking-wider">WAPE</span>
          <BarChart3 className="w-4 h-4 text-slate-600" />
        </div>
        <div className="flex items-baseline space-x-1.5">
          <span className="text-2xl font-bold tracking-tight text-slate-900">
            {metrics.wapePct !== null ? `${formatNumber(metrics.wapePct, 2)}%` : 'N/A'}
          </span>
        </div>
        <p className="text-[11px] text-slate-500 mt-1">Weighted abs % error</p>
      </div>

      {/* 5. Over/Under Frequency */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
        <div className="flex items-center justify-between text-slate-500 mb-1.5">
          <span className="text-xs font-semibold uppercase tracking-wider">Error Direction</span>
          <Zap className="w-4 h-4 text-amber-500" />
        </div>
        <div className="text-xs font-semibold text-slate-700 space-y-1 mt-1">
          <div className="flex justify-between items-center">
            <span className="text-amber-700">Over ({metrics.overforecastCount}):</span>
            <span className="font-bold">{formatPercent(metrics.overforecastFrequencyPct, 1)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-cyan-700">Under ({metrics.underforecastCount}):</span>
            <span className="font-bold">{formatPercent(metrics.underforecastFrequencyPct, 1)}</span>
          </div>
        </div>
      </div>

      {/* 6. Data Coverage */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
        <div className="flex items-center justify-between text-slate-500 mb-1.5">
          <span className="text-xs font-semibold uppercase tracking-wider">Data Coverage</span>
          {metrics.dataCoveragePct >= 99.0 ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          )}
        </div>
        <div className="flex items-baseline space-x-1.5">
          <span className="text-2xl font-bold tracking-tight text-slate-900">
            {formatPercent(metrics.dataCoveragePct, 0)}
          </span>
        </div>
        <p className="text-[11px] text-slate-500 mt-1">
          {formatNumber(metrics.matchedIntervals)} / {formatNumber(metrics.totalIntervals)} valid hours
        </p>
      </div>
    </div>
  );
};
