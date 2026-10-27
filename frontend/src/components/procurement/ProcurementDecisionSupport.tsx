import React from 'react';
import {
  Scale,
  Info,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { ProcurementImpact, SummaryMetrics } from '../../types';
import { formatNumber, formatPercent } from '../../utils/format';

interface ProcurementDecisionSupportProps {
  impact: ProcurementImpact | null;
  metrics: SummaryMetrics | null;
  loading: boolean;
}

export const ProcurementDecisionSupport: React.FC<ProcurementDecisionSupportProps> = ({
  impact,
  metrics,
  loading,
}) => {
  if (loading || !impact || !metrics) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs animate-pulse mb-6">
        <div className="h-5 bg-slate-200 rounded w-64 mb-4" />
        <div className="h-32 bg-slate-100 rounded w-full" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs mb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-navy-800 rounded-lg text-cyan-400">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Day-Ahead Procurement Decision Support & Volume Uncertainty
            </h3>
            <p className="text-xs text-slate-500">
              Evaluates physical position exposure, imbalance volume risk, and cash-out mechanisms.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[11px] font-semibold text-slate-500">National Wind GB Net Volume Miss:</span>
          <span
            className={`font-mono text-xs font-bold px-2 py-0.5 rounded border ${
              impact.netImbalanceMWh > 0
                ? 'bg-amber-50 text-amber-800 border-amber-300'
                : 'bg-cyan-50 text-cyan-800 border-cyan-300'
            }`}
          >
            {impact.netImbalanceMWh > 0
              ? `+${formatNumber(impact.netImbalanceMWh)} MWh (Short Risk)`
              : `${formatNumber(impact.netImbalanceMWh)} MWh (Long Risk)`}
          </span>
        </div>
      </div>

      {/* 2-Column Analytical Cards: Overforecast vs Underforecast */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-5">
        {/* Overforecast Risk (Short Position) */}
        <div className="bg-gradient-to-br from-amber-50/50 to-orange-50/20 rounded-xl p-4 border border-amber-200/80">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-amber-200/60">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-amber-600" />
              <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider">
                Overforecast Risk (Short Position)
              </h4>
            </div>
            <span className="text-xs font-mono font-bold text-amber-800">
              {formatPercent(metrics.overforecastFrequencyPct, 1)} Frequency
            </span>
          </div>

          <div className="flex items-baseline space-x-2 my-2">
            <span className="text-2xl font-bold font-mono text-amber-900">
              {formatNumber(impact.totalOverforecastMWh)}
            </span>
            <span className="text-xs font-semibold text-amber-700">MWh Prospective Deficit</span>
          </div>

          <p className="text-xs text-slate-700 leading-relaxed">
            {impact.overforecastRiskSummary}
          </p>

          <div className="mt-3 text-[11px] bg-amber-100/70 text-amber-900 p-2 rounded border border-amber-200">
            <strong>Procurement Action:</strong> If relying on overforecast wind, day-ahead contracts will under-procure.
            The utility is exposed to volatile intraday spikes or system buy prices in the National Grid Balancing Mechanism.
          </div>
        </div>

        {/* Underforecast Risk (Long Position) */}
        <div className="bg-gradient-to-br from-cyan-50/50 to-blue-50/20 rounded-xl p-4 border border-cyan-200/80">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-cyan-200/60">
            <div className="flex items-center space-x-2">
              <TrendingDown className="w-4 h-4 text-cyan-600" />
              <h4 className="text-xs font-bold text-cyan-900 uppercase tracking-wider">
                Underforecast Risk (Long Position)
              </h4>
            </div>
            <span className="text-xs font-mono font-bold text-cyan-800">
              {formatPercent(metrics.underforecastFrequencyPct, 1)} Frequency
            </span>
          </div>

          <div className="flex items-baseline space-x-2 my-2">
            <span className="text-2xl font-bold font-mono text-cyan-900">
              {formatNumber(impact.totalUnderforecastMWh)}
            </span>
            <span className="text-xs font-semibold text-cyan-700">MWh Prospective Surplus</span>
          </div>

          <p className="text-xs text-slate-700 leading-relaxed">
            {impact.underforecastRiskSummary}
          </p>

          <div className="mt-3 text-[11px] bg-cyan-100/70 text-cyan-900 p-2 rounded border border-cyan-200">
            <strong>Procurement Action:</strong> When wind delivers more than expected, excess generation must be spilled,
            curtailed, or sold into cash-out at potentially discounted System Sell Prices (SSP).
          </div>
        </div>
      </div>

      {/* Mandatory Analytical Guardrail / Disclaimer */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 flex items-start space-x-3">
        <Info className="w-5 h-5 text-slate-500 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-600 space-y-1">
          <div className="font-semibold text-slate-800">
            Analytical Scope & Procurement Boundary Notice:
          </div>
          <p>
            Wind generation alone does <strong>not</strong> define net electricity procurement. Net utility procurement is determined by:
            <span className="font-mono text-slate-800 font-medium"> Net Requirement = Customer Demand − Wind − Solar − Baseload Contracts ± Battery Storage</span>.
          </p>
          <p className="text-slate-500 text-[11px]">
            In strict compliance with Gridbricks challenge requirements, this platform focuses exclusively on official Elexon BMRS generation datasets
            and does not fabricate artificial wholesale market prices, consumer demand, or thermal dispatch schedules.
          </p>
        </div>
      </div>
    </div>
  );
};
