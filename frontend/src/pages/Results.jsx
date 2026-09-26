import { assessmentPdfUrl } from '../api/client'
import AiAnalysis from '../components/AiAnalysis'
import BenchmarkChart from '../components/BenchmarkChart'
import CsrdReadiness from '../components/CsrdReadiness'
import MetricCard from '../components/MetricCard'
import ProgressChart from '../components/ProgressChart'
import ScoreGauge from '../components/ScoreGauge'
import { formatDate } from '../metrics'

// result = { id, created_at, score, ai_analysis, ai_error } from the backend.
function Results({ result, companyName, checklist, onReset }) {
  const { score, ai_analysis: analysis, ai_error: aiError } = result

  return (
    <div className="space-y-8">
      <section className="rounded-lg bg-white p-6 text-center shadow">
        <p className="mb-4 text-sm text-slate-500">Sustainability score for {companyName}</p>
        <ScoreGauge score={score.overall_score} />
        <p className="mt-4 text-xs text-slate-500">
          50 = exactly at the sector benchmark. Benchmarks are indicative estimates, not official statistics.
        </p>
        {result.id && (
          <p className="mt-1 text-xs text-slate-500">
            Assessment #{result.id} · saved {formatDate(result.created_at)}
          </p>
        )}
      </section>

      <ProgressChart companyName={companyName} />

      <BenchmarkChart metrics={score.metrics} />

      <section>
        <h2 className="mb-4 text-xl font-semibold">Benchmark comparison</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {score.metrics.map((metric) => (
            <MetricCard key={metric.key} metric={metric} />
          ))}
        </div>
      </section>

      {/* Assessments saved before the checklist existed have csrd = null. */}
      {result.csrd && <CsrdReadiness readiness={result.csrd} checklist={checklist} />}

      <AiAnalysis analysis={analysis} source={result.analysis_source} error={aiError} />

      <div className="flex flex-col gap-3 sm:flex-row">
        {/* Only saved assessments have an id, and the PDF is built from the saved data. */}
        {result.id && (
          <a
            href={assessmentPdfUrl(result.id)}
            className="flex-1 rounded-md bg-emerald-700 px-4 py-2 text-center font-medium text-white hover:bg-emerald-800"
          >
            Download PDF report
          </a>
        )}
        <button
          type="button"
          onClick={onReset}
          className="flex-1 rounded-md border border-emerald-700 px-4 py-2 font-medium text-emerald-700 hover:bg-emerald-50"
        >
          New assessment
        </button>
      </div>
    </div>
  )
}

export default Results
