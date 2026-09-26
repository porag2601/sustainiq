// Every call to the backend lives in this file. Components never call fetch()
// directly, so the API URL, headers and error handling exist in one place only.

// Vite exposes variables that start with VITE_ from frontend/.env.
// In production (Vercel) this is set to the Render backend URL.
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// Thrown when the backend rejects input (HTTP 422).
// fieldErrors maps a field name to its message, e.g. { water_m3: '...' },
// so the form can show each message under the right input.
export class ValidationError extends Error {
  constructor(fieldErrors) {
    super('Some values are invalid. Please check the highlighted fields.')
    this.fieldErrors = fieldErrors
  }
}

// FastAPI 422 body: { detail: [{ loc: ['body', 'water_m3'], msg: '...' }] }
function toFieldErrors(detail) {
  const errors = {}
  for (const item of detail ?? []) {
    const field = item.loc?.[1] ?? '_form'
    errors[field] = item.msg
  }
  return errors
}

// Shared by all calls below: sends the request and turns every kind of
// failure into an Error with a message the user can understand.
async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API_URL}${path}`, options)
  } catch {
    // fetch() only throws when there is no response at all:
    // backend not running, wrong URL, or blocked by CORS.
    throw new Error(`Cannot reach the backend at ${API_URL}. Is it running?`)
  }

  if (response.status === 422) {
    const body = await response.json()
    throw new ValidationError(toFieldErrors(body.detail))
  }
  if (response.status === 404) {
    throw new Error('Not found. It may have been deleted.')
  }
  if (!response.ok) {
    throw new Error(`The server returned an error (HTTP ${response.status}).`)
  }
  return response.json()
}

// Score, analyse and save one company. Returns { id, created_at, score, ai_analysis, ai_error }.
export function analyseCompany(data) {
  return request('/analyse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

// Saved assessments, newest first: [{ id, created_at, company_name, sector, overall_score }].
// With companyName, only that company's history (for progress tracking).
export function listAssessments(companyName) {
  // URLSearchParams encodes spaces and characters like "&" safely.
  const query = companyName ? `?${new URLSearchParams({ company_name: companyName })}` : ''
  return request(`/assessments${query}`)
}

// One saved assessment, in the same shape as analyseCompany() returns.
export function getAssessment(id) {
  return request(`/assessments/${id}`)
}

// Link target for the PDF report. A normal link (not fetch) is enough:
// the backend sends "Content-Disposition: attachment", so the browser downloads it.
export function assessmentPdfUrl(id) {
  return `${API_URL}/assessments/${id}/pdf`
}
