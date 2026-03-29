"use client"
import { useState } from "react"
import useSWR from "swr"
import api from "@/lib/api"

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
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Fitness</h1>

      {/* Add Form */}
      <div className="bg-white rounded-lg p-5 shadow-sm border mb-6">
        <h2 className="font-medium mb-3">Log Workout</h2>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <input
            placeholder="Type (e.g. Run, Gym, Yoga) *"
            value={type}
            onChange={e => setType(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleAdd()}
            className="border rounded px-3 py-2 text-sm col-span-2"
          />
          <input
            type="number"
            placeholder="Duration (minutes)"
            value={duration}
            onChange={e => setDuration(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          />
        </div>
        <button
          onClick={handleAdd}
          disabled={loading}
          className="bg-black text-white px-4 py-2 rounded text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
        >
          {loading ? "Adding..." : "Log Workout"}
        </button>
      </div>

      {/* Workout List */}
      <div className="bg-white rounded-lg shadow-sm border divide-y">
        {!data || data.length === 0 ? (
          <p className="p-5 text-sm text-gray-400">No workouts yet. Log one above.</p>
        ) : (
          data.map((w: any) => (
            <div key={w.id} className="p-4 flex items-center justify-between">
              <div>
                <p className="font-medium text-sm">{w.type}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {w.duration_mins} min · {new Date(w.logged_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={() => handleDelete(w.id)}
                className="text-xs text-red-400 hover:text-red-600"
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