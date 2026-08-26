"use client"
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

type IconType = React.ComponentType<{ className?: string }>

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

type CalloutTone = "gray" | "green" | "yellow" | "red" | "blue" | "purple"

const toneBg: Record<CalloutTone, string> = {
  gray: "bg-[var(--callout-gray)]",
  green: "bg-[var(--callout-green)]",
  yellow: "bg-[var(--callout-yellow)]",
  red: "bg-[var(--callout-red)]",
  blue: "bg-[var(--callout-blue)]",
  purple: "bg-[var(--callout-purple)]",
}

export default function DashboardPage() {
  const { data, isLoading } = useSWR("/dashboard", fetcher, {
    refreshInterval: 30000,
  })

  const { data: aiData, error: aiError, mutate: refreshAI, isValidating: aiLoading } = useSWR(
    "/ai/briefing",
    () => api.post("/ai/briefing").then(r => r.data)
  )

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-16 py-16">
        <p className="text-sm text-[var(--muted)]">Loading…</p>
      </div>
    )
  }
  if (!data) {
    return (
      <div className="max-w-5xl mx-auto px-16 py-16">
        <p className="text-sm text-[var(--muted)]">No data.</p>
      </div>
    )
  }

  const loadPercent = data.assignments.load_percent
  const budgetPercent = data.finance.budget_percent
  const daysSinceWorkout = data.fitness.days_since_workout

  const rateLimited =
    aiError?.response?.status === 429 ||
    (typeof aiError?.message === "string" && aiError.message.includes("429"))

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
            {rateLimited ? (
              <p className="text-sm text-[var(--muted)] italic">
                Daily AI limit reached (10/day). Resets tomorrow.
              </p>
            ) : aiData ? (
              <p className="text-[15px] leading-relaxed text-[var(--foreground)]">
                {aiData.content}
              </p>
            ) : (
              <p className="text-sm text-[var(--muted)] italic">
                {aiLoading ? "Generating your brief…" : "No brief yet."}
              </p>
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
                <div className="grid grid-cols-[1fr_120px_100px_100px] gap-4 px-3 py-2 bg-[var(--callout-gray)] text-[11px] font-medium text-[var(--muted)] uppercase tracking-wide">
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
                    days <= 0
                      ? "Today"
                      : days === 1
                      ? "Tomorrow"
                      : `${days}d`
                  return (
                    <div
                      key={a.id}
                      className={`grid grid-cols-[1fr_120px_100px_100px] gap-4 px-3 py-2.5 items-center text-sm hover:bg-[var(--surface-hover)] transition-colors ${
                        i < data.assignments.upcoming.length - 1
                          ? "border-b border-[var(--rule)]"
                          : ""
                      }`}
                    >
                      <span className="text-[var(--foreground)]">{a.title}</span>
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

function Callout({
  tone,
  icon: Icon,
  children,
  className = "",
}: {
  tone: CalloutTone
  icon: IconType
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`${toneBg[tone]} rounded-md p-4 flex gap-3 ${className}`}>
      <Icon className="w-5 h-5 shrink-0 mt-0.5 text-[var(--accent)]" />
      {children}
    </div>
  )
}

function StatCallout({
  icon: Icon,
  tone,
  label,
  value,
  context,
  meter,
  alert,
}: {
  icon: IconType
  tone: CalloutTone
  label: string
  value: string | number
  context: string
  meter?: number
  alert?: boolean
}) {
  return (
    <div className={`${toneBg[tone]} rounded-md p-3.5`}>
      <div className="flex items-start gap-2.5">
        <Icon
          className={`w-[18px] h-[18px] shrink-0 mt-0.5 ${
            alert ? "text-[var(--danger)]" : "text-[var(--muted)]"
          }`}
        />
        <div className="flex-1 min-w-0">
          <p className="text-[11px] font-medium text-[var(--muted)] uppercase tracking-wide">
            {label}
          </p>
          <div className="flex items-baseline gap-1.5 mt-0.5">
            <span
              className={`text-2xl font-semibold tabular-nums ${
                alert ? "text-[var(--danger)]" : "text-[var(--foreground)]"
              }`}
            >
              {value}
            </span>
            <span className="text-xs text-[var(--muted)]">{context}</span>
          </div>
          {meter !== undefined && (
            <div className="mt-2 h-1 w-full bg-[var(--rule)] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-[width] duration-300 ${
                  alert ? "bg-[var(--danger)]" : "bg-[var(--accent)]"
                }`}
                style={{ width: `${Math.min(meter, 100)}%` }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function SectionHeading({
  icon: Icon,
  title,
  count,
}: {
  icon: IconType
  title: string
  count?: number
}) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <Icon className="w-4 h-4 text-[var(--muted)]" />
      <h2 className="text-base font-semibold text-[var(--foreground)]">{title}</h2>
      {count !== undefined && (
        <span className="text-xs text-[var(--muted-2)]">· {count}</span>
      )}
    </div>
  )
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-[var(--callout-gray)] text-[var(--foreground)] w-fit">
      {children}
    </span>
  )
}

function EmptyRow({ icon: Icon, text }: { icon: IconType; text: string }) {
  return (
    <div className="border border-dashed border-[var(--rule)] rounded-md py-8 text-center">
      <Icon className="w-7 h-7 mx-auto mb-2 text-[var(--muted-2)]" />
      <p className="text-sm text-[var(--muted)]">{text}</p>
    </div>
  )
}
