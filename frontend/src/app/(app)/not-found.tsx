"use client"
import Link from "next/link"
import { LeafIcon } from "@/components/icons"

export default function NotFound() {
  return (
    <div className="max-w-3xl mx-auto px-16 py-16 flex flex-col items-center text-center">
      <div className="w-16 h-16 rounded-full bg-[var(--callout-gray)] flex items-center justify-center mb-6">
        <LeafIcon className="w-8 h-8 text-[var(--muted-2)]" />
      </div>
      <h1 className="text-4xl font-bold text-[var(--foreground)] mb-2">404</h1>
      <p className="text-lg text-[var(--muted)] mb-8">This page doesn&apos;t exist.</p>
      <Link
        href="/dashboard"
        className="bg-[var(--accent)] text-white px-5 py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity"
      >
        Back to Dashboard
      </Link>
    </div>
  )
}
