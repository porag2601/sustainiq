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

// Values must match the Sector enum in backend/app/models.py.
export const SECTORS = [
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'logistics_transport', label: 'Logistics & Transport' },
  { value: 'food_retail', label: 'Food & Retail' },
  { value: 'construction', label: 'Construction' },
  { value: 'other', label: 'Other' },
]

export function sectorLabel(value) {
  return SECTORS.find((sector) => sector.value === value)?.label ?? value
}

// "2026-09-26T18:25:55Z" -> "26/09/2026, 20:25" in the viewer's local time.
export function formatDate(isoString) {
  return new Date(isoString).toLocaleString('en-GB', { dateStyle: 'short', timeStyle: 'short' })
}

// ESRS standards used in this tool (checklist, AI recommendations, CSRD gaps).
export const ESRS_LABELS = {
  'ESRS 2': 'ESRS 2 General disclosures',
  E1: 'ESRS E1 Climate',
  E2: 'ESRS E2 Pollution',
  E3: 'ESRS E3 Water',
  E5: 'ESRS E5 Resources',
}

export function esrsLabel(standard) {
  return ESRS_LABELS[standard] ?? standard
}

export function metricLabel(key) {
  return METRIC_LABELS[key] ?? key
}

// 850000 -> "850,000"; 18888.888 -> "18,888.9"
export function formatNumber(value) {
  return value.toLocaleString('en-US', { maximumFractionDigits: 1 })
}
