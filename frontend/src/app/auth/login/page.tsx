"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import api from "@/lib/api"
import { LeafIcon } from "@/components/icons"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleLogin(creds?: { email: string; password: string }) {
    setLoading(true)
    setError("")
    try {
      await api.post("/auth/login", creds ?? { email, password })
      router.push("/dashboard")
    } catch (err: any) {
      setError("Invalid email or password")
    } finally {
      setLoading(false)
    }
  }

  function handleGuestLogin() {
    handleLogin({ email: "demo@lifeos.app", password: "demo1234" })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--background)] px-4">
      <div className="bg-[var(--surface)] border border-[var(--rule)] p-8 rounded-xl shadow-sm w-full max-w-md">
        <div className="flex items-center gap-2 mb-6">
          <LeafIcon className="w-5 h-5 text-[var(--accent)]" />
          <span className="text-lg font-semibold text-[var(--foreground)]">LifeOS</span>
        </div>
        <h2 className="text-lg font-medium mb-4 text-[var(--foreground)]">Sign in</h2>

        {error && (
          <p className="text-[var(--danger)] text-sm mb-4" role="alert">
            {error}
          </p>
        )}

        <div className="space-y-4">
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
              onKeyDown={e => e.key === "Enter" && handleLogin()}
            />
          </div>
          <button
            onClick={() => handleLogin()}
            disabled={loading}
            className="w-full bg-[var(--accent)] text-white py-2 rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 cursor-pointer transition-opacity focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </div>

        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-[var(--rule)]" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="bg-[var(--surface)] px-2 text-[var(--muted)]">or</span>
          </div>
        </div>

        <button
          onClick={handleGuestLogin}
          disabled={loading}
          className="w-full border border-[var(--rule)] text-[var(--foreground)] py-2 rounded-md text-sm font-medium hover:bg-[var(--surface-hover)] disabled:opacity-50 cursor-pointer transition-colors focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2"
        >
          Try as guest
        </button>
        <p className="text-xs text-center text-[var(--muted)] mt-2">
          Explore the app with a pre-loaded demo account
        </p>

        <p className="text-sm text-center mt-4 text-[var(--muted)]">
          No account?{" "}
          <a href="/auth/register" className="text-[var(--accent)] underline underline-offset-2">
            Register
          </a>
        </p>
      </div>
    </div>
  )
}
