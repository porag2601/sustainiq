import { formatNumber, metricLabel } from '../metrics'

// One metric: company value vs. sector benchmark, score bar and status.

// Tailwind only generates classes it finds written out in full in the code,
// so colours are listed as complete strings, never built like `bg-${color}-100`.
const STATUS_STYLES = {
  better: { label: 'Better than benchmark', badge: 'bg-emerald-100 text-emerald-800', bar: 'bg-emerald-500' },
  on_par: { label: 'On par with benchmark', badge: 'bg-amber-100 text-amber-800', bar: 'bg-amber-500' },
  worse: { label: 'Worse than benchmark', badge: 'bg-red-100 text-red-800', bar: 'bg-red-500' },
}

function MetricCard({ metric }) {
  const style = STATUS_STYLES[metric.status]
  const sign = metric.diff_pct > 0 ? '+' : ''

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold">{metricLabel(metric.key)}</h3>
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${style.badge}`}>
          {style.label}
        </span>
      </div>

      <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
        <div>
          <dt className="text-slate-500">Your company</dt>
          <dd className="font-medium">{formatNumber(metric.value)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Sector benchmark</dt>
          <dd className="font-medium">
            {formatNumber(metric.benchmark_value)}
            <span className="font-normal text-slate-500"> ({sign}{metric.diff_pct} %)</span>
          </dd>
        </div>
      </dl>
      <p className="mt-1 text-xs text-slate-500">{metric.unit}</p>

      {/* Score bar: the width is the score in % (0-100). */}
      <div className="mt-3 flex items-center gap-2">
        <div className="h-2 flex-1 rounded-full bg-slate-200">
          <div className={`h-2 rounded-full ${style.bar}`} style={{ width: `${metric.score}%` }} />
        </div>
        <span className="w-12 text-right text-sm font-medium">{metric.score}</span>
      </div>

      {/* Domain rule: an estimated benchmark must never look like an official figure. */}
      <details className="mt-3 text-xs text-slate-600">
        <summary className="cursor-pointer">
          {metric.benchmark_indicative ? (
            <span className="rounded bg-slate-100 px-1.5 py-0.5 font-medium">Indicative benchmark</span>
          ) : (
            'Official benchmark'
          )}{' '}
          · source
        </summary>
        <p className="mt-1">{metric.benchmark_source}</p>
      </details>
    </article>
  )
}

export default MetricCard
