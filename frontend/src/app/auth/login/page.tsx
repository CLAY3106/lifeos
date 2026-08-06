"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import api from "@/lib/api"

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
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-lg shadow w-full max-w-md">
        <h1 className="text-2xl font-bold mb-6">LifeOS</h1>
        <h2 className="text-lg font-medium mb-4">Sign in</h2>

        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
              onKeyDown={e => e.key === "Enter" && handleLogin()}
            />
          </div>
          <button
            onClick={() => handleLogin()}
            disabled={loading}
            className="w-full bg-black text-white py-2 rounded text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </div>

        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="bg-white px-2 text-gray-500">or</span>
          </div>
        </div>

        <button
          onClick={handleGuestLogin}
          disabled={loading}
          className="w-full border border-gray-300 py-2 rounded text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
        >
          Try as guest
        </button>
        <p className="text-xs text-center text-gray-500 mt-2">
          Explore the app with a pre-loaded demo account
        </p>

        <p className="text-sm text-center mt-4">
          No account?{" "}
          <a href="/auth/register" className="underline">Register</a>
        </p>
      </div>
    </div>
  )
}