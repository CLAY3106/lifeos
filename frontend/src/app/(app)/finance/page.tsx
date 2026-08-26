"use client"
import { useState } from "react"
import useSWR from "swr"
import api from "@/lib/api"
import { WalletIcon } from "@/components/icons"

const fetcher = (url: string) => api.get(url).then(r => r.data)

const CATEGORIES = ["food", "transport", "study", "fitness", "other"]

type CalloutTone = "gray" | "green" | "yellow" | "red" | "blue" | "purple"

const CATEGORY_TONE: Record<string, CalloutTone> = {
  food: "yellow",
  transport: "blue",
  study: "purple",
  fitness: "green",
  other: "gray",
}

const toneBg: Record<CalloutTone, string> = {
  gray: "bg-[var(--callout-gray)]",
  green: "bg-[var(--callout-green)]",
  yellow: "bg-[var(--callout-yellow)]",
  red: "bg-[var(--callout-red)]",
  blue: "bg-[var(--callout-blue)]",
  purple: "bg-[var(--callout-purple)]",
}

const inputClass =
  "border border-[var(--rule)] bg-[var(--surface)] text-[var(--foreground)] placeholder:text-[var(--muted-2)] rounded-md px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:border-[var(--accent)] transition-colors"

export default function FinancePage() {
  const { data, mutate } = useSWR("/expenses", fetcher)
  const [amount, setAmount] = useState("")
  const [category, setCategory] = useState("food")
  const [note, setNote] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleAdd() {
    if (!amount) return
    setLoading(true)
    try {
      await api.post("/expenses", {
        amount: parseFloat(amount),
        category,
        note,
      })
      setAmount("")
      setNote("")
      setCategory("food")
      mutate()
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: string) {
    await api.delete(`/expenses/${id}`)
    mutate()
  }

  const total = data?.reduce((sum: number, e: any) => sum + e.amount, 0) ?? 0

  return (
    <div className="max-w-3xl mx-auto px-16 py-16">
      <div className="flex items-center gap-2 mb-6">
        <WalletIcon className="w-6 h-6 text-[var(--accent)]" />
        <h1 className="text-2xl font-bold text-[var(--foreground)]">Finance</h1>
      </div>

      {/* Add Form */}
      <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-4 shadow-sm mb-4">
        <h2 className="text-sm font-semibold text-[var(--foreground)] mb-3">Add Expense</h2>
        <div className="grid grid-cols-2 gap-2 mb-3">
          <input
            type="number"
            placeholder="Amount *"
            value={amount}
            onChange={e => setAmount(e.target.value)}
            className={inputClass}
          />
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            className={`${inputClass} cursor-pointer`}
          >
            {CATEGORIES.map(c => (
              <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
            ))}
          </select>
          <input
            placeholder="Note (optional)"
            value={note}
            onChange={e => setNote(e.target.value)}
            className={`${inputClass} col-span-2`}
          />
        </div>
        <button
          onClick={handleAdd}
          disabled={loading}
          className="bg-[var(--accent)] text-white px-4 py-2 rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2"
        >
          {loading ? "Adding..." : "Add Expense"}
        </button>
      </div>

      {/* Total */}
      <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-4 shadow-sm mb-4">
        <p className="text-xs font-medium text-[var(--muted)] uppercase tracking-wide">
          Total spent this month
        </p>
        <p className="text-3xl font-bold text-[var(--foreground)] tabular-nums mt-0.5">
          ${total.toFixed(2)}
        </p>
      </div>

      {/* Expense List */}
      <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-md shadow-sm divide-y divide-[var(--rule)] overflow-hidden">
        {!data || data.length === 0 ? (
          <p className="p-4 text-sm text-[var(--muted-2)]">No expenses yet. Add one above.</p>
        ) : (
          data.map((e: any) => (
            <div
              key={e.id}
              className="px-4 py-2.5 flex items-center justify-between gap-3 hover:bg-[var(--surface-hover)] transition-colors"
            >
              <div className="min-w-0">
                <p className="font-semibold text-sm text-[var(--foreground)] tabular-nums">
                  ${e.amount.toFixed(2)}
                </p>
                <div className="flex items-center gap-1.5 mt-1">
                  <span
                    className={`inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-medium text-[var(--foreground)] ${
                      toneBg[CATEGORY_TONE[e.category] ?? "gray"]
                    }`}
                  >
                    {e.category}
                  </span>
                  <span className="text-xs text-[var(--muted-2)] truncate">
                    {e.note && `${e.note} · `}
                    {new Date(e.spent_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <button
                onClick={() => handleDelete(e.id)}
                className="shrink-0 text-xs text-[var(--danger)] hover:opacity-80 cursor-pointer transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] rounded"
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
