import AiAnalysis from '../components/AiAnalysis'
import BenchmarkChart from '../components/BenchmarkChart'
import MetricCard from '../components/MetricCard'

// Same +/- 5 band around 50 as ON_PAR_BAND in backend/app/scoring.py.
function overallLabel(score) {
  if (score > 55) return { text: 'Better than the sector benchmark', color: 'text-emerald-700' }
  if (score < 45) return { text: 'Below the sector benchmark', color: 'text-red-700' }
  return { text: 'Around the sector benchmark', color: 'text-amber-700' }
}

// result = { score, ai_analysis, ai_error } from POST /analyse.
function Results({ result, companyName, onReset }) {
  const { score, ai_analysis: analysis, ai_error: aiError } = result
  const label = overallLabel(score.overall_score)

  return (
    <div className="space-y-8">
      <section className="rounded-lg bg-white p-6 text-center shadow">
        <p className="text-sm text-slate-500">Sustainability score for {companyName}</p>
        <p className={`mt-2 text-6xl font-bold ${label.color}`}>
          {score.overall_score}
          <span className="text-2xl font-normal text-slate-400"> / 100</span>
        </p>
        <p className={`mt-2 font-medium ${label.color}`}>{label.text}</p>
        <p className="mt-3 text-xs text-slate-500">
          50 = exactly at the sector benchmark. Benchmarks are indicative estimates, not official statistics.
        </p>
      </section>

      <BenchmarkChart metrics={score.metrics} />

      <section>
        <h2 className="mb-4 text-xl font-semibold">Benchmark comparison</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {score.metrics.map((metric) => (
            <MetricCard key={metric.key} metric={metric} />
          ))}
        </div>
      </section>

      <AiAnalysis analysis={analysis} error={aiError} />

      <button
        type="button"
        onClick={onReset}
        className="w-full rounded-md border border-emerald-700 px-4 py-2 font-medium text-emerald-700 hover:bg-emerald-50"
      >
        New assessment
      </button>
    </div>
  )
}

export default Results
