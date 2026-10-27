import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts';
import { ErrorDistributionBucket } from '../../types';

interface ErrorDistributionChartProps {
  data: ErrorDistributionBucket[];
  loading: boolean;
}

const CustomDistributionTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const bucket: ErrorDistributionBucket = payload[0].payload;
    return (
      <div className="bg-navy-900 text-white p-3 rounded-lg shadow-xl border border-slate-700 text-xs space-y-1 min-w-[180px]">
        <div className="font-semibold text-slate-200 border-b border-slate-700 pb-1">
          {bucket.label}
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Intervals:</span>
          <span className="font-mono font-bold text-white">{bucket.count}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Frequency:</span>
          <span className="font-mono font-bold text-cyan-300">{bucket.frequencyPct}%</span>
        </div>
      </div>
    );
  }
  return null;
};

export const ErrorDistributionChart: React.FC<ErrorDistributionChartProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs animate-pulse">
        <div className="h-5 bg-slate-200 rounded w-40 mb-3" />
        <div className="h-60 bg-slate-100 rounded" />
      </div>
    );
  }

  const getBarColor = (label: string) => {
    if (label.includes('Accurate')) return '#10B981'; // green
    if (label.includes('Over')) return '#F59E0B'; // amber
    return '#0891B2'; // cyan
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
      <div className="pb-3 border-b border-slate-100 mb-3">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight">
          Forecast Error Distribution (MW)
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Histogram of signed errors around zero baseline (Green = accurate band).
        </p>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 9, fill: '#64748B' }}
              tickLine={false}
              interval={0}
              angle={-30}
              textAnchor="end"
              axisLine={{ stroke: '#CBD5E1' }}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#64748B' }}
              tickLine={false}
              axisLine={false}
              label={{ value: 'Intervals', angle: -90, position: 'insideLeft', fontSize: 10, fill: '#94A3B8' }}
            />
            <Tooltip content={<CustomDistributionTooltip />} />
            <Bar dataKey="count" name="Frequency" radius={[4, 4, 0, 0]} maxBarSize={28}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.label)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
