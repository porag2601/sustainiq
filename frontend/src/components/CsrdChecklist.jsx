import { ESRS_LABELS, esrsLabel } from '../metrics'

// Checkboxes for the CSRD data checklist, grouped by ESRS standard.
// "Controlled" component: the parent owns the list of ticked ids (selected)
// and gets every change through onChange(newSelectedIds).
function CsrdChecklist({ items, selected, onChange }) {
  function toggle(id) {
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id])
  }

  // Standards in a fixed order (ESRS 2, E1, E2, E3, E5), each with its items.
  const groups = Object.keys(ESRS_LABELS)
    .map((standard) => ({ standard, items: items.filter((item) => item.standard === standard) }))
    .filter((group) => group.items.length > 0)

  return (
    <div className="space-y-4">
      {groups.map((group) => (
        // fieldset + legend: screen readers announce the group name for each checkbox.
        <fieldset key={group.standard}>
          <legend className="text-sm font-semibold text-slate-700">{esrsLabel(group.standard)}</legend>
          <div className="mt-2 space-y-2">
            {group.items.map((item) => (
              <label key={item.id} className="flex cursor-pointer items-start gap-3 text-sm">
                <input
                  type="checkbox"
                  checked={selected.includes(item.id)}
                  onChange={() => toggle(item.id)}
                  className="mt-0.5 h-4 w-4 accent-emerald-700"
                />
                <span>
                  <span className="font-medium">{item.title}</span>{' '}
                  <span className="text-slate-500">({item.reference})</span>
                  <span className="block text-slate-500">{item.hint}</span>
                </span>
              </label>
            ))}
          </div>
        </fieldset>
      ))}
    </div>
  )
}

export default CsrdChecklist
