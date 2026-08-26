"use client"
import { useState } from "react"
import useSWR from "swr"
import api from "@/lib/api"
import { BookIcon } from "@/components/icons"

const fetcher = (url: string) => api.get(url).then(r => r.data)

const STATUS_STYLES: Record<string, string> = {
  pending: "text-[var(--foreground)]",
  done: "text-[var(--muted-2)]",
  overdue: "text-[var(--danger)]",
}

export default function AssignmentsPage() {
  const { data, mutate } = useSWR("/assignments", fetcher)
  const [title, setTitle] = useState("")
  const [course, setCourse] = useState("")
  const [dueDate, setDueDate] = useState("")
  const [hours, setHours] = useState("1")
  const [loading, setLoading] = useState(false)

  async function handleAdd() {
    if (!title || !dueDate) return
    setLoading(true)
    try {
      await api.post("/assignments", {
        title,
        course,
        due_date: new Date(dueDate).toISOString(),
        estimated_hours: parseFloat(hours)
      })
      setTitle("")
      setCourse("")
      setDueDate("")
      setHours("1")
      mutate()
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: string) {
    await api.delete(`/assignments/${id}`)
    mutate()
  }

  async function handleStatusChange(id: string, status: string) {
    await api.patch(`/assignments/${id}`, { status })
    mutate()
  }

  const inputClass =
    "border border-[var(--rule)] bg-[var(--surface)] text-[var(--foreground)] placeholder:text-[var(--muted-2)] rounded px-3 py-2 text-sm outline-none transition-colors focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/25"

  return (
    <div className="max-w-3xl mx-auto px-16 py-16">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-lg bg-[var(--callout-blue)] flex items-center justify-center shrink-0">
          <BookIcon className="w-5 h-5 text-[var(--foreground)]" />
        </div>
        <h1 className="text-2xl font-bold text-[var(--foreground)]">Assignments</h1>
      </div>

      {/* Add Form */}
      <div className="bg-[var(--surface)] rounded-lg p-6 shadow-sm border border-[var(--rule)] mb-8">
        <h2 className="text-sm font-semibold text-[var(--foreground)] mb-4">Add Assignment</h2>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <input
            placeholder="Title *"
            value={title}
            onChange={e => setTitle(e.target.value)}
            className={`${inputClass} col-span-2`}
          />
          <input
            placeholder="Course"
            value={course}
            onChange={e => setCourse(e.target.value)}
            className={inputClass}
          />
          <input
            type="number"
            placeholder="Estimated hours"
            value={hours}
            onChange={e => setHours(e.target.value)}
            className={inputClass}
          />
          <input
            type="datetime-local"
            value={dueDate}
            onChange={e => setDueDate(e.target.value)}
            className={`${inputClass} col-span-2`}
          />
        </div>
        <button
          onClick={handleAdd}
          disabled={loading}
          className="bg-[var(--accent)] text-white px-4 py-2 rounded-md text-sm font-medium cursor-pointer transition-opacity hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-offset-2 focus:ring-offset-[var(--surface)]"
        >
          {loading ? "Adding..." : "Add Assignment"}
        </button>
      </div>

      {/* Assignment List */}
      <div className="bg-[var(--surface)] rounded-lg shadow-sm border border-[var(--rule)] divide-y divide-[var(--rule)]">
        {!data || data.length === 0 ? (
          <p className="p-6 text-sm text-[var(--muted-2)]">No assignments yet. Add one above.</p>
        ) : (
          data.map((a: any) => (
            <div
              key={a.id}
              className="p-4 flex items-center justify-between gap-4 transition-colors hover:bg-[var(--surface-hover)]"
            >
              <div className="min-w-0">
                <p
                  className={`font-medium text-sm truncate ${
                    a.status === "done" ? "line-through text-[var(--muted-2)]" : "text-[var(--foreground)]"
                  }`}
                >
                  {a.title}
                </p>
                <p className="text-xs text-[var(--muted-2)] mt-0.5">
                  {a.course && `${a.course} · `}
                  Due {new Date(a.due_date).toLocaleDateString()} · {a.estimated_hours}h
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <select
                  value={a.status}
                  onChange={e => handleStatusChange(a.id, e.target.value)}
                  className={`text-xs border border-[var(--rule)] bg-[var(--surface)] rounded px-2 py-1 cursor-pointer outline-none transition-colors focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/25 ${
                    STATUS_STYLES[a.status] ?? "text-[var(--foreground)]"
                  }`}
                >
                  <option value="pending">Pending</option>
                  <option value="done">Done</option>
                  <option value="overdue">Overdue</option>
                </select>
                <button
                  onClick={() => handleDelete(a.id)}
                  className="text-xs text-[var(--muted-2)] hover:text-[var(--danger)] cursor-pointer transition-colors outline-none focus:text-[var(--danger)] focus:ring-2 focus:ring-[var(--accent)]/25 rounded px-1 py-0.5"
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
