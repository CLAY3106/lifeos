// Scrolls an add form into view and focuses its first field. Used by the empty
// state buttons so "Add the first ..." lands the user in the real form.
export function focusForm(id: string): void {
  if (typeof document === "undefined") return
  const el = document.getElementById(id)
  if (!el) return
  el.scrollIntoView({ behavior: "smooth", block: "center" })
  const field = el.querySelector("input, select, textarea")
  if (field instanceof HTMLInputElement || field instanceof HTMLSelectElement) {
    field.focus({ preventScroll: true })
  }
}
