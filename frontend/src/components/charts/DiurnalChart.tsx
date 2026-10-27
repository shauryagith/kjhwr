import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ReferenceLine,
} from 'recharts';
import { DiurnalAccuracyItem } from '../../types';

interface DiurnalChartProps {
  data: DiurnalAccuracyItem[];
  loading: boolean;
}

const CustomDiurnalTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const item: DiurnalAccuracyItem = payload[0].payload;
    const hourLabel = `${item.hourOfDay.toString().padStart(2, '0')}:00 UTC`;
    return (
      <div className="bg-navy-900 text-white p-3 rounded-lg shadow-xl border border-slate-700 text-xs space-y-1.5 min-w-[200px]">
        <div className="font-semibold text-slate-200 border-b border-slate-700 pb-1">
          Time of Day: {hourLabel}
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Mean MAE:</span>
          <span className="font-mono font-semibold text-cyan-300">{item.maeMW.toLocaleString()} MW</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Mean Bias:</span>
          <span className={`font-mono font-semibold ${item.biasMW > 0 ? 'text-amber-400' : 'text-cyan-400'}`}>
            {item.biasMW > 0 ? `+${item.biasMW.toLocaleString()}` : item.biasMW.toLocaleString()} MW
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Mean Actual:</span>
          <span className="font-mono font-semibold text-emerald-400">{item.meanActualMW.toLocaleString()} MW</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Mean Forecast:</span>
          <span className="font-mono font-semibold text-blue-300">{item.meanForecastMW.toLocaleString()} MW</span>
        </div>
        <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-800">
          Sampled Intervals: {item.count} days in month
        </div>
      </div>
    );
  }
  return null;
};

export const DiurnalChart: React.FC<DiurnalChartProps> = ({ data, loading }) => {
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
          Diurnal Forecasting Profile (Hour of Day 00–23 UTC)
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Intraday error patterns: checks whether models systematically overforecast during morning or evening ramps.
        </p>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
            <XAxis
              dataKey="hourOfDay"
              tickFormatter={(v) => `${v.toString().padStart(2, '0')}:00`}
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
            <Tooltip content={<CustomDiurnalTooltip />} />
            <Legend verticalAlign="top" height={32} iconType="circle" wrapperStyle={{ fontSize: '11px' }} />
            <ReferenceLine y={0} stroke="#94A3B8" />
            <Bar dataKey="maeMW" name="Hour MAE (MW)" fill="#60A5FA" radius={[3, 3, 0, 0]} maxBarSize={16} />
            <Line
              type="monotone"
              dataKey="biasMW"
              name="Hour Bias (MW)"
              stroke="#EA580C"
              strokeWidth={2}
              dot={{ r: 2, fill: '#EA580C' }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
