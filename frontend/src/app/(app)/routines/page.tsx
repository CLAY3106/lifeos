"use client"
import { useState } from "react"
import useSWR from "swr"
import api from "@/lib/api"
import { ActivityIcon, PlusIcon, TrashIcon } from "@/components/icons"

const fetcher = (url: string) => api.get(url).then(r => r.data)

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

const inputClass =
  "border border-[var(--rule)] rounded-md px-3 py-2 text-sm bg-[var(--surface)] text-[var(--foreground)] placeholder:text-[var(--muted-2)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-colors"

export default function RoutinesPage() {
  const { data, mutate } = useSWR("/routines", fetcher)
  const [name, setName] = useState("")
  const [loading, setLoading] = useState(false)

  // Inline item form state per routine
  const [addingToRoutine, setAddingToRoutine] = useState<string | null>(null)
  const [itemName, setItemName] = useState("")
  const [itemSets, setItemSets] = useState("")
  const [itemReps, setItemReps] = useState("")
  const [itemDuration, setItemDuration] = useState("")
  const [itemDay, setItemDay] = useState("")
  const [itemLoading, setItemLoading] = useState(false)

  async function handleCreateRoutine() {
    if (!name.trim()) return
    setLoading(true)
    try {
      await api.post("/routines", { name: name.trim() })
      setName("")
      mutate()
    } finally {
      setLoading(false)
    }
  }

  async function handleAddItem(routineId: string) {
    if (!itemName.trim()) return
    setItemLoading(true)
    try {
      await api.patch(`/routines/${routineId}`, {})
      // Create a new routine with the item by re-creating
      // Actually we need a dedicated item endpoint. For now, use the create with items approach.
      // Let's add items via a nested POST
      await api.post(`/routines/${routineId}/items`, {
        exercise_name: itemName.trim(),
        sets: itemSets ? parseInt(itemSets) : null,
        reps: itemReps ? parseInt(itemReps) : null,
        duration_mins: itemDuration ? parseInt(itemDuration) : null,
        day_of_week: itemDay || null,
      })
      setItemName("")
      setItemSets("")
      setItemReps("")
      setItemDuration("")
      setItemDay("")
      setAddingToRoutine(null)
      mutate()
    } finally {
      setItemLoading(false)
    }
  }

  async function handleDeleteRoutine(id: string) {
    await api.delete(`/routines/${id}`)
    mutate()
  }

  async function handleDeleteItem(routineId: string, itemId: string) {
    await api.delete(`/routines/${routineId}/items/${itemId}`)
    mutate()
  }

  return (
    <div className="max-w-3xl mx-auto px-16 py-16">
      <div className="flex items-center gap-2.5 mb-8">
        <div className="w-10 h-10 rounded-lg bg-[var(--callout-purple)] flex items-center justify-center shrink-0">
          <ActivityIcon className="w-5 h-5 text-[var(--foreground)]" />
        </div>
        <h1 className="text-2xl font-bold text-[var(--foreground)]">Routines</h1>
      </div>

      {/* Create Routine Form */}
      <div className="bg-[var(--surface)] rounded-lg p-6 shadow-sm border border-[var(--rule)] mb-8">
        <h2 className="text-sm font-semibold text-[var(--foreground)] mb-4">New Routine</h2>
        <div className="flex gap-3">
          <input
            placeholder="Routine name (e.g. Push Day) *"
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleCreateRoutine()}
            className={`${inputClass} flex-1`}
          />
          <button
            onClick={handleCreateRoutine}
            disabled={loading}
            className="bg-[var(--accent)] text-white px-4 py-2 rounded-md text-sm font-medium cursor-pointer transition-opacity hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-offset-2 focus:ring-offset-[var(--surface)]"
          >
            {loading ? "Creating..." : "Create"}
          </button>
        </div>
      </div>

      {/* Routines List */}
      <div className="space-y-4">
        {!data || data.length === 0 ? (
          <div className="bg-[var(--surface)] rounded-lg border border-dashed border-[var(--rule)] py-12 text-center">
            <ActivityIcon className="w-8 h-8 mx-auto mb-3 text-[var(--muted-2)]" />
            <p className="text-sm text-[var(--muted)]">No routines yet. Create one above.</p>
          </div>
        ) : (
          data.map((routine: any) => (
            <div
              key={routine.id}
              className="bg-[var(--surface)] rounded-lg border border-[var(--rule)] shadow-sm overflow-hidden"
            >
              {/* Routine Header */}
              <div className="px-5 py-4 flex items-center justify-between border-b border-[var(--rule)]">
                <div>
                  <h3 className="font-semibold text-[var(--foreground)]">{routine.name}</h3>
                  <p className="text-xs text-[var(--muted)] mt-0.5">
                    {routine.items.length} exercise{routine.items.length !== 1 ? "s" : ""}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setAddingToRoutine(addingToRoutine === routine.id ? null : routine.id)}
                    className="text-xs text-[var(--accent)] hover:opacity-80 cursor-pointer transition-opacity flex items-center gap-1"
                  >
                    <PlusIcon className="w-3.5 h-3.5" />
                    Add Exercise
                  </button>
                  <button
                    onClick={() => handleDeleteRoutine(routine.id)}
                    className="p-1.5 rounded-md text-[var(--muted-2)] hover:text-[var(--danger)] hover:bg-[var(--callout-red)] cursor-pointer transition-colors"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Add Item Form (inline) */}
              {addingToRoutine === routine.id && (
                <div className="px-5 py-4 bg-[var(--callout-gray)] border-b border-[var(--rule)]">
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    <input
                      placeholder="Exercise name *"
                      value={itemName}
                      onChange={e => setItemName(e.target.value)}
                      className={`${inputClass} col-span-2`}
                    />
                    <input
                      type="number"
                      placeholder="Sets"
                      value={itemSets}
                      onChange={e => setItemSets(e.target.value)}
                      className={inputClass}
                    />
                    <input
                      type="number"
                      placeholder="Reps"
                      value={itemReps}
                      onChange={e => setItemReps(e.target.value)}
                      className={inputClass}
                    />
                    <input
                      type="number"
                      placeholder="Duration (min)"
                      value={itemDuration}
                      onChange={e => setItemDuration(e.target.value)}
                      className={inputClass}
                    />
                    <select
                      value={itemDay}
                      onChange={e => setItemDay(e.target.value)}
                      className={inputClass}
                    >
                      <option value="">Any day</option>
                      {DAYS.map(d => (
                        <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleAddItem(routine.id)}
                      disabled={itemLoading}
                      className="bg-[var(--accent)] text-white px-3 py-1.5 rounded-md text-xs font-medium cursor-pointer transition-opacity hover:opacity-90 disabled:opacity-50"
                    >
                      {itemLoading ? "Adding..." : "Add"}
                    </button>
                    <button
                      onClick={() => setAddingToRoutine(null)}
                      className="text-xs text-[var(--muted)] hover:text-[var(--foreground)] cursor-pointer transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {/* Items List */}
              {routine.items.length === 0 ? (
                <div className="px-5 py-6 text-center">
                  <p className="text-sm text-[var(--muted-2)]">No exercises yet.</p>
                </div>
              ) : (
                <div className="divide-y divide-[var(--rule)]">
                  {routine.items.map((item: any) => (
                    <div
                      key={item.id}
                      className="px-5 py-3 flex items-center justify-between hover:bg-[var(--surface-hover)] transition-colors"
                    >
                      <div className="min-w-0">
                        <p className="font-medium text-sm text-[var(--foreground)]">
                          {item.exercise_name}
                        </p>
                        <p className="text-xs text-[var(--muted-2)] mt-0.5">
                          {[
                            item.sets && item.reps ? `${item.sets}x${item.reps}` : null,
                            item.duration_mins && `${item.duration_mins} min`,
                            item.day_of_week && item.day_of_week.charAt(0).toUpperCase() + item.day_of_week.slice(1),
                          ]
                            .filter(Boolean)
                            .join(" · ")}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteItem(routine.id, item.id)}
                        className="text-xs text-[var(--muted-2)] hover:text-[var(--danger)] cursor-pointer transition-colors shrink-0"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
