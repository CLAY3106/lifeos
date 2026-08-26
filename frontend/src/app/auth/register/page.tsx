"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import api from "@/lib/api"
import { LeafIcon } from "@/components/icons"

export default function RegisterPage() {
  const router = useRouter()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleRegister() {
    setLoading(true)
    setError("")
    try {
      await api.post("/auth/register", { name, email, password })
      router.push("/dashboard")
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--background)] px-4">
      <div className="bg-[var(--surface)] border border-[var(--rule)] p-8 rounded-xl shadow-sm w-full max-w-md">
        <div className="flex items-center gap-2 mb-6">
          <LeafIcon className="w-5 h-5 text-[var(--accent)]" />
          <span className="text-lg font-semibold text-[var(--foreground)]">LifeOS</span>
        </div>
        <h2 className="text-lg font-medium mb-4 text-[var(--foreground)]">Create account</h2>

        {error && (
          <p className="text-[var(--danger)] text-sm mb-4" role="alert">
            {error}
          </p>
        )}

        <div className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium mb-1 text-[var(--foreground)]">
              Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full border border-[var(--rule)] bg-[var(--surface)] text-[var(--foreground)] rounded-md px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:border-[var(--accent)] transition-colors"
              placeholder="Son Le"
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1 text-[var(--foreground)]">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full border border-[var(--rule)] bg-[var(--surface)] text-[var(--foreground)] rounded-md px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:border-[var(--accent)] transition-colors"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1 text-[var(--foreground)]">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full border border-[var(--rule)] bg-[var(--surface)] text-[var(--foreground)] rounded-md px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:border-[var(--accent)] transition-colors"
              onKeyDown={e => e.key === "Enter" && handleRegister()}
            />
          </div>
          <button
            onClick={handleRegister}
            disabled={loading}
            className="w-full bg-[var(--accent)] text-white py-2 rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 cursor-pointer transition-opacity focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2"
          >
            {loading ? "Creating account..." : "Create account"}
          </button>
        </div>

        <p className="text-sm text-center mt-4 text-[var(--muted)]">
          Already have an account?{" "}
          <a href="/auth/login" className="text-[var(--accent)] underline underline-offset-2">
            Sign in
          </a>
        </p>
      </div>
    </div>
  )
}
