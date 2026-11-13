// Client-side flags behind the dashboard "LifeOS setup" checklist.
//
// The wizard writes these when it completes; the dashboard reads them. They
// never leave the browser, so they are a v1 convenience: the backend only
// knows onboarding_completed_at. Items 1-4 need both signals (backend
// timestamp plus this flag) because a seeded or demo account can be marked
// onboarded without ever seeing the wizard shell.

export const WIZARD_DONE_KEY = "lifeos_onboarding_wizard_done"
export const ONBOARDING_DATE_KEY = "lifeos_onboarding_date"
export const BRIEFING_OPENED_KEY = "lifeos_briefing_opened_date"
export const SETUP_DISMISSED_KEY = "lifeos_setup_dismissed"

/** Today in the browser's local time as YYYY-MM-DD. */
export function todayLocalDate(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function read(key: string): string | null {
  if (typeof window === "undefined") return null
  try {
    return window.localStorage.getItem(key)
  } catch {
    // Storage blocked (private mode), treat the flag as "not set".
    return null
  }
}

function write(key: string, value: string): void {
  if (typeof window === "undefined") return
  try {
    window.localStorage.setItem(key, value)
  } catch {
    // Storage blocked, the checklist simply stays unchecked.
  }
}

export interface ChecklistLocal {
  wizardDone: boolean
  briefingSeen: boolean
  dismissed: boolean
}

/** Called on the wizard's final button, both on finish and on skip setup. */
export function recordWizardDone(): void {
  write(WIZARD_DONE_KEY, "1")
  write(ONBOARDING_DATE_KEY, todayLocalDate())
}

/**
 * Called when the dashboard briefing renders. Keeps the latest date rather
 * than only the first one, so item 6 ("open tomorrow's briefing") can flip to
 * done the day after the wizard finished instead of being stuck forever when
 * the briefing first renders on the same day as onboarding.
 */
export function recordBriefingOpened(): void {
  const stored = read(BRIEFING_OPENED_KEY)
  const today = todayLocalDate()
  if (stored === null || today > stored) write(BRIEFING_OPENED_KEY, today)
}

/**
 * Reads the local flags for the checklist.
 *
 * Item 6: the briefing must have been opened on a day strictly after the day
 * the wizard finished. Accounts with no onboarding date (demo or seeded) count
 * as done as soon as any briefing has been opened, because there is no
 * "tomorrow" to compare against.
 */
export function readChecklistLocal(): ChecklistLocal {
  const opened = read(BRIEFING_OPENED_KEY)
  const onboarding = read(ONBOARDING_DATE_KEY)
  const briefingSeen = opened !== null && (onboarding === null || opened > onboarding)
  return {
    wizardDone: read(WIZARD_DONE_KEY) === "1",
    briefingSeen,
    dismissed: read(SETUP_DISMISSED_KEY) === "1",
  }
}

export function dismissChecklist(): void {
  write(SETUP_DISMISSED_KEY, "1")
}
