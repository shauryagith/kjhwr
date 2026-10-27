/**
 * Standard UK English number formatting helpers (en-GB locale).
 * Ensures deterministic commas (e.g. 1,369,190) regardless of developer OS locale.
 */

export const formatNumber = (
  val: number | null | undefined,
  decimals: number = 0
): string => {
  if (val === null || val === undefined) return '—';
  return val.toLocaleString('en-GB', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const formatMW = (val: number | null | undefined): string => {
  return formatNumber(val, 0);
};

export const formatMWh = (val: number | null | undefined): string => {
  return formatNumber(val, 0);
};

export const formatPercent = (
  val: number | null | undefined,
  decimals: number = 1
): string => {
  if (val === null || val === undefined) return 'N/A';
  return `${val.toLocaleString('en-GB', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}%`;
};
