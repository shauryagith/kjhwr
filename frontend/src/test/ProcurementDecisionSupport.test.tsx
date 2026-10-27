import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

import { ProcurementDecisionSupport } from '../components/procurement/ProcurementDecisionSupport';
import { ProcurementImpact, SummaryMetrics } from '../types';

const mockImpact: ProcurementImpact = {
  totalOverforecastMWh: 1369190.0,
  totalUnderforecastMWh: 67140.0,
  netImbalanceMWh: 1302050.0,
  overforecastRiskSummary: 'Overforecasting creates risk of a short physical position.',
  underforecastRiskSummary: 'Underforecasting creates a prospective long position.',
  guidanceNotes: [
    'Procurement Warning: Wind generation alone does NOT determine net utility procurement.',
  ],
};

const mockMetrics: SummaryMetrics = {
  totalIntervals: 744,
  matchedIntervals: 744,
  missingActualIntervals: 0,
  missingForecastIntervals: 0,
  dataCoveragePct: 100.0,
  maeMW: 2122.81,
  rmseMW: 2616.69,
  biasMW: 1840.30,
  wapePct: 18.25,
  maxOverforecastMW: 5800.0,
  maxUnderforecastMW: 3200.0,
  overforecastCount: 520,
  underforecastCount: 210,
  exactMatchCount: 14,
  overforecastFrequencyPct: 69.89,
  underforecastFrequencyPct: 28.23,
  meanActualMW: 11630.0,
  meanForecastMW: 13470.3,
  totalActualGWh: 8652.7,
  totalForecastGWh: 10021.9,
};

describe('ProcurementDecisionSupport Component', () => {
  it('renders volume risks, short and long exposures, and regulatory notice', () => {
    render(
      <ProcurementDecisionSupport
        impact={mockImpact}
        metrics={mockMetrics}
        loading={false}
      />
    );

    expect(screen.getByText(/Day-Ahead Procurement Decision Support/i)).toBeInTheDocument();
    expect(screen.getByText(/Overforecast Risk \(Short Position\)/i)).toBeInTheDocument();
    expect(screen.getByText('1,369,190')).toBeInTheDocument();
    expect(screen.getByText(/Underforecast Risk \(Long Position\)/i)).toBeInTheDocument();
    expect(screen.getByText('67,140')).toBeInTheDocument();
    expect(screen.getByText(/Analytical Scope & Procurement Boundary Notice/i)).toBeInTheDocument();
  });
});
