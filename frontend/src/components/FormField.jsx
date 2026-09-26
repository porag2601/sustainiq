// One labelled input with an optional unit and error message.
// Reused for all form fields so they look and behave the same.
function FormField({ label, name, value, onChange, error, unit, type = 'number', ...inputProps }) {
  return (
    <div>
      <label htmlFor={name} className="block text-sm font-medium text-slate-700">
        {label}
        {unit && <span className="font-normal text-slate-500"> ({unit})</span>}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        required
        // aria-invalid lets screen readers announce the error state.
        aria-invalid={Boolean(error)}
        className={`mt-1 w-full rounded-md border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
          error ? 'border-red-500' : 'border-slate-300'
        }`}
        // min, max, step etc. are passed straight to the <input>.
        {...inputProps}
      />
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  )
}

export default FormField
