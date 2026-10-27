import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ReferenceLine,
} from 'recharts';
import { DailySummaryItem } from '../../types';

interface DailySummaryChartProps {
  data: DailySummaryItem[];
  loading: boolean;
}

const CustomDailyTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const item: DailySummaryItem = payload[0].payload;
    return (
      <div className="bg-navy-900 text-white p-3 rounded-lg shadow-xl border border-slate-700 text-xs space-y-1.5 min-w-[200px]">
        <div className="font-semibold text-slate-200 border-b border-slate-700 pb-1">
          Date: {item.date}
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400">MAE (Mean Miss):</span>
          <span className="font-mono font-semibold text-cyan-300">{item.maeMW?.toLocaleString()} MW</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400">RMSE (Peak Miss):</span>
          <span className="font-mono font-semibold text-blue-300">{item.rmseMW?.toLocaleString()} MW</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Mean Bias:</span>
          <span className={`font-mono font-semibold ${(item.biasMW ?? 0) > 0 ? 'text-amber-400' : 'text-cyan-400'}`}>
            {(item.biasMW ?? 0) > 0 ? `+${item.biasMW?.toLocaleString()}` : item.biasMW?.toLocaleString()} MW
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400">WAPE %:</span>
          <span className="font-mono font-semibold text-white">{item.wapePct !== null ? `${item.wapePct}%` : 'N/A'}</span>
        </div>
        <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-800">
          Matched Intervals: {item.matchedIntervals} / {item.totalExpectedIntervals} ({item.coveragePct}%)
        </div>
      </div>
    );
  }
  return null;
};

export const DailySummaryChart: React.FC<DailySummaryChartProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs animate-pulse">
        <div className="h-5 bg-slate-200 rounded w-40 mb-3" />
        <div className="h-60 bg-slate-100 rounded" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
      <div className="pb-3 border-b border-slate-100 mb-3">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight">
          Daily Forecasting Accuracy (MAE & Mean Bias, MW)
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Day-by-day Mean Absolute Error vs signed bias across January 2026.
        </p>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
            <XAxis
              dataKey="date"
              tickFormatter={(v) => v.slice(8)} // Show day of month (e.g. "01", "15")
              tick={{ fontSize: 10, fill: '#64748B' }}
              tickLine={false}
              axisLine={{ stroke: '#CBD5E1' }}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#64748B' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomDailyTooltip />} />
            <Legend verticalAlign="top" height={32} iconType="circle" wrapperStyle={{ fontSize: '11px' }} />
            <ReferenceLine y={0} stroke="#94A3B8" />
            <Bar dataKey="maeMW" name="Daily MAE (MW)" fill="#38BDF8" radius={[3, 3, 0, 0]} maxBarSize={14} />
            <Line
              type="monotone"
              dataKey="biasMW"
              name="Daily Bias (MW)"
              stroke="#F59E0B"
              strokeWidth={2}
              dot={{ r: 2, fill: '#F59E0B' }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
