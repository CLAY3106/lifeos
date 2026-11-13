"use client"
import { useEffect, useState } from "react"
import useSWR from "swr"
import api from "@/lib/api"
import { CheckCircleIcon } from "@/components/icons"
import {
  dismissChecklist,
  readChecklistLocal,
  recordBriefingOpened,
  type ChecklistLocal,
} from "@/lib/setupChecklist"

const fetcher = (url: string) => api.get(url).then(r => r.data)

interface ChecklistItem {
  label: string
  done: boolean
}

/**
 * "LifeOS setup: X of 6" card.
 *
 * Items 1-4 come pre-checked from the wizard: the backend timestamp
 * (onboarding_completed_at) plus the local flag written when the wizard's
 * final button was pressed. Item 5 reads live data, item 6 compares the local
 * briefing date against the onboarding date. The whole card disappears once
 * everything is done or the user dismisses it.
 */
export default function SetupChecklist({
  wizardCompleted,
  briefingRendered,
}: {
  wizardCompleted: boolean
  briefingRendered: boolean
}) {
  const { data: routines } = useSWR("/routines", fetcher)
  const [local, setLocal] = useState<ChecklistLocal | null>(null)
  const [dismissed, setDismissed] = useState(false)

  // Record the briefing visit first, then re-read so item 6 can flip to done.
  // Deferred one tick so the read of localStorage happens after the browser
  // settles, not synchronously inside the effect body.
  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (briefingRendered) recordBriefingOpened()
      const flags = readChecklistLocal()
      setLocal(flags)
      if (flags.dismissed) setDismissed(true)
    }, 0)
    return () => window.clearTimeout(timer)
  }, [briefingRendered])

  if (!local || dismissed) return null

  const wizardItemsDone = wizardCompleted && local.wizardDone

  const items: ChecklistItem[] = [
    { label: "Choose your areas", done: wizardItemsDone },
    { label: "Set your limits", done: wizardItemsDone },
    { label: "Add your first items", done: wizardItemsDone },
    { label: "See your first briefing", done: wizardItemsDone },
    { label: "Add a workout routine", done: (routines?.length ?? 0) > 0 },
    { label: "Open tomorrow's briefing", done: local.briefingSeen },
  ]

  const doneCount = items.filter(item => item.done).length
  if (doneCount === items.length) return null

  function handleDismiss() {
    dismissChecklist()
    setDismissed(true)
  }

  return (
    <section
      aria-label="Setup checklist"
      className="bg-[var(--surface)] border border-[var(--rule)] rounded-lg p-5 shadow-sm mb-8"
    >
      <div className="flex items-center justify-between gap-3 mb-3">
        <h2 className="text-sm font-semibold text-[var(--foreground)]">
          LifeOS setup: {doneCount} of {items.length}
        </h2>
        <button
          type="button"
          onClick={handleDismiss}
          className="text-xs text-[var(--muted)] hover:text-[var(--foreground)] transition-colors cursor-pointer rounded px-1 py-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2"
        >
          Dismiss
        </button>
      </div>
      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5">
        {items.map(item => (
          <li key={item.label} className="flex items-center gap-2 text-sm">
            {item.done ? (
              <CheckCircleIcon className="w-4 h-4 shrink-0 text-[var(--accent)]" />
            ) : (
              <span
                aria-hidden="true"
                className="w-4 h-4 shrink-0 rounded-full border border-[var(--rule)]"
              />
            )}
            <span className={item.done ? "text-[var(--muted)]" : "text-[var(--foreground)]"}>
              {item.label}
            </span>
            <span className="sr-only">{item.done ? "done" : "not done"}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
