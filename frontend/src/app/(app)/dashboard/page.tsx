"use client"
import useSWR from "swr"
import api from "@/lib/api"

const fetcher = (url: string) => api.get(url).then(r => r.data)

export default function DashboardPage() {
  const { data, isLoading } = useSWR("/dashboard", fetcher, {
    refreshInterval: 30000
  })

  const { data: aiData, mutate: refreshAI } = useSWR("/ai/briefing", 
  () => api.post("/ai/briefing").then(r => r.data)
  )

  if (isLoading) return <div className="text-gray-400">Loading...</div>
  if (!data) return <div className="text-gray-400">No data</div>

  const loadPercent = data.assignments.load_percent
  const budgetPercent = data.finance.budget_percent

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Good morning, {data.user.name} 👋</h1>
      <p className="text-gray-500 mb-8">Here's your day at a glance.</p>

      {/* AI Briefing */}
<div className="bg-black text-white rounded-lg p-5 mb-8">
  <div className="flex justify-between items-start">
    <h2 className="text-sm font-medium text-gray-400 mb-2">AI Briefing</h2>
    <button
      onClick={() => {
        api.post("/ai/refresh").then(() => refreshAI())
      }}
      className="text-xs text-gray-400 hover:text-white"
    >
      Refresh
    </button>
  </div>
  {aiData ? (
    <p className="text-sm leading-relaxed">{aiData.content}</p>
  ) : (
    <p className="text-sm text-gray-500">Generating your briefing...</p>
  )}
</div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 mb-8">

        {/* Assignments */}
        <div className="bg-white rounded-lg p-5 shadow-sm border">
          <h2 className="text-sm font-medium text-gray-500 mb-1">Assignments</h2>
          <p className="text-2xl font-bold">{data.assignments.upcoming.length}</p>
          <p className="text-sm text-gray-500">due this week</p>
          <div className="mt-3">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Weekly load</span>
              <span>{data.assignments.weekly_load_hours}h / {data.assignments.weekly_capacity_hours}h</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${loadPercent >= 80 ? "bg-red-500" : "bg-black"}`}
                style={{ width: `${Math.min(loadPercent, 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Jobs */}
        <div className="bg-white rounded-lg p-5 shadow-sm border">
          <h2 className="text-sm font-medium text-gray-500 mb-1">Jobs</h2>
          <p className="text-2xl font-bold">{data.jobs.overdue_followups}</p>
          <p className="text-sm text-gray-500">overdue follow-ups</p>
        </div>

        {/* Fitness */}
        <div className="bg-white rounded-lg p-5 shadow-sm border">
          <h2 className="text-sm font-medium text-gray-500 mb-1">Fitness</h2>
          <p className="text-2xl font-bold">
            {data.fitness.days_since_workout ?? "—"}
          </p>
          <p className="text-sm text-gray-500">days since last workout</p>
        </div>

        {/* Finance */}
        <div className="bg-white rounded-lg p-5 shadow-sm border">
          <h2 className="text-sm font-medium text-gray-500 mb-1">Finance</h2>
          <p className="text-2xl font-bold">${data.finance.total_spent.toFixed(2)}</p>
          <p className="text-sm text-gray-500">of ${data.finance.monthly_budget} budget</p>
          <div className="mt-3">
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${budgetPercent >= 100 ? "bg-red-500" : budgetPercent >= 80 ? "bg-amber-400" : "bg-black"}`}
                style={{ width: `${Math.min(budgetPercent, 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Upcoming Assignments */}
      <div className="bg-white rounded-lg p-5 shadow-sm border">
        <h2 className="font-medium mb-3">Upcoming Assignments</h2>
        {data.assignments.upcoming.length === 0 ? (
          <p className="text-sm text-gray-400">No assignments due this week 🎉</p>
        ) : (
          <ul className="divide-y">
            {data.assignments.upcoming.map((a: any) => (
              <li key={a.id} className="py-2 flex justify-between text-sm">
                <span>{a.title} {a.course && <span className="text-gray-400">— {a.course}</span>}</span>
                <span className="text-gray-500">{new Date(a.due_date).toLocaleDateString()}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}