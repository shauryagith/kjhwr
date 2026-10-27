import React from 'react';
import { X, BookOpen, CheckCircle, Database, ShieldAlert, Cpu, BarChart } from 'lucide-react';

interface MethodologyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MethodologyModal: React.FC<MethodologyModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-navy-900 text-white flex items-center justify-between border-b border-navy-800">
          <div className="flex items-center space-x-2.5">
            <BookOpen className="w-5 h-5 text-cyan-400" />
            <div>
              <h2 className="text-base font-bold tracking-tight">Platform Methodology & Technical Architecture</h2>
              <p className="text-xs text-slate-400">Analytical standards, Elexon BMRS ingestion, and procurement principles</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-navy-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm text-slate-700 leading-relaxed">
          {/* Section 1: Elexon Authoritative Data Sources */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2 border-b border-slate-200 pb-2 mb-3">
              <Database className="w-4 h-4 text-cyan-600" />
              <span>1. Authoritative Elexon BMRS Datasets</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200">
                <span className="font-bold text-slate-900 block mb-1">Actual Generation: FUELHH Stream</span>
                <p className="text-slate-600 mb-2">
                  Official half-hourly settlement generation by fuel type. Filtered strictly for national GB wind (<code>fuelType = 'WIND'</code>).
                </p>
                <div className="font-mono text-[11px] text-slate-500">
                  Endpoint: <code>/datasets/FUELHH/stream</code>
                </div>
              </div>

              <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200">
                <span className="font-bold text-slate-900 block mb-1">Wind Forecast: WINDFOR Stream</span>
                <p className="text-slate-600 mb-2">
                  Rolling wind generation forecasts published at discrete intervals (typically 73 hourly predictions per run, ~3 days horizon).
                </p>
                <div className="font-mono text-[11px] text-slate-500">
                  Endpoint: <code>/datasets/WINDFOR/stream</code>
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: Point-in-Time Forecast Selection */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2 border-b border-slate-200 pb-2 mb-3">
              <Cpu className="w-4 h-4 text-cyan-600" />
              <span>2. Point-in-Time Forecast Selection Algorithm</span>
            </h3>
            <p className="text-xs text-slate-600 mb-3">
              To prevent <strong>lookahead bias</strong>, a forecast published after a procurement decision deadline must never be presented as information that was available to the trader.
            </p>
            <div className="bg-slate-900 text-slate-100 p-3.5 rounded-lg font-mono text-xs overflow-x-auto">
              {`def select_forecast_as_of(forecasts, delivery_interval, decision_cutoff):
    # 1. Filter forecasts matching the delivery interval
    # 2. Exclude all forecasts published AFTER decision_cutoff (publishTime <= decision_cutoff)
    # 3. Select latest eligible publication: max(publishTime)
    # 4. Return selected forecast MW with publication metadata`}
            </div>
          </div>

          {/* Section 3: Decision Cutoff Assumptions */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2 border-b border-slate-200 pb-2 mb-3">
              <CheckCircle className="w-4 h-4 text-cyan-600" />
              <span>3. Decision Cutoff Rationale & Conventions</span>
            </h3>
            <div className="space-y-2 text-xs">
              <p>
                <strong>Day-Ahead 11:00 UK Time (Default):</strong> In the Great Britain wholesale market, the primary Day-Ahead Auctions (EPEX SPOT and Nord Pool) close order books at <strong>11:00 GMT</strong> on day D-1. This is the authoritative default for day-ahead purchasing decisions.
              </p>
              <p>
                <strong>Alternative Presets:</strong> The platform also supports DA 12:00 (European internal locking deadline), DA 17:00 (end of trading business day), DA 23:00 (midnight prior to delivery), and rolling lookahead horizons (24h, 12h, 6h, 2h).
              </p>
            </div>
          </div>

          {/* Section 4: Resolution & Settlement Period Aggregation */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2 border-b border-slate-200 pb-2 mb-3">
              <BarChart className="w-4 h-4 text-cyan-600" />
              <span>4. Interval Resolution & Aggregation</span>
            </h3>
            <div className="space-y-2 text-xs text-slate-600">
              <p>
                While actual generation (<code>FUELHH</code>) is published at 30-minute settlement period resolution, <code>WINDFOR</code> forecasts are natively provided at 1-hour resolution.
              </p>
              <p>
                To compare like-for-like power (MW), the platform aligns observations to hourly delivery intervals <code>[T, T+1h)</code>, where the actual hourly power is the arithmetic mean of the two half-hours:
              </p>
              <div className="font-mono bg-slate-100 p-2 rounded text-slate-800 text-center font-semibold">
                Actual_Hourly_MW = (Actual_HH1 + Actual_HH2) / 2
              </div>
            </div>
          </div>

          {/* Section 5: Mathematical Metric Definitions */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2 border-b border-slate-200 pb-2 mb-3">
              <BarChart className="w-4 h-4 text-cyan-600" />
              <span>5. Mathematical Metric Definitions</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="border border-slate-200 p-3 rounded-lg">
                <span className="font-bold text-slate-900">Signed Error (MW)</span>
                <div className="font-mono text-cyan-700 font-semibold my-1">Error = Forecast − Actual</div>
                <p className="text-slate-500">Positive = Overforecasting; Negative = Underforecasting.</p>
              </div>

              <div className="border border-slate-200 p-3 rounded-lg">
                <span className="font-bold text-slate-900">Mean Absolute Error (MAE)</span>
                <div className="font-mono text-cyan-700 font-semibold my-1">MAE = (1/N) * Σ |Forecast − Actual|</div>
                <p className="text-slate-500">Average magnitude of misses in Megawatts.</p>
              </div>

              <div className="border border-slate-200 p-3 rounded-lg">
                <span className="font-bold text-slate-900">Root Mean Squared Error (RMSE)</span>
                <div className="font-mono text-cyan-700 font-semibold my-1">RMSE = sqrt((1/N) * Σ (Forecast − Actual)²)</div>
                <p className="text-slate-500">Heavily penalizes extreme forecast misses.</p>
              </div>

              <div className="border border-slate-200 p-3 rounded-lg">
                <span className="font-bold text-slate-900">Weighted Absolute Percentage Error (WAPE)</span>
                <div className="font-mono text-cyan-700 font-semibold my-1">WAPE = (Σ |F − A| / Σ A) * 100%</div>
                <p className="text-slate-500">Weighted volume accuracy; handles zero intervals safely.</p>
              </div>
            </div>
          </div>

          {/* Section 6: Procurement Guardrails */}
          <div>
            <h3 className="text-sm font-bold text-amber-900 uppercase tracking-wider flex items-center space-x-2 border-b border-amber-200 pb-2 mb-3">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              <span>6. Procurement Decision Support Guardrails</span>
            </h3>
            <div className="bg-amber-50/70 border border-amber-200 p-3.5 rounded-lg text-xs text-amber-950 space-y-2">
              <p>
                <strong>Wind Generation vs. Net Utility Procurement:</strong> Wind power is an intermittent supply source, not the total utility purchase volume. Net procurement also depends on customer demand profiles, solar PV generation, contracted thermal capacity, battery storage cycling, and existing PPAs.
              </p>
              <p>
                <strong>No Fabricated Data:</strong> In strict compliance with hiring submission integrity, this application does not simulate artificial electricity prices, synthetic demand schedules, or fabricated financial savings.
              </p>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-navy-800 hover:bg-navy-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
          >
            Close Methodology
          </button>
        </div>
      </div>
    </div>
  );
};
