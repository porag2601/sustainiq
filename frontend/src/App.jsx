import { Suspense, lazy, useState } from 'react'
import PastAssessments from './components/PastAssessments'
import AssessmentForm from './pages/AssessmentForm'

// Code splitting: Results (and the large Recharts library it uses) is loaded
// only when the first result arrives, so the form page opens faster.
const Results = lazy(() => import('./pages/Results'))

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
          // Suspense shows the fallback while the Results code is downloading.
          <Suspense fallback={<p className="text-center text-slate-500">Loading results…</p>}>
            <Results result={result} companyName={companyName} onReset={() => setResult(null)} />
          </Suspense>
        ) : (
          <>
            <AssessmentForm onResult={handleResult} />
            {/* Mounted again each time the form is shown, so the list is always fresh. */}
            <PastAssessments onOpen={handleResult} />
          </>
        )}
      </div>
    </main>
  )
}

export default App
