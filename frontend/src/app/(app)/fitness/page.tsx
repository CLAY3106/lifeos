"use client"
import { useState } from "react"
import useSWR from "swr"
import api from "@/lib/api"
import { ActivityIcon } from "@/components/icons"

const fetcher = (url: string) => api.get(url).then(r => r.data)

export default function FitnessPage() {
  const { data, mutate } = useSWR("/workouts", fetcher)
  const [type, setType] = useState("")
  const [duration, setDuration] = useState("30")
  const [loading, setLoading] = useState(false)

  async function handleAdd() {
    if (!type) return
    setLoading(true)
    try {
      await api.post("/workouts", {
        type,
        duration_mins: parseInt(duration),
      })
      setType("")
      setDuration("30")
      mutate()
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: string) {
    await api.delete(`/workouts/${id}`)
    mutate()
  }

  return (
    <div className="max-w-3xl mx-auto px-16 py-16">
      <div className="flex items-center gap-2.5 mb-8">
        <ActivityIcon className="w-6 h-6 text-[var(--accent)]" />
        <h1 className="text-2xl font-semibold tracking-tight text-[var(--foreground)]">Fitness</h1>
      </div>

      {/* Add Form */}
      <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-xl p-6 shadow-sm mb-8">
        <h2 className="text-sm font-semibold text-[var(--foreground)] mb-4">Log Workout</h2>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <input
            placeholder="Type (e.g. Run, Gym, Yoga) *"
            value={type}
            onChange={e => setType(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleAdd()}
            className="col-span-2 border border-[var(--rule)] bg-[var(--surface)] text-[var(--foreground)] placeholder:text-[var(--muted-2)] rounded-md px-3 py-2.5 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:border-[var(--accent)] transition-colors"
          />
          <input
            type="number"
            placeholder="Duration (minutes)"
            value={duration}
            onChange={e => setDuration(e.target.value)}
            className="border border-[var(--rule)] bg-[var(--surface)] text-[var(--foreground)] placeholder:text-[var(--muted-2)] rounded-md px-3 py-2.5 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:border-[var(--accent)] transition-colors"
          />
        </div>
        <button
          onClick={handleAdd}
          disabled={loading}
          className="bg-[var(--accent)] text-white px-4 py-2 rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2"
        >
          {loading ? "Adding..." : "Log Workout"}
        </button>
      </div>

      {/* Workout List */}
      <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-xl shadow-sm divide-y divide-[var(--rule)] overflow-hidden">
        {!data || data.length === 0 ? (
          <div className="p-10 flex flex-col items-center text-center gap-2">
            <ActivityIcon className="w-6 h-6 text-[var(--muted-2)]" />
            <p className="text-sm text-[var(--muted-2)]">No workouts yet. Log one above.</p>
          </div>
        ) : (
          data.map((w: any) => (
            <div
              key={w.id}
              className="p-4 flex items-center justify-between gap-4 hover:bg-[var(--surface-hover)] transition-colors"
            >
              <div className="min-w-0">
                <p className="font-medium text-sm text-[var(--foreground)] truncate">{w.type}</p>
                <p className="text-xs text-[var(--muted-2)] mt-0.5">
                  {w.duration_mins} min · {new Date(w.logged_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={() => handleDelete(w.id)}
                className="text-xs text-[var(--danger)] hover:opacity-75 cursor-pointer transition-opacity shrink-0 rounded outline-none focus-visible:ring-2 focus-visible:ring-[var(--danger)]"
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}