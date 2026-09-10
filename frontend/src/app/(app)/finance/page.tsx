"use client"
import { useState, useMemo } from "react"
import useSWR from "swr"
import api from "@/lib/api"
import { WalletIcon } from "@/components/icons"
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from "chart.js"
import { Doughnut, Bar } from "react-chartjs-2"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { ListSkeleton } from "@/components/skeletons"
import toast from "react-hot-toast"

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement)

ChartJS.defaults.plugins.tooltip.backgroundColor = "rgb(24, 24, 27)"
ChartJS.defaults.plugins.tooltip.titleColor = "#fafafa"
ChartJS.defaults.plugins.tooltip.bodyColor = "#d4d4d8"
ChartJS.defaults.plugins.tooltip.borderColor = "#27272a"
ChartJS.defaults.plugins.tooltip.borderWidth = 1
ChartJS.defaults.plugins.tooltip.cornerRadius = 6
ChartJS.defaults.plugins.tooltip.padding = 10
ChartJS.defaults.plugins.tooltip.displayColors = true
ChartJS.defaults.plugins.tooltip.boxPadding = 4

const fetcher = (url: string) => api.get(url).then(r => r.data)

const CATEGORIES = ["food", "transport", "study", "fitness", "other"]

const LOCATION_SUGGESTIONS = ["Online", "In-store", "Campus", "Restaurant", "Public Transportation"]

const expenseSchema = z.object({
  amount: z.string().refine((val) => {
    const num = Number(val)
    return !isNaN(num) && num > 0 && num <= 10000
  }, "Must be between $0.01 and $10,000"),
  group: z.string().optional(),
  note: z.string().optional(),
  location: z.string().optional(),
})

type ExpenseForm = z.infer<typeof expenseSchema>

const CATEGORY_COLORS: Record<string, string> = {
  food: "#eab308",
  transport: "#3b82f6",
  study: "#a855f7",
  fitness: "#22c55e",
  other: "#9ca3af",
}

const NEEDS_CATEGORIES = ["food", "transport", "study"]
const WANTS_CATEGORIES = ["fitness", "other"]

const ENVELOPE_CONFIG = [
  { key: "needs", label: "Needs", percent: 50, categories: NEEDS_CATEGORIES, color: "#3b82f6" },
  { key: "wants", label: "Wants", percent: 30, categories: WANTS_CATEGORIES, color: "#a855f7" },
  { key: "savings", label: "Savings", percent: 20, categories: [], color: "#22c55e" },
] as const

const CATEGORY_TO_GROUP: Record<string, string> = {
  food: "needs",
  transport: "needs",
  study: "needs",
  fitness: "wants",
  other: "wants",
}

function getEnvelopeColor(spent: number, limit: number) {
  if (limit <= 0) return "var(--muted)"
  const ratio = spent / limit
  if (ratio >= 0.8) return "var(--danger)"
  if (ratio >= 0.5) return "#eab308"
  return "var(--accent)"
}

const inputClass =
  "border border-[var(--rule)] bg-[var(--surface)] text-[var(--foreground)] placeholder:text-[var(--muted-2)] rounded-md px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:border-[var(--accent)] transition-colors"

export default function FinancePage() {
  const { data: responseData, mutate } = useSWR("/expenses", fetcher)
  const data = responseData?.expenses
  const monthlyBudget = responseData?.monthly_budget ?? 0

  const [tab, setTab] = useState<"envelopes" | "transactions">("envelopes")
  const [expandedEnvelope, setExpandedEnvelope] = useState<string | null>(null)
  const [filterCategory, setFilterCategory] = useState("")
  const [filterDate, setFilterDate] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ExpenseForm>({
    resolver: zodResolver(expenseSchema),
    defaultValues: { amount: undefined, group: "needs", note: "", location: "" },
  })

  async function onSubmit(values: ExpenseForm) {
    await api.post("/expenses", {
      amount: parseFloat(values.amount),
      category: "other",
      group_override: values.group || undefined,
      note: values.note || undefined,
      location: values.location || undefined,
    })
    reset()
    mutate()
    toast.success("Expense added")
  }

  async function handleDelete(id: string) {
    await api.delete(`/expenses/${id}`)
    mutate()
    toast.success("Expense deleted")
  }

  const total = useMemo(() => {
    if (!data) return 0
    const now = new Date()
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
    return data
      .filter((e: any) => new Date(e.spent_at) >= startOfMonth)
      .reduce((sum: number, e: any) => sum + e.amount, 0)
  }, [data])

  // Envelope calculations — only current month, uses group_override
  const envelopeData = useMemo(() => {
    if (!data) return []
    const now = new Date()
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
    const monthExpenses = data.filter((e: any) => new Date(e.spent_at) >= startOfMonth)
    const monthTotal = monthExpenses.reduce((sum: number, e: any) => sum + e.amount, 0)

    return ENVELOPE_CONFIG.map(env => {
      const spent = env.key === "savings"
        ? 0
        : monthExpenses.filter((e: any) => {
            const group = e.group_override || CATEGORY_TO_GROUP[e.category] || "wants"
            return group === env.key
          }).reduce((sum: number, e: any) => sum + e.amount, 0)
      const limit = monthlyBudget * (env.percent / 100)
      const remaining = env.key === "savings"
        ? monthlyBudget - monthTotal
        : limit - spent
      return { ...env, spent, limit, remaining: Math.max(0, remaining) }
    })
  }, [data, monthlyBudget])

  // Filtered expenses for expanded envelope — current month only
  const envelopeExpenses = useMemo(() => {
    if (!expandedEnvelope || !data) return []
    const now = new Date()
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
    const monthExpenses = data.filter((e: any) => new Date(e.spent_at) >= startOfMonth)
    const env = ENVELOPE_CONFIG.find(e => e.key === expandedEnvelope)
    if (!env) return []
    let filtered = monthExpenses.filter((e: any) => {
      const group = e.group_override || CATEGORY_TO_GROUP[e.category] || "wants"
      return group === env.key
    })
    if (filterCategory) {
      filtered = filtered.filter((e: any) => e.category === filterCategory)
    }
    if (filterDate) {
      filtered = filtered.filter((e: any) =>
        new Date(e.spent_at).toISOString().slice(0, 10) === filterDate
      )
    }
    return filtered
  }, [expandedEnvelope, data, filterCategory, filterDate])

  // Transaction search
  const filteredTransactions = useMemo(() => {
    if (!data) return []
    let filtered = [...data]
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      filtered = filtered.filter((e: any) =>
        e.category.toLowerCase().includes(q) ||
        (e.note && e.note.toLowerCase().includes(q)) ||
        (e.location && e.location.toLowerCase().includes(q))
      )
    }
    if (dateFrom) {
      const from = new Date(dateFrom)
      from.setHours(0, 0, 0, 0)
      filtered = filtered.filter((e: any) => new Date(e.spent_at) >= from)
    }
    if (dateTo) {
      const to = new Date(dateTo)
      to.setHours(23, 59, 59, 999)
      filtered = filtered.filter((e: any) => new Date(e.spent_at) <= to)
    }
    return filtered
  }, [data, searchQuery, dateFrom, dateTo])

  // Chart data — current month only
  const categoryTotals = useMemo(() => {
    if (!data) return {}
    const now = new Date()
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
    const monthExpenses = data.filter((e: any) => new Date(e.spent_at) >= startOfMonth)
    const totals: Record<string, number> = {}
    for (const e of monthExpenses) {
      totals[e.category] = (totals[e.category] || 0) + e.amount
    }
    return totals
  }, [data])

  const doughnutData = useMemo(() => {
    const labels = Object.keys(categoryTotals)
    return {
      labels,
      datasets: [{
        data: labels.map(l => categoryTotals[l]),
        backgroundColor: labels.map(l => CATEGORY_COLORS[l] || "#9ca3af"),
        borderWidth: 0,
      }],
    }
  }, [categoryTotals])

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    cutout: "65%",
  }

  const dailyData = useMemo(() => {
    if (!data) return { labels: [], amounts: [] }
    const now = new Date()
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
    const monthExpenses = data.filter((e: any) => new Date(e.spent_at) >= startOfMonth)
    const days: { label: string; amount: number }[] = []
    for (let i = 13; i >= 0; i--) {
      const d = new Date(now)
      d.setDate(d.getDate() - i)
      const key = d.toISOString().slice(0, 10)
      const label = d.toLocaleDateString(undefined, { month: "short", day: "numeric" })
      const amount = monthExpenses
        .filter((e: any) => new Date(e.spent_at).toISOString().slice(0, 10) === key)
        .reduce((sum: number, e: any) => sum + e.amount, 0)
      days.push({ label, amount })
    }
    return { labels: days.map(d => d.label), amounts: days.map(d => d.amount) }
  }, [data])

  const barData = {
    labels: dailyData.labels,
    datasets: [{
      data: dailyData.amounts,
      backgroundColor: "#22c55e",
      borderRadius: 4,
    }],
  }

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { color: "#a1a1aa", font: { size: 10 }, maxRotation: 45 } },
      y: { grid: { color: "#27272a" }, ticks: { color: "#a1a1aa", font: { size: 10 }, callback: (v: any) => `$${v}` } },
    },
  }

  return (
    <div className="max-w-3xl mx-auto px-16 py-16">
      <div className="flex items-center gap-2 mb-6">
        <WalletIcon className="w-6 h-6 text-[var(--accent)]" />
        <h1 className="text-2xl font-bold text-[var(--foreground)]">Finance</h1>
      </div>

      {/* Sub-tabs */}
      <div className="flex gap-1 mb-6 bg-[var(--callout-gray)] rounded-lg p-1">
        {(["envelopes", "transactions"] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors cursor-pointer ${
              tab === t
                ? "bg-[var(--surface)] text-[var(--foreground)] shadow-sm"
                : "text-[var(--muted)] hover:text-[var(--foreground)]"
            }`}
          >
            {t === "envelopes" ? "Envelopes" : "Transactions"}
          </button>
        ))}
      </div>

      {/* Add Form - Envelopes tab only */}
      {tab === "envelopes" && (
        <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-4 shadow-sm mb-4">
        <h2 className="text-sm font-semibold text-[var(--foreground)] mb-3">Add Expense</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-2 gap-2 mb-3">
          <div>
            <input
              type="number"
              step="0.01"
              placeholder="Amount *"
              {...register("amount")}
              className={`${inputClass} w-full ${errors.amount ? "border-[var(--danger)]" : ""}`}
            />
            {errors.amount && (
              <p className="text-xs text-[var(--danger)] mt-1">{errors.amount.message}</p>
            )}
          </div>
          <select {...register("group")} className={`${inputClass} cursor-pointer`}>
            <option value="needs">Need</option>
            <option value="wants">Want</option>
          </select>
          <input
            placeholder="What was this for?"
            {...register("note")}
            className={`${inputClass} col-span-2`}
          />
          <input
            placeholder="Where? (optional)"
            {...register("location")}
            list="location-suggestions"
            className={`${inputClass} col-span-2`}
          />
          <datalist id="location-suggestions">
            {LOCATION_SUGGESTIONS.map(loc => (
              <option key={loc} value={loc} />
            ))}
          </datalist>
          <div className="col-span-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-[var(--accent)] text-white px-4 py-2 rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2"
            >
              {isSubmitting ? "Adding..." : "Add Expense"}
            </button>
          </div>
        </form>
      </div>
      )}

      {/* Demo Data Button */}
      {data && data.length < 3 && (
        <button
          onClick={async () => {
            const demoExpenses = [
              { amount: 45.50, category: "food", note: "Groceries", location: "In-store" },
              { amount: 12.00, category: "food", note: "Lunch", location: "Restaurant" },
              { amount: 25.00, category: "transport", note: "Metro card", location: "Public Transportation" },
              { amount: 85.00, category: "study", note: "Textbook", location: "Online" },
              { amount: 35.00, category: "fitness", note: "Gym membership", location: "In-store" },
              { amount: 15.00, category: "other", note: "Coffee with friends", location: "Restaurant" },
              { amount: 60.00, category: "food", note: "Weekly groceries", location: "In-store" },
              { amount: 20.00, category: "transport", note: "Uber ride", location: "Online" },
              { amount: 50.00, category: "study", note: "Course materials", location: "Campus" },
              { amount: 30.00, category: "fitness", note: "Protein powder", location: "Online" },
            ]
            for (const exp of demoExpenses) {
              await api.post("/expenses", exp)
            }
            mutate()
            toast.success("Demo data loaded!")
          }}
          className="w-full mb-4 px-4 py-2 border border-dashed border-[var(--rule)] rounded-md text-sm text-[var(--muted)] hover:text-[var(--foreground)] hover:border-[var(--accent)] transition-colors cursor-pointer"
        >
          Load demo data to see envelopes in action
        </button>
      )}

      {/* Envelopes Tab */}
      {tab === "envelopes" && (
        <div className="space-y-3 mb-6">
          {monthlyBudget > 0 ? (
            envelopeData.map(env => (
              <div key={env.key} className="bg-[var(--surface)] border border-[var(--rule)] rounded-md shadow-sm overflow-hidden">
                <button
                  onClick={() => setExpandedEnvelope(expandedEnvelope === env.key ? null : env.key)}
                  className="w-full p-4 text-left hover:bg-[var(--surface-hover)] transition-colors cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full" style={{ backgroundColor: env.color }} />
                      <span className="text-sm font-semibold text-[var(--foreground)]">{env.label}</span>
                      <span className="text-xs text-[var(--muted)]">({env.percent}%)</span>
                    </div>
                    <span className="text-sm font-medium text-[var(--foreground)] tabular-nums">
                      ${env.spent.toFixed(2)} / ${env.limit.toFixed(2)}
                    </span>
                  </div>
                  <div className="w-full h-2 bg-[var(--rule)] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-300"
                      style={{
                        width: `${Math.min(100, (env.spent / env.limit) * 100)}%`,
                        backgroundColor: getEnvelopeColor(env.spent, env.limit),
                      }}
                    />
                  </div>
                  <p className="text-xs text-[var(--muted)] mt-1.5">
                    {env.key === "savings"
                      ? `$${env.remaining.toFixed(2)} available to save`
                      : `${Math.round((env.spent / env.limit) * 100)}% used`}
                  </p>
                </button>

                {/* Expanded envelope */}
                {expandedEnvelope === env.key && (
                  <div className="border-t border-[var(--rule)] p-4 bg-[var(--callout-gray)]">
                    <div className="flex gap-2 mb-3">
                      <select
                        value={filterCategory}
                        onChange={e => setFilterCategory(e.target.value)}
                        className="text-xs border border-[var(--rule)] bg-[var(--surface)] rounded px-2 py-1 cursor-pointer"
                      >
                        <option value="">All categories</option>
                        {env.categories.map(c => (
                          <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                        ))}
                      </select>
                      <input
                        type="date"
                        value={filterDate}
                        onChange={e => setFilterDate(e.target.value)}
                        className="text-xs border border-[var(--rule)] bg-[var(--surface)] rounded px-2 py-1"
                      />
                    </div>
                    {envelopeExpenses.length === 0 ? (
                      <p className="text-xs text-[var(--muted-2)] py-2">No expenses in this envelope.</p>
                    ) : (
                      <div className="space-y-1.5">
                        {envelopeExpenses.map((e: any) => (
                          <div key={e.id} className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-[var(--foreground)] tabular-nums">${e.amount.toFixed(2)}</span>
                              <span className="text-xs text-[var(--muted)]">{e.category}</span>
                              {e.note && <span className="text-xs text-[var(--muted-2)] truncate max-w-[120px]">{e.note}</span>}
                            </div>
                            <div className="flex items-center gap-2">
                              {e.location && <span className="text-xs text-[var(--muted-2)]">{e.location}</span>}
                              <span className="text-xs text-[var(--muted-2)]">{new Date(e.spent_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-6 text-center">
              <p className="text-sm text-[var(--muted)]">Set a monthly budget in your profile to see envelopes.</p>
            </div>
          )}
        </div>
      )}

      {/* Transactions Tab */}
      {tab === "transactions" && (
        <div className="mb-6">
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              placeholder="Search transactions..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className={`${inputClass} flex-1 min-w-0`}
            />
            <input
              type="date"
              value={dateFrom}
              onChange={e => setDateFrom(e.target.value)}
              className={`${inputClass} w-[140px] shrink-0`}
              title="From date"
            />
            <input
              type="date"
              value={dateTo}
              onChange={e => setDateTo(e.target.value)}
              className={`${inputClass} w-[140px] shrink-0`}
              title="To date"
            />
          </div>
          <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-md shadow-sm divide-y divide-[var(--rule)] overflow-hidden">
            {!data ? (
              <div className="p-4"><ListSkeleton count={3} /></div>
            ) : filteredTransactions.length === 0 ? (
              <p className="p-4 text-sm text-[var(--muted-2)]">No transactions found.</p>
            ) : (
              filteredTransactions.map((e: any) => (
                <div key={e.id} className="px-4 py-2.5 flex items-center justify-between gap-3 hover:bg-[var(--surface-hover)] transition-colors">
                  <div className="min-w-0">
                    <p className="font-semibold text-sm text-[var(--foreground)] tabular-nums">${e.amount.toFixed(2)}</p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className="text-xs text-[var(--muted)]">{e.category}</span>
                      {e.note && <span className="text-xs text-[var(--muted-2)] truncate">· {e.note}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    {e.location && <span className="text-xs text-[var(--muted-2)]">{e.location}</span>}
                    <span className="text-xs text-[var(--muted-2)]">{new Date(e.spent_at).toLocaleDateString()}</span>
                    <button
                      onClick={() => handleDelete(e.id)}
                      className="text-xs text-[var(--danger)] hover:opacity-80 cursor-pointer transition-opacity"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Charts - Envelopes tab only */}
      {tab === "envelopes" && data && data.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-4 shadow-sm">
            <p className="text-xs font-medium text-[var(--muted)] uppercase tracking-wide mb-3">By Category</p>
            <div className="h-48 relative">
              <Doughnut data={doughnutData} options={doughnutOptions} />
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <p className="text-2xl font-bold text-[var(--foreground)] tabular-nums">${total.toFixed(2)}</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-3 mt-3">
              {Object.entries(categoryTotals).map(([cat, amt]) => (
                <div key={cat} className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[cat] || "#9ca3af" }} />
                  <span className="text-xs text-[var(--muted)]">{cat} · ${(amt as number).toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-4 shadow-sm">
            <p className="text-xs font-medium text-[var(--muted)] uppercase tracking-wide mb-3">Daily Spending (14 days)</p>
            <div className="h-56">
              <Bar data={barData} options={barOptions} />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
