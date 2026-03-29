"use client"
import { useState } from "react"
import useSWR from "swr"
import api from "@/lib/api"

const fetcher = (url: string) => api.get(url).then(r => r.data)

const CATEGORIES = ["food", "transport", "study", "fitness", "other"]

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
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Finance</h1>

      {/* Add Form */}
      <div className="bg-white rounded-lg p-5 shadow-sm border mb-6">
        <h2 className="font-medium mb-3">Add Expense</h2>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <input
            type="number"
            placeholder="Amount *"
            value={amount}
            onChange={e => setAmount(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          />
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          >
            {CATEGORIES.map(c => (
              <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
            ))}
          </select>
          <input
            placeholder="Note (optional)"
            value={note}
            onChange={e => setNote(e.target.value)}
            className="border rounded px-3 py-2 text-sm col-span-2"
          />
        </div>
        <button
          onClick={handleAdd}
          disabled={loading}
          className="bg-black text-white px-4 py-2 rounded text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
        >
          {loading ? "Adding..." : "Add Expense"}
        </button>
      </div>

      {/* Total */}
      <div className="bg-white rounded-lg p-5 shadow-sm border mb-6">
        <p className="text-sm text-gray-500">Total spent this month</p>
        <p className="text-3xl font-bold">${total.toFixed(2)}</p>
      </div>

      {/* Expense List */}
      <div className="bg-white rounded-lg shadow-sm border divide-y">
        {!data || data.length === 0 ? (
          <p className="p-5 text-sm text-gray-400">No expenses yet. Add one above.</p>
        ) : (
          data.map((e: any) => (
            <div key={e.id} className="p-4 flex items-center justify-between">
              <div>
                <p className="font-medium text-sm">${e.amount.toFixed(2)}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {e.category} {e.note && `· ${e.note}`} · {new Date(e.spent_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={() => handleDelete(e.id)}
                className="text-xs text-red-400 hover:text-red-600"
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