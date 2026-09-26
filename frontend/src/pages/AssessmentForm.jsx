import { useState } from 'react'
import { ValidationError, analyseCompany } from '../api/client'
import CsrdChecklist from '../components/CsrdChecklist'
import FormField from '../components/FormField'
import { SECTORS } from '../metrics'

// Number fields. min/max mirror the backend rules, so the browser catches
// most mistakes before sending; the backend still checks everything.
const NUMBER_FIELDS = [
  { name: 'employees_fte', label: 'Employees', unit: 'FTE', min: 0.1, step: 0.1 },
  { name: 'energy_kwh', label: 'Energy use', unit: 'kWh / year', min: 0, step: 'any' },
  { name: 'renewable_share_pct', label: 'Renewable share', unit: '%', min: 0, max: 100, step: 'any' },
  { name: 'scope12_emissions_t', label: 'Scope 1+2 emissions', unit: 't CO2e / year', min: 0, step: 'any' },
  { name: 'waste_t', label: 'Waste', unit: 't / year', min: 0, step: 'any' },
  { name: 'recycling_rate_pct', label: 'Recycling rate', unit: '%', min: 0, max: 100, step: 'any' },
  { name: 'water_m3', label: 'Water use', unit: 'm³ / year', min: 0, step: 'any' },
]

const EMPTY_FORM = {
  company_name: '',
  sector: 'manufacturing',
  ...Object.fromEntries(NUMBER_FIELDS.map((field) => [field.name, ''])),
  csrd_available: [], // ids of ticked checklist items
}

// A realistic example so the form can be tested with one click.
const EXAMPLE = {
  company_name: 'Muster Metallbau GmbH',
  sector: 'manufacturing',
  employees_fte: '45',
  energy_kwh: '850000',
  renewable_share_pct: '30',
  scope12_emissions_t: '320',
  waste_t: '60',
  recycling_rate_pct: '55',
  water_m3: '1200',
  csrd_available: ['e1_energy_mix', 'e1_scope12', 'e3_water', 'e5_waste'],
}

// checklist: CSRD checklist items from the backend (null while loading or if unavailable).
function AssessmentForm({ onResult, checklist }) {
  // One state object for all fields. Inputs always give strings,
  // so numbers are converted only when sending.
  const [form, setForm] = useState(EMPTY_FORM)
  const [fieldErrors, setFieldErrors] = useState({})
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  function handleChange(event) {
    const { name, value } = event.target
    setForm((previous) => ({ ...previous, [name]: value }))
  }

  async function handleSubmit(event) {
    // Stop the browser's default full-page form submit.
    event.preventDefault()
    setLoading(true)
    setError(null)
    setFieldErrors({})

    const payload = {
      ...form,
      ...Object.fromEntries(NUMBER_FIELDS.map((field) => [field.name, Number(form[field.name])])),
    }

    try {
      onResult(await analyseCompany(payload), payload.company_name)
    } catch (err) {
      if (err instanceof ValidationError) setFieldErrors(err.fieldErrors)
      setError(err.message)
    } finally {
      // Runs after success and after errors, so the button never stays disabled.
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 rounded-lg bg-white p-6 shadow">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Company data (last full year)</h2>
        <button
          type="button"
          onClick={() => setForm(EXAMPLE)}
          className="text-sm text-emerald-700 underline hover:text-emerald-900"
        >
          Fill example data
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          label="Company name"
          name="company_name"
          type="text"
          maxLength={200}
          value={form.company_name}
          onChange={handleChange}
          error={fieldErrors.company_name}
        />
        <div>
          <label htmlFor="sector" className="block text-sm font-medium text-slate-700">
            Sector
          </label>
          <select
            id="sector"
            name="sector"
            value={form.sector}
            onChange={handleChange}
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {SECTORS.map((sector) => (
              <option key={sector.value} value={sector.value}>
                {sector.label}
              </option>
            ))}
          </select>
          {fieldErrors.sector && <p className="mt-1 text-sm text-red-600">{fieldErrors.sector}</p>}
        </div>

        {NUMBER_FIELDS.map(({ name, ...field }) => (
          <FormField
            key={name}
            name={name}
            value={form[name]}
            onChange={handleChange}
            error={fieldErrors[name]}
            {...field}
          />
        ))}
      </div>

      {/* The checklist is optional: if it could not be loaded, the form still works. */}
      {checklist?.length > 0 && (
        <div className="border-t border-slate-200 pt-6">
          <h3 className="font-semibold">CSRD data checklist (optional)</h3>
          <p className="mt-1 text-sm text-slate-600">
            Tick the data your company already collects. This shows your CSRD reporting readiness and
            focuses the AI on the gaps.
          </p>
          <div className="mt-4">
            <CsrdChecklist
              items={checklist}
              selected={form.csrd_available}
              onChange={(ids) => setForm((previous) => ({ ...previous, csrd_available: ids }))}
            />
          </div>
          {fieldErrors.csrd_available && (
            <p className="mt-2 text-sm text-red-600">{fieldErrors.csrd_available}</p>
          )}
        </div>
      )}

      {error && (
        <p role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-md bg-emerald-700 px-4 py-2 font-medium text-white hover:bg-emerald-800 disabled:opacity-50"
      >
        {/* The AI part can take several seconds, so show that something is happening. */}
        {loading ? 'Analysing… (this can take up to a minute)' : 'Analyse'}
      </button>
    </form>
  )
}

export default AssessmentForm
