// Shared helpers for displaying metrics. Kept outside component files, because
// Vite's fast refresh works best when component files export only components.

// Readable names for the metric keys sent by the backend (scoring.py).
export const METRIC_LABELS = {
  energy_kwh_per_fte: 'Energy per employee',
  scope12_t_per_fte: 'Scope 1+2 emissions per employee',
  waste_t_per_fte: 'Waste per employee',
  water_m3_per_fte: 'Water per employee',
  renewable_share_pct: 'Renewable energy share',
  recycling_rate_pct: 'Recycling rate',
}

export function metricLabel(key) {
  return METRIC_LABELS[key] ?? key
}

// 850000 -> "850,000"; 18888.888 -> "18,888.9"
export function formatNumber(value) {
  return value.toLocaleString('en-US', { maximumFractionDigits: 1 })
}
