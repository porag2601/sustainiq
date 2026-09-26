// Semicircle gauge for the overall score (0-100), drawn in plain SVG.
// No chart library needed for a single arc.

// Same +/- 5 band around 50 as ON_PAR_BAND in backend/app/scoring.py.
// SVG needs colour values; they match the Tailwind colours of the badges.
function scoreStatus(score) {
  if (score > 55)
    return { text: 'Better than the sector benchmark', arc: '#059669', badge: 'bg-emerald-100 text-emerald-800' }
  if (score < 45)
    return { text: 'Below the sector benchmark', arc: '#dc2626', badge: 'bg-red-100 text-red-800' }
  return { text: 'Around the sector benchmark', arc: '#f59e0b', badge: 'bg-amber-100 text-amber-800' }
}

// Half circle from left (score 0) over the top to right (score 100):
// centre (120, 120), radius 100.
const ARC = 'M 20 120 A 100 100 0 0 1 220 120'

function ScoreGauge({ score }) {
  const status = scoreStatus(score)

  return (
    <div className="flex flex-col items-center">
      {/* role="img" + aria-label: screen readers announce one sentence
          instead of trying to read the SVG shapes. */}
      <svg viewBox="0 0 240 135" className="w-64" role="img" aria-label={`Score ${score} out of 100. ${status.text}.`}>
        {/* pathLength="100" tells SVG to treat the arc as 100 units long,
            so a dash of `score` units covers exactly score % of it. */}
        <path d={ARC} pathLength="100" fill="none" stroke="#e2e8f0" strokeWidth="16" strokeLinecap="round" />
        <path
          d={ARC}
          pathLength="100"
          fill="none"
          stroke={status.arc}
          strokeWidth="16"
          strokeLinecap="round"
          strokeDasharray={`${score} 100`}
        />
        {/* Benchmark mark: score 50 is the top of the half circle. */}
        <line x1="120" y1="4" x2="120" y2="36" stroke="#52514e" strokeWidth="2" />
        <text x="120" y="112" textAnchor="middle" className="fill-slate-900 text-5xl font-bold">
          {score}
        </text>
        <text x="120" y="132" textAnchor="middle" className="fill-slate-400 text-sm">
          / 100
        </text>
      </svg>
      <span className={`mt-2 rounded-full px-3 py-1 text-sm font-medium ${status.badge}`}>{status.text}</span>
    </div>
  )
}

export default ScoreGauge
