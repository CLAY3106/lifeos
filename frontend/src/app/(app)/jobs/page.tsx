"use client"
import { useState } from "react"
import useSWR from "swr"
import api from "@/lib/api"
import { CalendarIcon, PlusIcon, TrashIcon } from "@/components/icons"

const fetcher = (url: string) => api.get(url).then(r => r.data)

const STATUS_COLORS: Record<string, string> = {
  applied: "bg-[var(--callout-blue)] text-[var(--callout-blue-text)]",
  interview: "bg-[var(--callout-yellow)] text-[var(--callout-yellow-text)]",
  offer: "bg-[var(--callout-green)] text-[var(--callout-green-text)]",
  rejected: "bg-[var(--callout-red)] text-[var(--callout-red-text)]",
}

const STATUSES = ["applied", "interview", "offer", "rejected"]

const inputClass =
  "border border-[var(--rule)] rounded-md px-3 py-2 text-sm bg-[var(--surface)] text-[var(--foreground)] placeholder:text-[var(--muted-2)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-colors"

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
    <div className="max-w-5xl mx-auto px-16 py-16">
      <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)] mb-1">
        Job Applications
      </h1>
      <p className="text-sm text-[var(--muted)] mb-8">
        {data ? `${data.length} application${data.length === 1 ? "" : "s"} tracked` : "Loading…"}
      </p>

      {/* Add Form */}
      <div className="bg-[var(--surface)] rounded-lg p-5 shadow-sm border border-[var(--rule)] mb-8">
        <h2 className="text-sm font-semibold text-[var(--foreground)] mb-3">Add Application</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
          <input
            placeholder="Company *"
            value={company}
            onChange={e => setCompany(e.target.value)}
            className={inputClass}
          />
          <input
            placeholder="Role *"
            value={role}
            onChange={e => setRole(e.target.value)}
            className={inputClass}
          />
          <div className="sm:col-span-2">
            <label className="text-xs text-[var(--muted)] mb-1 block">Applied date *</label>
            <input
              type="date"
              value={appliedDate}
              onChange={e => setAppliedDate(e.target.value)}
              className={`${inputClass} w-full`}
            />
          </div>
        </div>
        <button
          onClick={handleAdd}
          disabled={loading}
          className="inline-flex items-center gap-1.5 bg-[var(--accent)] text-black px-4 py-2 rounded-md text-sm font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-opacity focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--surface)]"
        >
          <PlusIcon className="w-4 h-4" />
          {loading ? "Adding…" : "Add Application"}
        </button>
      </div>

      {/* Kanban columns */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STATUSES.map(status => {
          const jobs = data ? data.filter((j: any) => j.status === status) : []
          return (
            <div
              key={status}
              className="bg-[var(--surface)] rounded-lg border border-[var(--rule)] flex flex-col"
            >
              <div className="p-3 border-b border-[var(--rule)] bg-[var(--callout-gray)] rounded-t-lg flex items-center justify-between">
                <span
                  className={`text-xs font-semibold px-2 py-1 rounded-full ${STATUS_COLORS[status]}`}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </span>
                <span className="text-xs font-medium text-[var(--muted-2)] tabular-nums">
                  {jobs.length}
                </span>
              </div>
              <div className="p-3 space-y-2 flex-1">
                {!data ? (
                  <p className="text-xs text-[var(--muted-2)] py-4 text-center">Loading…</p>
                ) : jobs.length === 0 ? (
                  <p className="text-xs text-[var(--muted-2)] py-4 text-center">None</p>
                ) : (
                  jobs.map((j: any) => (
                    <div
                      key={j.id}
                      className="border border-[var(--rule)] rounded-md p-3 bg-[var(--surface)] hover:bg-[var(--surface-hover)] transition-colors"
                    >
                      <p className="font-semibold text-sm text-[var(--foreground)]">{j.company}</p>
                      <p className="text-xs text-[var(--muted)] mt-0.5">{j.role}</p>
                      <p className="text-xs text-[var(--muted-2)] mt-1.5 flex items-center gap-1">
                        <CalendarIcon className="w-3 h-3 shrink-0" />
                        {j.followup_date
                          ? new Date(j.followup_date).toLocaleDateString()
                          : "No follow-up set"}
                      </p>
                      <div className="flex items-center gap-2 mt-2.5">
                        <select
                          value={j.status}
                          onChange={e => handleStatusChange(j.id, e.target.value)}
                          className="text-xs border border-[var(--rule)] rounded-md px-1.5 py-1 flex-1 bg-[var(--surface)] text-[var(--foreground)] cursor-pointer focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition-colors"
                        >
                          {STATUSES.map(s => (
                            <option key={s} value={s}>
                              {s.charAt(0).toUpperCase() + s.slice(1)}
                            </option>
                          ))}
                        </select>
                        <button
                          onClick={() => handleDelete(j.id)}
                          aria-label={`Delete application to ${j.company}`}
                          className="p-1.5 rounded-md text-[var(--muted-2)] hover:text-[var(--danger)] hover:bg-[var(--callout-red)] cursor-pointer transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--danger)]"
                        >
                          <TrashIcon className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
