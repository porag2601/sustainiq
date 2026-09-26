import { useEffect, useState } from 'react'
import { getAssessment, listAssessments } from '../api/client'
import { formatDate, sectorLabel } from '../metrics'

// List of saved assessments. Clicking a row loads the full report and hands
// it to onOpen(result, companyName), the same callback the form uses.
function PastAssessments({ onOpen }) {
  const [rows, setRows] = useState(null) // null = still loading
  const [error, setError] = useState(null)
  const [openingId, setOpeningId] = useState(null)

  // Load the list once when the component appears on screen.
  useEffect(() => {
    // If the component disappears before the answer arrives, ignore the
    // answer (React would warn about updating a component that is gone).
    let ignore = false
    listAssessments()
      .then((data) => !ignore && setRows(data))
      .catch((err) => !ignore && setError(err.message))
    return () => {
      ignore = true
    }
  }, [])

  async function open(row) {
    setOpeningId(row.id)
    setError(null)
    try {
      onOpen(await getAssessment(row.id), row.company_name)
    } catch (err) {
      setError(err.message)
      setOpeningId(null)
    }
  }

  return (
    <section className="rounded-lg bg-white p-6 shadow">
      <h2 className="text-xl font-semibold">Past assessments</h2>

      {error && (
        <p role="alert" className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}
      {!error && rows === null && <p className="mt-4 text-sm text-slate-500">Loading…</p>}
      {rows?.length === 0 && (
        <p className="mt-4 text-sm text-slate-500">No saved assessments yet. Run your first one above.</p>
      )}

      {rows?.length > 0 && (
        <table className="mt-4 w-full text-left text-sm">
          <thead className="border-b border-slate-200 text-slate-500">
            <tr>
              <th className="py-2 font-medium">Date</th>
              <th className="py-2 font-medium">Company</th>
              <th className="hidden py-2 font-medium sm:table-cell">Sector</th>
              <th className="py-2 text-right font-medium">Score</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b border-slate-100 last:border-0">
                <td className="py-2 whitespace-nowrap text-slate-600">{formatDate(row.created_at)}</td>
                <td className="py-2">
                  {/* A real <button>, so the row works with keyboard and screen readers. */}
                  <button
                    type="button"
                    onClick={() => open(row)}
                    disabled={openingId !== null}
                    className="text-left text-emerald-700 underline hover:text-emerald-900 disabled:opacity-50"
                  >
                    {openingId === row.id ? 'Opening…' : row.company_name}
                  </button>
                </td>
                <td className="hidden py-2 text-slate-600 sm:table-cell">{sectorLabel(row.sector)}</td>
                <td className="py-2 text-right font-medium">{row.overall_score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

export default PastAssessments
