"use client"
import { useState } from "react"
import useSWR from "swr"
import api from "@/lib/api"
import {
  LeafIcon,
  LightbulbIcon,
  CalendarIcon,
  CheckCircleIcon,
  ClockIcon,
  BriefcaseIcon,
  ActivityIcon,
  WalletIcon,
  RefreshIcon,
} from "@/components/icons"
import { Callout, StatCallout, SectionHeading, Tag, EmptyRow } from "@/components/primitives"
import toast from "react-hot-toast"
import { DashboardSkeleton } from "@/components/skeletons"

const fetcher = (url: string) => api.get(url).then(r => r.data)

function greeting() {
  const h = new Date().getHours()
  if (h < 12) return "Good morning"
  if (h < 18) return "Good afternoon"
  return "Good evening"
}

function longDate() {
  return new Date().toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  })
}

function ProgressRing({ complete }: { complete: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 18 18" className="shrink-0">
      <circle cx="9" cy="9" r="7" fill="none" stroke="var(--rule)" strokeWidth="2" />
      {complete ? (
        <circle cx="9" cy="9" r="7" fill="var(--accent)" stroke="var(--accent)" strokeWidth="2" />
      ) : (
        <circle
          cx="9" cy="9" r="7" fill="none" stroke="var(--accent)" strokeWidth="2"
          strokeDasharray="44" strokeDashoffset="11"
        />
      )}
    </svg>
  )
}

export default function DashboardPage() {
  const [showFullBriefing, setShowFullBriefing] = useState(false)
  const { data, isLoading } = useSWR("/dashboard", fetcher, {
    refreshInterval: 30000,
  })

  const { data: aiData, mutate: refreshAI, isValidating: aiLoading } = useSWR(
    "/ai/briefing",
    () => api.post("/ai/briefing").then(r => r.data)
  )

  if (isLoading) {
    return <DashboardSkeleton />
  }
  if (!data) {
    return (
      <div className="max-w-5xl mx-auto px-16 py-16">
        <div className="bg-[var(--callout-red)] rounded-md p-4 flex gap-3">
          <p className="text-sm text-[var(--foreground)]">Failed to load dashboard data. Please try again.</p>
        </div>
      </div>
    )
  }

  const loadPercent = data.assignments.load_percent
  const budgetPercent = data.finance.budget_percent
  const daysSinceWorkout = data.fitness.days_since_workout

  return (
    <div className="max-w-5xl mx-auto px-16">
      {/* Notion-style cover strip */}
      <div className="h-28 bg-gradient-to-r from-[var(--callout-green)] via-[var(--callout-blue)] to-[var(--callout-purple)]" />

      <div className="-mt-8">
        {/* Page icon badge */}
        <div className="w-11 h-11 rounded-full bg-[var(--callout-green)] text-[var(--accent)] flex items-center justify-center mb-3">
          <LeafIcon className="w-5 h-5" />
        </div>

        {/* Page title */}
        <h1 className="text-4xl font-bold tracking-tight text-[var(--foreground)] mb-1">
          {greeting()}, {data.user.name}
        </h1>
        <p className="text-sm text-[var(--muted)] mb-8">{longDate()}</p>

        {/* AI Briefing callout */}
        <Callout tone="green" icon={LightbulbIcon} className="mb-8">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-medium text-[var(--muted)] uppercase tracking-wide">
                AI Briefing
              </p>
              <button
                onClick={() => api.post("/ai/refresh").then(() => refreshAI())}
                className="inline-flex items-center gap-1 text-xs text-[var(--muted)] hover:text-[var(--foreground)] transition-colors cursor-pointer rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-1"
              >
                <RefreshIcon className="w-3.5 h-3.5" />
                Refresh
              </button>
            </div>
            {aiLoading ? (
              <p className="text-sm text-[var(--muted)] italic">Generating your brief…</p>
            ) : aiData && aiData.priorities?.length > 0 ? (
              <div>
                <div className="space-y-2.5 mb-3">
                  {aiData.priorities.map((p: any, i: number) => (
                    <div key={i} className="flex items-start gap-3">
                      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[var(--accent)] text-white text-xs font-bold shrink-0 mt-0.5">
                        {i + 1}
                      </span>
                      <div>
                        <p className="text-sm font-medium text-[var(--foreground)]">{p.title}</p>
                        <p className="text-xs text-[var(--muted)]">{p.reason}</p>
                      </div>
                    </div>
                  ))}
                </div>
                {aiData.summary && (
                  <button
                    onClick={() => setShowFullBriefing(!showFullBriefing)}
                    className="text-xs text-[var(--muted)] hover:text-[var(--foreground)] transition-colors cursor-pointer"
                  >
                    {showFullBriefing ? "Hide summary" : "Show summary"}
                  </button>
                )}
                {showFullBriefing && aiData.summary && (
                  <p className="text-[15px] leading-relaxed text-[var(--foreground)] mt-2">
                    {aiData.summary}
                  </p>
                )}
              </div>
            ) : aiData?.summary ? (
              <p className="text-[15px] leading-relaxed text-[var(--foreground)]">
                {aiData.summary}
              </p>
            ) : (
              <p className="text-sm text-[var(--muted)] italic">No brief yet.</p>
            )}
          </div>
        </Callout>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8">
          {/* LEFT — database-style upcoming */}
          <section>
            <SectionHeading icon={CalendarIcon} title="This week" count={data.assignments.upcoming.length} />
            {data.assignments.upcoming.length === 0 ? (
              <EmptyRow icon={CheckCircleIcon} text="Nothing due this week." />
            ) : (
              <div className="border border-[var(--rule)] rounded-md overflow-hidden">
                <div className="grid grid-cols-[24px_1fr_120px_100px_100px] gap-3 px-3 py-2 bg-[var(--callout-gray)] text-[11px] font-medium text-[var(--muted)] uppercase tracking-wide">
                  <span></span>
                  <span>Assignment</span>
                  <span>Course</span>
                  <span>Est. hrs</span>
                  <span className="text-right">Due</span>
                </div>
                {data.assignments.upcoming.map((a: any, i: number) => {
                  const days = Math.ceil(
                    (new Date(a.due_date).getTime() - Date.now()) / 86400000
                  )
                  const urgent = days <= 2
                  const dueLabel =
                    days < 0
                      ? "Overdue"
                      : days === 0
                      ? "Today"
                      : days === 1
                      ? "Tomorrow"
                      : `${days}d`
                  return (
                    <div
                      key={a.id}
                      className={`grid grid-cols-[24px_1fr_120px_100px_100px] gap-3 px-3 py-2.5 items-center text-sm hover:bg-[var(--surface-hover)] transition-colors ${
                        i < data.assignments.upcoming.length - 1
                          ? "border-b border-[var(--rule)]"
                          : ""
                      }`}
                    >
                      <ProgressRing complete={a.status === "done"} />
                      <span className="text-[var(--foreground)] truncate">{a.title}</span>
                      <Tag>{a.course || "—"}</Tag>
                      <span className="text-[var(--muted)]">
                        {a.estimated_hours ? `${a.estimated_hours}h` : "—"}
                      </span>
                      <span
                        className={`text-right text-xs font-medium ${
                          urgent ? "text-[var(--danger)]" : "text-[var(--muted)]"
                        }`}
                      >
                        {dueLabel}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </section>

          {/* RIGHT — callout stats */}
          <aside className="space-y-3">
            <p className="text-[11px] font-medium text-[var(--muted-2)] uppercase tracking-wide mb-2">
              At a glance
            </p>

            <StatCallout
              icon={ClockIcon}
              tone="blue"
              label="Weekly load"
              value={`${data.assignments.weekly_load_hours}h`}
              context={`of ${data.assignments.weekly_capacity_hours}h`}
              meter={loadPercent}
              alert={loadPercent >= 80}
            />
            <StatCallout
              icon={BriefcaseIcon}
              tone={data.jobs.overdue_followups > 0 ? "red" : "gray"}
              label="Job follow-ups"
              value={data.jobs.overdue_followups}
              context={data.jobs.overdue_followups === 1 ? "overdue" : "overdue"}
              alert={data.jobs.overdue_followups > 0}
            />
            <StatCallout
              icon={ActivityIcon}
              tone={daysSinceWorkout != null && daysSinceWorkout >= 3 ? "yellow" : "green"}
              label="Last workout"
              value={daysSinceWorkout ?? "—"}
              context={
                daysSinceWorkout == null
                  ? "no sessions"
                  : daysSinceWorkout === 1
                  ? "day ago"
                  : "days ago"
              }
              alert={daysSinceWorkout != null && daysSinceWorkout >= 5}
            />
            <StatCallout
              icon={WalletIcon}
              tone={budgetPercent >= 100 ? "red" : budgetPercent >= 80 ? "yellow" : "purple"}
              label="Spent this month"
              value={`$${data.finance.total_spent.toFixed(0)}`}
              context={`of $${data.finance.monthly_budget} budget`}
              meter={budgetPercent}
              alert={budgetPercent >= 100}
            />
          </aside>
        </div>

        <div className="h-16" />
      </div>
    </div>
  )
}
