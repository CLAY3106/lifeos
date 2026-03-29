"use client"
import { useState } from "react"
import useSWR from "swr"
import api from "@/lib/api"

const fetcher = (url: string) => api.get(url).then(r => r.data)

const STATUS_COLORS: Record<string, string> = {
  applied: "bg-blue-100 text-blue-700",
  interview: "bg-yellow-100 text-yellow-700",
  offer: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
}

const STATUSES = ["applied", "interview", "offer", "rejected"]

export default function JobsPage() {
  const { data, mutate } = useSWR("/jobs", fetcher)
  const [company, setCompany] = useState("")
  const [role, setRole] = useState("")
  const [appliedDate, setAppliedDate] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleAdd() {
    if (!company || !role || !appliedDate) return
    setLoading(true)
    try {
      await api.post("/jobs", { company, role, applied_date: appliedDate })
      setCompany("")
      setRole("")
      setAppliedDate("")
      mutate()
    } finally {
      setLoading(false)
    }
  }

  async function handleStatusChange(id: string, status: string) {
    await api.patch(`/jobs/${id}`, { status })
    mutate()
  }

  async function handleDelete(id: string) {
    await api.delete(`/jobs/${id}`)
    mutate()
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Job Applications</h1>

      {/* Add Form */}
      <div className="bg-white rounded-lg p-5 shadow-sm border mb-6">
        <h2 className="font-medium mb-3">Add Application</h2>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <input
            placeholder="Company *"
            value={company}
            onChange={e => setCompany(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            placeholder="Role *"
            value={role}
            onChange={e => setRole(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          />
          <div className="col-span-2">
            <label className="text-xs text-gray-500 mb-1 block">Applied date *</label>
            <input
              type="date"
              value={appliedDate}
              onChange={e => setAppliedDate(e.target.value)}
              className="border rounded px-3 py-2 text-sm w-full"
            />
          </div>
        </div>
        <button
          onClick={handleAdd}
          disabled={loading}
          className="bg-black text-white px-4 py-2 rounded text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
        >
          {loading ? "Adding..." : "Add Application"}
        </button>
      </div>

      {/* Kanban columns */}
      <div className="grid grid-cols-2 gap-4">
        {STATUSES.map(status => (
          <div key={status} className="bg-white rounded-lg shadow-sm border">
            <div className="p-3 border-b">
              <span className={`text-xs font-medium px-2 py-1 rounded-full ${STATUS_COLORS[status]}`}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </span>
            </div>
            <div className="p-3 space-y-2">
              {!data || data.filter((j: any) => j.status === status).length === 0 ? (
                <p className="text-xs text-gray-400">None</p>
              ) : (
                data.filter((j: any) => j.status === status).map((j: any) => (
                  <div key={j.id} className="border rounded p-3">
                    <p className="font-medium text-sm">{j.company}</p>
                    <p className="text-xs text-gray-500">{j.role}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      Follow up: {j.followup_date ? new Date(j.followup_date).toLocaleDateString() : "—"}
                    </p>
                    <div className="flex gap-2 mt-2">
                      <select
                        value={j.status}
                        onChange={e => handleStatusChange(j.id, e.target.value)}
                        className="text-xs border rounded px-1 py-0.5 flex-1"
                      >
                        {STATUSES.map(s => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                      <button
                        onClick={() => handleDelete(j.id)}
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
        ))}
      </div>
    </div>
  )
}