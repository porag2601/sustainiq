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

// Send one company's data and return { score, ai_analysis, ai_error }.
export async function analyseCompany(data) {
  let response
  try {
    response = await fetch(`${API_URL}/analyse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
  } catch {
    // fetch() only throws when there is no response at all:
    // backend not running, wrong URL, or blocked by CORS.
    throw new Error(`Cannot reach the backend at ${API_URL}. Is it running?`)
  }

  if (response.status === 422) {
    const body = await response.json()
    throw new ValidationError(toFieldErrors(body.detail))
  }
  if (!response.ok) {
    throw new Error(`The server returned an error (HTTP ${response.status}).`)
  }
  return response.json()
}
