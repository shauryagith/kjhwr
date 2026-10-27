import React, { useState, useEffect } from 'react';
import {
  Filter,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Download,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { ForecastTableResponse } from '../../types';
import { api, QueryFilters } from '../../services/api';

interface ForecastTableProps {
  filters: QueryFilters;
  onExportCsv: () => void;
}

export const ForecastTable: React.FC<ForecastTableProps> = ({ filters, onExportCsv }) => {
  const [data, setData] = useState<ForecastTableResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('deliveryInterval');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    let cancelled = false;
    const fetchTable = async () => {
      setLoading(true);
      try {
        const res = await api.getForecastTable(
          filters,
          page,
          pageSize,
          statusFilter,
          sortBy,
          sortDir
        );
        if (!cancelled) {
          setData(res);
        }
      } catch (err) {
        console.error('Failed to load forecast table:', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchTable();
    return () => {
      cancelled = true;
    };
  }, [filters, page, pageSize, statusFilter, sortBy, sortDir]);

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDir('asc');
    }
    setPage(1);
  };

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  const renderSortIcon = (column: string) => {
    if (sortBy !== column) {
      return <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />;
    }
    return sortDir === 'asc' ? (
      <ArrowUp className="w-3.5 h-3.5 text-cyan-600" />
    ) : (
      <ArrowDown className="w-3.5 h-3.5 text-cyan-600" />
    );
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OVERFORECAST':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            Overforecast
          </span>
        );
      case 'UNDERFORECAST':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-cyan-50 text-cyan-700 border border-cyan-200">
            Underforecast
          </span>
        );
      case 'EXACT_MATCH':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            Exact Match
          </span>
        );
      case 'ZERO_ACTUAL':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-300">
            Zero Actual
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs mb-8 overflow-hidden">
      {/* Table Controls Header */}
      <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/50">
        <div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-2">
            <span>Forecast Explorer (Interval Audit Table)</span>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-200 text-slate-700">
              {data?.total ?? 0} Intervals
            </span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit point-in-time forecast selection, exact publication times, lead times, and signed generation errors.
          </p>
        </div>

        {/* Filter and Page Size Controls */}
        <div className="flex items-center space-x-2.5">
          {/* Status Filter */}
          <div className="flex items-center space-x-1.5 bg-white border border-slate-300 rounded-md px-2.5 py-1 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="bg-transparent font-medium text-slate-700 border-none focus:outline-none focus:ring-0 cursor-pointer"
            >
              <option value="ALL">All Statuses</option>
              <option value="OVERFORECAST">Overforecast Only</option>
              <option value="UNDERFORECAST">Underforecast Only</option>
              <option value="EXACT_MATCH">Exact Matches</option>
            </select>
          </div>

          {/* Rows Per Page */}
          <div className="flex items-center space-x-1 bg-white border border-slate-300 rounded-md px-2 py-1 text-xs">
            <span className="text-slate-400">Rows:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="bg-transparent font-medium text-slate-700 border-none focus:outline-none focus:ring-0 cursor-pointer"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          {/* Export CSV button */}
          <button
            onClick={onExportCsv}
            className="flex items-center space-x-1.5 px-3 py-1 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium rounded-md shadow-xs transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Table Element */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
          <thead className="bg-slate-50/80 text-slate-600 font-semibold tracking-wider uppercase">
            <tr>
              <th
                onClick={() => handleSort('deliveryInterval')}
                className="py-3 px-4 cursor-pointer hover:bg-slate-100/80 group transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Delivery Interval</span>
                  {renderSortIcon('deliveryInterval')}
                </div>
              </th>
              <th
                onClick={() => handleSort('actualMW')}
                className="py-3 px-4 cursor-pointer hover:bg-slate-100/80 group transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Actual (MW)</span>
                  {renderSortIcon('actualMW')}
                </div>
              </th>
              <th
                onClick={() => handleSort('forecastMW')}
                className="py-3 px-4 cursor-pointer hover:bg-slate-100/80 group transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Forecast (MW)</span>
                  {renderSortIcon('forecastMW')}
                </div>
              </th>
              <th className="py-3 px-4">
                <span>Forecast Publish Time</span>
              </th>
              <th className="py-3 px-4">
                <span>Lead Time</span>
              </th>
              <th
                onClick={() => handleSort('errorMW')}
                className="py-3 px-4 cursor-pointer hover:bg-slate-100/80 group transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Signed Error (F − A)</span>
                  {renderSortIcon('errorMW')}
                </div>
              </th>
              <th
                onClick={() => handleSort('absErrorMW')}
                className="py-3 px-4 cursor-pointer hover:bg-slate-100/80 group transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Abs Error</span>
                  {renderSortIcon('absErrorMW')}
                </div>
              </th>
              <th className="py-3 px-4">
                <span>Error %</span>
              </th>
              <th className="py-3 px-4">
                <span>Status</span>
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100 bg-white">
            {loading ? (
              <tr>
                <td colSpan={9} className="py-12 text-center text-slate-400 animate-pulse">
                  Loading interval observations...
                </td>
              </tr>
            ) : !data || data.items.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-12 text-center text-slate-500">
                  No delivery intervals found matching the current criteria.
                </td>
              </tr>
            ) : (
              data.items.map((row, idx) => {
                const deliveryDate = parseISO(row.deliveryInterval);
                const pubDate = row.forecastPublishTime ? parseISO(row.forecastPublishTime) : null;
                const isOver = (row.errorMW ?? 0) > 0;

                return (
                  <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                    {/* Delivery Interval */}
                    <td className="py-2.5 px-4 font-mono font-medium text-slate-900 whitespace-nowrap">
                      {format(deliveryDate, 'yyyy-MM-dd HH:mm')} UTC
                    </td>

                    {/* Actual Generation */}
                    <td className="py-2.5 px-4 font-mono font-semibold text-emerald-700 whitespace-nowrap">
                      {row.actualMW !== null ? `${row.actualMW.toLocaleString()} MW` : '—'}
                    </td>

                    {/* Forecast Generation */}
                    <td className="py-2.5 px-4 font-mono font-semibold text-blue-700 whitespace-nowrap">
                      {row.forecastMW !== null ? `${row.forecastMW.toLocaleString()} MW` : '—'}
                    </td>

                    {/* Forecast Publish Time */}
                    <td className="py-2.5 px-4 font-mono text-slate-600 whitespace-nowrap">
                      {pubDate ? format(pubDate, 'yyyy-MM-dd HH:mm') : '—'}
                    </td>

                    {/* Lead Time */}
                    <td className="py-2.5 px-4 text-slate-600 whitespace-nowrap">
                      {row.leadTimeHours !== null ? `${row.leadTimeHours} hrs` : '—'}
                    </td>

                    {/* Signed Error */}
                    <td className="py-2.5 px-4 font-mono font-bold whitespace-nowrap">
                      {row.errorMW !== null ? (
                        <span className={isOver ? 'text-amber-700' : 'text-cyan-700'}>
                          {row.errorMW > 0 ? `+${row.errorMW.toLocaleString()}` : row.errorMW.toLocaleString()} MW
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>

                    {/* Abs Error */}
                    <td className="py-2.5 px-4 font-mono text-slate-700 whitespace-nowrap">
                      {row.absErrorMW !== null ? `${row.absErrorMW.toLocaleString()} MW` : '—'}
                    </td>

                    {/* Pct Error */}
                    <td className="py-2.5 px-4 font-mono text-slate-600 whitespace-nowrap">
                      {row.pctError !== null ? `${row.pctError}%` : '—'}
                    </td>

                    {/* Status Badge */}
                    <td className="py-2.5 px-4 whitespace-nowrap">
                      {getStatusBadge(row.status)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-3.5 border-t border-slate-100 flex items-center justify-between bg-slate-50/50 text-xs">
        <span className="text-slate-500">
          Showing page <strong className="text-slate-800">{page}</strong> of{' '}
          <strong className="text-slate-800">{totalPages || 1}</strong> (
          {data ? data.total.toLocaleString() : 0} total intervals)
        </span>

        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1 || loading}
            className="p-1.5 rounded border border-slate-300 bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Previous Page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="px-2 font-semibold text-slate-700">
            {page} / {totalPages || 1}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages || loading}
            className="p-1.5 rounded border border-slate-300 bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Next Page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
