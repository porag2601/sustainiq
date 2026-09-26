// Root component. For now a simple start page that proves React and Tailwind
// work; the assessment form and results page are added in the next steps.
function App() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-800">
      <div className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="text-4xl font-bold text-emerald-700">SustainIQ</h1>
        <p className="mt-4 text-lg">
          Sustainability assessment for German SMEs: EU benchmarking,
          CSRD/ESRS gap analysis and AI recommendations.
        </p>
        <p className="mt-8 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm">
          Frontend is running. The assessment form comes next.
        </p>
      </div>
    </main>
  )
}

export default App
