"use client"
import { useState } from "react"
import useSWR from "swr"
import api from "@/lib/api"

const fetcher = (url: string) => api.get(url).then(r => r.data)

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

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Assignments</h1>

      {/* Add Form */}
      <div className="bg-white rounded-lg p-5 shadow-sm border mb-6">
        <h2 className="font-medium mb-3">Add Assignment</h2>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <input
            placeholder="Title *"
            value={title}
            onChange={e => setTitle(e.target.value)}
            className="border rounded px-3 py-2 text-sm col-span-2"
          />
          <input
            placeholder="Course"
            value={course}
            onChange={e => setCourse(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            type="number"
            placeholder="Estimated hours"
            value={hours}
            onChange={e => setHours(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            type="datetime-local"
            value={dueDate}
            onChange={e => setDueDate(e.target.value)}
            className="border rounded px-3 py-2 text-sm col-span-2"
          />
        </div>
        <button
          onClick={handleAdd}
          disabled={loading}
          className="bg-black text-white px-4 py-2 rounded text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
        >
          {loading ? "Adding..." : "Add Assignment"}
        </button>
      </div>

      {/* Assignment List */}
      <div className="bg-white rounded-lg shadow-sm border divide-y">
        {!data || data.length === 0 ? (
          <p className="p-5 text-sm text-gray-400">No assignments yet. Add one above.</p>
        ) : (
          data.map((a: any) => (
            <div key={a.id} className="p-4 flex items-center justify-between">
              <div>
                <p className={`font-medium text-sm ${a.status === "done" ? "line-through text-gray-400" : ""}`}>
                  {a.title}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {a.course && `${a.course} · `}
                  Due {new Date(a.due_date).toLocaleDateString()} · {a.estimated_hours}h
                </p>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={a.status}
                  onChange={e => handleStatusChange(a.id, e.target.value)}
                  className="text-xs border rounded px-2 py-1"
                >
                  <option value="pending">Pending</option>
                  <option value="done">Done</option>
                  <option value="overdue">Overdue</option>
                </select>
                <button
                  onClick={() => handleDelete(a.id)}
                  className="text-xs text-red-400 hover:text-red-600"
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