"use client"
import useSWR from "swr"
import api from "@/lib/api"
import { UserIcon } from "@/components/icons"

const fetcher = (url: string) => api.get(url).then(r => r.data)

export default function ProfilePage() {
  const { data: user } = useSWR("/auth/me", fetcher)

  if (!user) {
    return (
      <div className="max-w-3xl mx-auto px-16 py-16">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-32 bg-[var(--callout-gray)] rounded" />
          <div className="h-40 bg-[var(--callout-gray)] rounded-md" />
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-16 py-16">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-full bg-[var(--callout-blue)] flex items-center justify-center">
          <UserIcon className="w-5 h-5 text-[var(--foreground)]" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-[var(--foreground)]">Profile</h1>
          <p className="text-sm text-[var(--muted)]">Account settings and preferences</p>
        </div>
      </div>

      <div className="space-y-6">
        <section className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-[var(--foreground)] mb-4">Account</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-[var(--muted)]">Name</span>
              <span className="text-sm font-medium text-[var(--foreground)]">{user.name || "—"}</span>
            </div>
            <div className="border-t border-[var(--rule)]" />
            <div className="flex justify-between items-center">
              <span className="text-sm text-[var(--muted)]">Email</span>
              <span className="text-sm font-medium text-[var(--foreground)]">{user.email}</span>
            </div>
          </div>
        </section>

        <section className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-[var(--foreground)] mb-4">Budget Settings</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-[var(--muted)]">Monthly Budget</span>
              <span className="text-sm font-medium text-[var(--foreground)]">${user.monthly_budget?.toFixed(2) ?? "200.00"}</span>
            </div>
            <div className="border-t border-[var(--rule)]" />
            <div className="flex justify-between items-center">
              <span className="text-sm text-[var(--muted)]">Weekly Capacity</span>
              <span className="text-sm font-medium text-[var(--foreground)]">{user.weekly_capacity_hours ?? 40} hours</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
