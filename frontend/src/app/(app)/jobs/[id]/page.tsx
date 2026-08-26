"use client"
import { useParams } from "next/navigation"
import Link from "next/link"
import useSWR from "swr"
import api from "@/lib/api"
import { BriefcaseIcon, CalendarIcon } from "@/components/icons"

const fetcher = (url: string) => api.get(url).then(r => r.data)

const STATUS_COLORS: Record<string, string> = {
  applied: "bg-[var(--callout-blue)] text-[var(--callout-blue-text)]",
  oa: "bg-[var(--callout-purple)] text-[var(--foreground)]",
  interview_scheduled: "bg-[var(--callout-yellow)] text-[var(--callout-yellow-text)]",
  offer: "bg-[var(--callout-green)] text-[var(--callout-green-text)]",
  rejected: "bg-[var(--callout-red)] text-[var(--callout-red-text)]",
  dropped: "bg-[var(--callout-gray)] text-[var(--muted)]",
}

const STATUS_LABELS: Record<string, string> = {
  applied: "Applied",
  oa: "OA",
  interview_scheduled: "Interview",
  offer: "Offer",
  rejected: "Rejected",
  dropped: "Dropped",
}

const STATUSES = ["applied", "oa", "interview_scheduled", "offer", "rejected", "dropped"]

const inputClass =
  "border border-[var(--rule)] rounded-md px-3 py-2 text-sm bg-[var(--surface)] text-[var(--foreground)] placeholder:text-[var(--muted-2)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-colors"

export default function JobDetailPage() {
  const params = useParams()
  const id = params?.id as string | undefined

  const { data, error, mutate } = useSWR(id ? `/jobs/${id}` : null, fetcher)

  async function handleStatusChange(status: string) {
    await api.patch(`/jobs/${id}`, { status })
    mutate()
  }

  async function handleFieldChange(field: string, value: string) {
    await api.patch(`/jobs/${id}`, { [field]: value || null })
    mutate()
  }

  if (error?.response?.status === 404) {
    return (
      <div className="max-w-3xl mx-auto px-16 py-16">
        <p className="text-sm text-[var(--foreground)] mb-2">Application not found.</p>
        <Link href="/jobs" className="text-sm text-[var(--accent)] hover:underline">
          Back to Jobs
        </Link>
      </div>
    )
  }

  if (!data && !error) {
    return (
      <div className="max-w-3xl mx-auto px-16 py-16">
        <p className="text-sm text-[var(--muted)]">Loading…</p>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="max-w-3xl mx-auto px-16 py-16">
        <p className="text-sm text-[var(--muted)]">Something went wrong.</p>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-16 py-16">
      <Link href="/jobs" className="text-xs text-[var(--muted)] hover:text-[var(--foreground)] transition-colors">
        ← Back to Jobs
      </Link>

      <div className="flex items-center gap-2.5 mt-3 mb-1">
        <BriefcaseIcon className="w-6 h-6 text-[var(--accent)]" />
        <h1 className="text-2xl font-semibold tracking-tight text-[var(--foreground)]">
          {data.company}
        </h1>
      </div>
      <p className="text-sm text-[var(--muted)] mb-6">{data.role}</p>

      <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-xl p-6 shadow-sm mb-6">
        <div className="grid grid-cols-2 gap-5">
          <div>
            <label className="text-xs text-[var(--muted-2)] uppercase tracking-wide block mb-1.5">
              Status
            </label>
            <select
              value={data.status}
              onChange={e => handleStatusChange(e.target.value)}
              className={`${inputClass} w-full`}
            >
              {STATUSES.map(s => (
                <option key={s} value={s}>
                  {STATUS_LABELS[s]}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-[var(--muted-2)] uppercase tracking-wide block mb-1.5">
              Follow-up date
            </label>
            <input
              key={`followup-${data.followup_date}`}
              type="date"
              defaultValue={data.followup_date || ""}
              onBlur={e => handleFieldChange("followup_date", e.target.value)}
              className={`${inputClass} w-full`}
            />
          </div>
          <div>
            <label className="text-xs text-[var(--muted-2)] uppercase tracking-wide block mb-1.5">
              Applied
            </label>
            <p className="text-sm text-[var(--foreground)] flex items-center gap-1.5">
              <CalendarIcon className="w-3.5 h-3.5 text-[var(--muted-2)]" />
              {new Date(data.applied_date).toLocaleDateString()}
            </p>
          </div>
          <div>
            <label className="text-xs text-[var(--muted-2)] uppercase tracking-wide block mb-1.5">
              Deadline
            </label>
            <input
              key={`deadline-${data.deadline}`}
              type="date"
              defaultValue={data.deadline || ""}
              onBlur={e => handleFieldChange("deadline", e.target.value)}
              className={`${inputClass} w-full`}
            />
          </div>
          <div>
            <label className="text-xs text-[var(--muted-2)] uppercase tracking-wide block mb-1.5">
              Location
            </label>
            <input
              key={`location-${data.location}`}
              type="text"
              placeholder="e.g. Remote, Seattle WA"
              defaultValue={data.location || ""}
              onBlur={e => handleFieldChange("location", e.target.value)}
              className={`${inputClass} w-full`}
            />
          </div>
          <div className="col-span-2">
            <label className="text-xs text-[var(--muted-2)] uppercase tracking-wide block mb-1.5">
              Application link
            </label>
            <input
              key={`application_url-${data.application_url}`}
              type="url"
              placeholder="https://..."
              defaultValue={data.application_url || ""}
              onBlur={e => handleFieldChange("application_url", e.target.value)}
              className={`${inputClass} w-full`}
            />
            {data.application_url && (
              <a
                href={data.application_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-[var(--accent)] hover:underline mt-1.5 inline-block"
              >
                Open link ↗
              </a>
            )}
          </div>
        </div>
      </div>

      <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-xl p-6 shadow-sm mb-6">
        <label className="text-xs text-[var(--muted-2)] uppercase tracking-wide block mb-1.5">
          Job description
        </label>
        <textarea
          key={`job_description-${data.job_description}`}
          rows={6}
          placeholder="Paste the job description here…"
          defaultValue={data.job_description || ""}
          onBlur={e => handleFieldChange("job_description", e.target.value)}
          className={`${inputClass} w-full resize-y`}
        />
      </div>

      <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-xl p-6 shadow-sm">
        <label className="text-xs text-[var(--muted-2)] uppercase tracking-wide block mb-1.5">
          Notes
        </label>
        <textarea
          key={`notes-${data.notes}`}
          rows={4}
          placeholder="Interview prep, contacts, anything to remember…"
          defaultValue={data.notes || ""}
          onBlur={e => handleFieldChange("notes", e.target.value)}
          className={`${inputClass} w-full resize-y`}
        />
      </div>
    </div>
  )
}
