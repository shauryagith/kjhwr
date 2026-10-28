import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Cell,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { TimeseriesPoint } from '../../types';

interface ErrorChartProps {
  data: TimeseriesPoint[];
  loading: boolean;
}

const CustomErrorTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const p: TimeseriesPoint = payload[0].payload;
    const dt = parseISO(p.timestamp);
    const err = p.errorMW ?? 0;
    const isOver = err > 0;

    return (
      <div className="bg-navy-900 text-white p-3 rounded-lg shadow-xl border border-slate-700 text-xs space-y-1 min-w-[200px]">
        <div className="font-semibold text-slate-200 border-b border-slate-700 pb-1">
          {format(dt, 'dd MMM yyyy, HH:mm')} UTC
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Error (F − A):</span>
          <span className={`font-mono font-bold ${isOver ? 'text-amber-400' : 'text-cyan-300'}`}>
            {err > 0 ? `+${err.toLocaleString()}` : err.toLocaleString()} MW
          </span>
        </div>
        <div className="flex justify-between items-center text-[11px] text-slate-400">
          <span>Direction:</span>
          <span className="font-semibold text-white">
            {isOver ? 'Overforecast (Short volume risk)' : 'Underforecast (Long volume risk)'}
          </span>
        </div>
      </div>
    );
  }
  return null;
};

export const ErrorChart: React.FC<ErrorChartProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs animate-pulse">
        <div className="h-5 bg-slate-200 rounded w-48 mb-4" />
        <div className="h-56 bg-slate-100 rounded w-full" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-xs mb-6 text-center text-slate-500 text-sm">
        <p className="font-semibold text-slate-700">No error data available</p>
      </div>
    );
  }

  const formatXAxis = (tickItem: string) => {
    try {
      const d = parseISO(tickItem);
      return format(d, 'dd MMM');
    } catch {
      return tickItem;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-2">
        <div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
            <span>Signed Forecast Error (Forecast − Actual, MW)</span>
            <span className="text-[11px] font-normal px-2 py-0.5 rounded bg-slate-100 text-slate-600">
              Zero Baseline
            </span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Amber bars above zero = Overforecasting (system shortfall). Cyan bars below zero = Underforecasting (excess wind).
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-amber-500 inline-block" />
            <span className="text-slate-600">Overforecast (+MW)</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-cyan-600 inline-block" />
            <span className="text-slate-600">Underforecast (−MW)</span>
          </span>
        </div>
      </div>

      <div className="h-64 w-full pt-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatXAxis}
              tick={{ fontSize: 11, fill: '#64748B' }}
              tickLine={false}
              axisLine={{ stroke: '#CBD5E1' }}
              minTickGap={40}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#64748B' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
            />
            <Tooltip content={<CustomErrorTooltip />} />
            <ReferenceLine y={0} stroke="#334155" strokeWidth={1.5} />
            <Bar dataKey="errorMW" name="Error (MW)" maxBarSize={8}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={(entry.errorMW ?? 0) >= 0 ? '#F59E0B' : '#0891B2'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
