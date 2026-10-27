import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import { FilterBar } from '../components/controls/FilterBar';
import { CutoffPresetOption } from '../types';

const mockPresets: CutoffPresetOption[] = [
  { id: 'DA_1100', label: 'Day-Ahead 11:00 UK Time', description: 'Auction Default' },
  { id: 'DA_1200', label: 'Day-Ahead 12:00 UK Time', description: 'Noon Default' },
];

describe('FilterBar Component', () => {
  it('renders date inputs and calls onFilterChange when changed', () => {
    const onFilterChange = vi.fn();
    const onRefresh = vi.fn();
    const onExportCsv = vi.fn();

    render(
      <FilterBar
        filters={{ startDate: '2026-01-01', endDate: '2026-01-31', cutoffPreset: 'DA_1100' }}
        onFilterChange={onFilterChange}
        onRefresh={onRefresh}
        isRefreshing={false}
        onExportCsv={onExportCsv}
        cutoffPresets={mockPresets}
      />
    );

    // Click quick preset
    const week1Btn = screen.getByText('Week 1');
    fireEvent.click(week1Btn);
    expect(onFilterChange).toHaveBeenCalledWith({ startDate: '2026-01-01', endDate: '2026-01-07' });

    // Export CSV click
    const exportBtn = screen.getByText(/Export/i);
    fireEvent.click(exportBtn);
    expect(onExportCsv).toHaveBeenCalled();

    // Sync button click
    const syncBtn = screen.getByText(/Sync Elexon/i);
    fireEvent.click(syncBtn);
    expect(onRefresh).toHaveBeenCalled();
  });
});
