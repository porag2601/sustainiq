import { useState } from 'react'
import AssessmentForm from './pages/AssessmentForm'
import Results from './pages/Results'

// Root component. Shows the form until a result exists, then the results page.
// Two "pages" only, so a simple if/else is enough; no router library needed yet.
function App() {
  const [result, setResult] = useState(null)
  const [companyName, setCompanyName] = useState('')

  function handleResult(newResult, name) {
    setResult(newResult)
    setCompanyName(name)
    window.scrollTo({ top: 0 })
  }

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

        {result ? (
          <Results result={result} companyName={companyName} onReset={() => setResult(null)} />
        ) : (
          <AssessmentForm onResult={handleResult} />
        )}
      </div>
    </main>
  )
}

export default App
