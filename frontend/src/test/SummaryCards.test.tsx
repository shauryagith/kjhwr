import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

import { SummaryCards } from '../components/analytics/SummaryCards';
import { SummaryMetrics } from '../types';

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

describe('SummaryCards Component', () => {
  it('renders loading skeleton when loading is true', () => {
    const { container } = render(<SummaryCards metrics={null} loading={true} />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders all 6 key performance indicators correctly', () => {
    render(<SummaryCards metrics={mockMetrics} loading={false} />);
    
    // MAE
    expect(screen.getByText('MAE (Mean Error)')).toBeInTheDocument();
    expect(screen.getByText('2,122.81')).toBeInTheDocument();

    // RMSE
    expect(screen.getByText('RMSE (Penalty)')).toBeInTheDocument();
    expect(screen.getByText('2,616.69')).toBeInTheDocument();

    // Bias
    expect(screen.getByText('Mean Bias')).toBeInTheDocument();
    expect(screen.getByText('+1,840.3')).toBeInTheDocument();
    expect(screen.getByText('Overforecast')).toBeInTheDocument();

    // WAPE
    expect(screen.getByText('WAPE')).toBeInTheDocument();
    expect(screen.getByText('18.25%')).toBeInTheDocument();

    // Over/Under direction
    expect(screen.getByText('Error Direction')).toBeInTheDocument();
    expect(screen.getByText('69.9%')).toBeInTheDocument();
    expect(screen.getByText('28.2%')).toBeInTheDocument();

    // Data Coverage
    expect(screen.getByText('Data Coverage')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText(/744 \/ 744 valid hours/i)).toBeInTheDocument();
  });
});
