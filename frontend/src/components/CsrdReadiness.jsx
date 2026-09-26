import { esrsLabel } from '../metrics'

// CSRD data readiness: how many checklist data points the company has.
// readiness comes from the backend (calculated in Python, see csrd.py);
// checklist is used only to show titles for the missing ids.
function CsrdReadiness({ readiness, checklist }) {
  const byId = Object.fromEntries((checklist ?? []).map((item) => [item.id, item]))
  const missing = readiness.missing_ids.map((id) => byId[id]).filter(Boolean)

  return (
    <section className="rounded-lg bg-white p-6 shadow">
      <h2 className="text-xl font-semibold">CSRD data readiness</h2>
      <p className="mt-1 text-sm text-slate-600">
        {readiness.available} of {readiness.total} key ESRS data points available (
        <span className="font-medium text-slate-900">{readiness.percent} %</span>).
      </p>

      <ul className="mt-4 space-y-2">
        {readiness.standards.map((s) => (
          <li key={s.standard} className="flex items-center gap-3 text-sm">
            <span className="w-48 shrink-0">{esrsLabel(s.standard)}</span>
            <div className="h-2 flex-1 rounded-full bg-slate-200">
              <div
                className="h-2 rounded-full bg-emerald-600"
                style={{ width: `${(s.available / s.total) * 100}%` }}
              />
            </div>
            <span className="w-10 text-right text-slate-600">
              {s.available}/{s.total}
            </span>
          </li>
        ))}
      </ul>

      {missing.length > 0 && (
        <>
          <h3 className="mt-6 font-semibold">Missing data points</h3>
          <ul className="mt-2 list-inside list-disc space-y-1 text-sm">
            {missing.map((item) => (
              <li key={item.id}>
                {item.title} <span className="text-slate-500">({item.reference})</span>
              </li>
            ))}
          </ul>
        </>
      )}

      <p className="mt-4 text-xs text-slate-500">
        Simplified checklist of key data points, not the full ESRS. References follow ESRS Set 1 (2023);
        the EU is simplifying the ESRS (Omnibus), so numbering and scope may change.
      </p>
    </section>
  )
}

export default CsrdReadiness
