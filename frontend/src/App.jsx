import { useState } from 'react'
import AssessmentForm from './pages/AssessmentForm'

// Root component: holds the latest result and shows the form.
// The raw JSON view is temporary; the Results page replaces it next step.
function App() {
  const [result, setResult] = useState(null)

  return (
    <main className="min-h-screen bg-slate-50 text-slate-800">
      <div className="mx-auto max-w-3xl space-y-8 px-4 py-12">
        <header>
          <h1 className="text-4xl font-bold text-emerald-700">SustainIQ</h1>
          <p className="mt-2 text-lg">
            Sustainability assessment for German SMEs: EU benchmarking,
            CSRD/ESRS gap analysis and AI recommendations.
          </p>
        </header>

        <AssessmentForm onResult={setResult} />

        {result && (
          <section className="rounded-lg bg-white p-6 shadow">
            <h2 className="text-xl font-semibold">
              Overall score: {result.score.overall_score} / 100
            </h2>
            <pre className="mt-4 max-h-96 overflow-auto rounded bg-slate-100 p-4 text-xs">
              {JSON.stringify(result, null, 2)}
            </pre>
          </section>
        )}
      </div>
    </main>
  )
}

export default App
