import React from 'react';
import { Wind, Database, BookOpen, ExternalLink } from 'lucide-react';
import { HealthResponse } from '../../types';
import { API_BASE } from '../../services/api';

interface HeaderProps {
  health: HealthResponse | null;
  onOpenMethodology: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, onOpenMethodology }) => {
  const docsUrl = API_BASE.startsWith('http')
    ? `${API_BASE.replace(/\/api\/v1\/?$/, '')}/docs`
    : '/docs';
  return (
    <header className="bg-navy-900 border-b border-navy-800 text-white shadow-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & App Name */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-inner">
              <Wind className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-white">Gridbricks</span>
                <span className="text-xs uppercase tracking-wider px-2 py-0.5 rounded bg-navy-700 text-cyan-300 font-semibold border border-cyan-500/20">
                  GB Wind Intelligence
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Day-Ahead Power Procurement & Forecast Uncertainty Platform
              </p>
            </div>
          </div>

          {/* Badges and Actions */}
          <div className="flex items-center space-x-3">
            {/* Elexon Status */}
            <div className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-navy-800 border border-slate-700/60 text-xs">
              <span className={`w-2 h-2 rounded-full ${health?.elexon_live_accessible ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span className="text-slate-300 font-medium">Elexon BMRS:</span>
              <span className={health?.elexon_live_accessible ? 'text-emerald-300 font-semibold' : 'text-amber-300 font-semibold'}>
                {health?.elexon_live_accessible ? 'Live Connected' : 'Cached Store'}
              </span>
            </div>

            {/* Ingestion Data Coverage */}
            <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-navy-800 border border-slate-700/60 text-xs">
              <Database className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-slate-300">Coverage:</span>
              <span className="text-cyan-300 font-semibold">Jan 1–31, 2026 (744h)</span>
            </div>

            {/* Methodology Modal Trigger */}
            <button
              onClick={onOpenMethodology}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-navy-700 hover:bg-navy-600 border border-slate-600 text-xs font-medium text-slate-200 transition-colors shadow-sm"
              title="Methodology, Formulas, and UK Market Conventions"
            >
              <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
              <span>Methodology</span>
            </button>

            {/* OpenAPI link */}
            <a
              href={docsUrl}
              target="_blank"
              rel="noreferrer"
              className="hidden sm:flex items-center space-x-1 px-2.5 py-1.5 rounded-md hover:bg-navy-800 text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              <span>API</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};
