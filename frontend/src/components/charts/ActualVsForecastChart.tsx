import React, { useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  Brush,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { TimeseriesPoint } from '../../types';
import { Eye, EyeOff, ZoomIn } from 'lucide-react';

interface ActualVsForecastChartProps {
  data: TimeseriesPoint[];
  loading: boolean;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const rawPoint: TimeseriesPoint = payload[0].payload;
    const dt = parseISO(rawPoint.timestamp);
    const pubDt = rawPoint.forecastPublishTime ? parseISO(rawPoint.forecastPublishTime) : null;
    const isOver = (rawPoint.errorMW ?? 0) > 0;

    return (
      <div className="bg-navy-900 text-white p-3.5 rounded-lg shadow-xl border border-slate-700 text-xs space-y-1.5 min-w-[240px]">
        <div className="font-semibold text-slate-200 border-b border-slate-700 pb-1 flex justify-between items-center">
          <span>{format(dt, 'dd MMM yyyy, HH:mm')} UTC</span>
          <span className="text-[10px] text-slate-400 font-mono">1h Interval</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-emerald-400 flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
            <span>Actual (FUELHH):</span>
          </span>
          <span className="font-mono font-semibold">
            {rawPoint.actualMW !== null ? `${rawPoint.actualMW.toLocaleString()} MW` : 'Missing'}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-cyan-400 flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block" />
            <span>Selected Forecast:</span>
          </span>
          <span className="font-mono font-semibold">
            {rawPoint.forecastMW !== null ? `${rawPoint.forecastMW.toLocaleString()} MW` : 'Missing'}
          </span>
        </div>
        {rawPoint.errorMW !== null && (
          <div className="flex justify-between items-center pt-1 border-t border-slate-800">
            <span className="text-slate-300">Signed Error (F − A):</span>
            <span className={`font-mono font-bold ${isOver ? 'text-amber-400' : 'text-cyan-300'}`}>
              {rawPoint.errorMW > 0 ? `+${rawPoint.errorMW.toLocaleString()}` : rawPoint.errorMW.toLocaleString()} MW
            </span>
          </div>
        )}
        {pubDt && (
          <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-800/80">
            Published: {format(pubDt, 'dd MMM HH:mm')} UTC
          </div>
        )}
      </div>
    );
  }
  return null;
};

export const ActualVsForecastChart: React.FC<ActualVsForecastChartProps> = ({ data, loading }) => {
  const [showActual, setShowActual] = useState(true);
  const [showForecast, setShowForecast] = useState(true);

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs animate-pulse">
        <div className="h-5 bg-slate-200 rounded w-48 mb-4" />
        <div className="h-72 bg-slate-100 rounded w-full" />
      </div>
    );
  }

  // Format tick labels
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
        <div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
            <span>Actual vs. Day-Ahead Forecast Generation (MW)</span>
            <span className="text-[11px] font-normal px-2 py-0.5 rounded bg-slate-100 text-slate-600">
              National Wind GB
            </span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Elexon FUELHH actual generation vs. latest eligible WINDFOR published prior to configured decision cutoff.
          </p>
        </div>

        {/* Visibility Toggles */}
        <div className="flex items-center space-x-2 text-xs">
          <button
            onClick={() => setShowActual(!showActual)}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded border transition-colors ${
              showActual
                ? 'bg-emerald-50 border-emerald-300 text-emerald-800 font-medium'
                : 'bg-slate-50 border-slate-200 text-slate-400 line-through'
            }`}
          >
            {showActual ? <Eye className="w-3 h-3 text-emerald-600" /> : <EyeOff className="w-3 h-3" />}
            <span>Actual (FUELHH)</span>
          </button>
          <button
            onClick={() => setShowForecast(!showForecast)}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded border transition-colors ${
              showForecast
                ? 'bg-cyan-50 border-cyan-300 text-cyan-800 font-medium'
                : 'bg-slate-50 border-slate-200 text-slate-400 line-through'
            }`}
          >
            {showForecast ? <Eye className="w-3 h-3 text-cyan-600" /> : <EyeOff className="w-3 h-3" />}
            <span>Forecast (WINDFOR)</span>
          </button>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-80 w-full pt-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
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
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: '12px' }} />

            {showActual && (
              <Line
                name="Actual Generation (MW)"
                type="monotone"
                dataKey="actualMW"
                stroke="#10B981"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 5, strokeWidth: 1, stroke: '#FFFFFF' }}
              />
            )}
            {showForecast && (
              <Line
                name="Selected Forecast (MW)"
                type="monotone"
                dataKey="forecastMW"
                stroke="#0284C7"
                strokeWidth={2}
                strokeDasharray="4 2"
                dot={false}
                activeDot={{ r: 5, strokeWidth: 1, stroke: '#FFFFFF' }}
              />
            )}
            <Brush
              dataKey="timestamp"
              height={26}
              stroke="#0284C7"
              fill="#F8FAFC"
              tickFormatter={formatXAxis}
              startIndex={0}
              endIndex={Math.min(data.length - 1, 168)} // Default to first week for readability
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between pt-2 text-[11px] text-slate-400">
        <span className="flex items-center space-x-1">
          <ZoomIn className="w-3.5 h-3.5 text-slate-400" />
          <span>Drag the handles on the bottom slider to zoom into specific days.</span>
        </span>
        <span>Units: Megawatts (MW)</span>
      </div>
    </div>
  );
};
