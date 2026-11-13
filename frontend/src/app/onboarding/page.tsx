"use client"
import { useEffect, useRef, useState } from "react"
import type { ChangeEvent, FormEvent } from "react"
import { useRouter } from "next/navigation"
import useSWR from "swr"
import { z } from "zod"
import api from "@/lib/api"
import { ALL_MODULES, type ModuleKey } from "@/lib/modules"
import { recordWizardDone, todayLocalDate } from "@/lib/setupChecklist"
import { Tag, type IconType } from "@/components/primitives"
import {
  ActivityIcon,
  BookIcon,
  BriefcaseIcon,
  LeafIcon,
  WalletIcon,
} from "@/components/icons"

const fetcher = (url: string) => api.get(url).then(r => r.data)

interface Me {
  id: string
  email: string
  name: string | null
  monthly_budget: number
  weekly_capacity_hours: number
  onboarding_completed_at: string | null
  active_modules: ModuleKey[]
}

interface BriefingPriority {
  title: string
  reason?: string
}

interface Briefing {
  summary?: string
  priorities?: BriefingPriority[]
  sample?: boolean
}

// Activity events logged by the wizard. step is required by the backend for
// onboarding_step_completed and ignored for the other events.
async function postEvent(body: { event: string; step?: 1 | 2 | 3 | 4 }): Promise<void> {
  try {
    await api.post("/onboarding/events", body)
  } catch {
    // Analytics must never block or break the wizard.
  }
}

const MODULE_META: { key: ModuleKey; label: string; hint: string; Icon: IconType }[] = [
  { key: "academics", label: "Academics", hint: "Assignments and deadlines", Icon: BookIcon },
  { key: "jobs", label: "Job hunt", hint: "Applications and follow-ups", Icon: BriefcaseIcon },
  { key: "fitness", label: "Fitness", hint: "Workouts and routines", Icon: ActivityIcon },
  { key: "finance", label: "Finance", hint: "Budget and spending", Icon: WalletIcon },
]

const STEPS = [
  { title: "What are you juggling?", blurb: "Pick the areas you want LifeOS to track." },
  { title: "Your limits", blurb: "Two numbers keep your plan realistic." },
  { title: "Quick add", blurb: "Add a few real things now, or skip and do it later." },
  { title: "Your first briefing", blurb: "Here is what LifeOS would focus on for you." },
]

const POST_PATHS: Record<ModuleKey, string> = {
  academics: "/assignments",
  jobs: "/jobs",
  fitness: "/workouts",
  finance: "/expenses",
}

type FieldType = "text" | "number" | "date" | "select" | "text-datalist"

interface FieldDef {
  name: string
  label: string
  type: FieldType
  placeholder?: string
  options?: { value: string; label: string }[]
}

// Kept in sync with the value lists on the existing module pages.
const EXPENSE_CATEGORIES = ["food", "transport", "study", "fitness", "other"]
const WORKOUT_TYPES = ["Run", "Gym", "Yoga", "Basketball", "Swimming", "Cycling"]

const QUICK_FIELDS: Record<ModuleKey, FieldDef[]> = {
  academics: [
    { name: "title", label: "Title", type: "text", placeholder: "Finish lab report" },
    { name: "due_date", label: "Due date", type: "date" },
    { name: "course", label: "Course (optional)", type: "text", placeholder: "CS 101" },
  ],
  jobs: [
    { name: "company", label: "Company", type: "text", placeholder: "Acme" },
    { name: "role", label: "Role", type: "text", placeholder: "Software intern" },
    { name: "applied_date", label: "Applied date", type: "date" },
  ],
  fitness: [
    { name: "type", label: "Type", type: "text-datalist", placeholder: "Run, Gym, Yoga…", options: WORKOUT_TYPES.map(t => ({ value: t, label: t })) },
    { name: "duration_mins", label: "Duration (minutes)", type: "number", placeholder: "30" },
    { name: "notes", label: "Notes (optional)", type: "text", placeholder: "Leg day at the gym" },
  ],
  finance: [
    { name: "amount", label: "Amount", type: "number", placeholder: "12.50" },
    {
      name: "category",
      label: "Category",
      type: "select",
      options: EXPENSE_CATEGORIES.map(c => ({ value: c, label: c.charAt(0).toUpperCase() + c.slice(1) })),
    },
    { name: "note", label: "Note (optional)", type: "text", placeholder: "Coffee" },
  ],
}

const SUBMIT_LABELS: Record<ModuleKey, string> = {
  academics: "Add assignment",
  jobs: "Add application",
  fitness: "Log workout",
  finance: "Add expense",
}

// Request shapes mirror the existing module pages and the backend schemas.
const academicsQuickSchema = z.object({
  title: z.string().trim().min(1, "Add a title"),
  due_date: z
    .string()
    .min(1, "Pick a due date")
    .refine(v => !Number.isNaN(Date.parse(v)), "Pick a due date"),
  course: z.string(),
})

const jobsQuickSchema = z.object({
  company: z.string().trim().min(1, "Add the company"),
  role: z.string().trim().min(1, "Add the role"),
  applied_date: z
    .string()
    .min(1, "Pick a date")
    .refine(v => !Number.isNaN(Date.parse(v)), "Pick a date"),
})

const workoutQuickSchema = z.object({
  type: z.string().trim().min(1, "Add the workout type"),
  duration_mins: z
    .string()
    .refine(v => Number.isInteger(Number(v)) && Number(v) > 0, "Enter the minutes"),
  notes: z.string(),
})

const expenseQuickSchema = z.object({
  amount: z.string().refine(v => Number(v) > 0, "Enter an amount"),
  category: z.string().min(1, "Pick a category"),
  note: z.string(),
})

const inputClass =
  "w-full border border-[var(--rule)] bg-[var(--surface)] text-[var(--foreground)] placeholder:text-[var(--muted-2)] rounded-md px-3 py-2 text-sm outline-none transition-colors focus:border-[var(--accent)] focus-visible:ring-2 focus-visible:ring-[var(--accent)]/40 disabled:opacity-60"

const primaryButtonClass =
  "bg-[var(--accent)] text-white px-5 py-2 rounded-md text-sm font-medium cursor-pointer transition-opacity hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--surface)]"

const secondaryButtonClass =
  "text-sm text-[var(--muted)] hover:text-[var(--foreground)] px-2 py-2 rounded-md cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--surface)]"

function emptyQuickValues(): Record<ModuleKey, Record<string, string>> {
  const today = todayLocalDate()
  return {
    academics: { title: "", due_date: "", course: "" },
    jobs: { company: "", role: "", applied_date: today },
    fitness: { type: "", duration_mins: "30", notes: "" },
    finance: { amount: "", category: "food", note: "" },
  }
}

function MiniForm({
  idPrefix,
  fields,
  values,
  disabled,
  busy,
  submitLabel,
  error,
  onChange,
  onSubmit,
}: {
  idPrefix: string
  fields: FieldDef[]
  values: Record<string, string>
  disabled: boolean
  busy: boolean
  submitLabel: string
  error: string
  onChange: (name: string, value: string) => void
  onSubmit: (e: FormEvent<HTMLFormElement>) => void
}) {
  return (
    <form onSubmit={onSubmit} noValidate className="space-y-3">
      {fields.map(field => {
        const id = `${idPrefix}-${field.name}`
        const handle = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
          onChange(field.name, e.target.value)
        return (
          <div key={field.name}>
            <label htmlFor={id} className="block text-xs font-medium text-[var(--muted)] mb-1">
              {field.label}
            </label>
            {field.type === "select" ? (
              <select id={id} value={values[field.name] ?? ""} disabled={disabled} onChange={handle} className={`${inputClass} cursor-pointer`}>
                {(field.options ?? []).map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                id={id}
                type={field.type === "number" ? "number" : field.type === "date" ? "date" : "text"}
                inputMode={field.type === "number" ? "decimal" : undefined}
                placeholder={field.placeholder}
                value={values[field.name] ?? ""}
                disabled={disabled}
                onChange={handle}
                list={field.type === "text-datalist" ? `${id}-list` : undefined}
                className={inputClass}
              />
            )}
            {field.type === "text-datalist" && (
              <datalist id={`${id}-list`}>
                {(field.options ?? []).map(opt => (
                  <option key={opt.value} value={opt.value} />
                ))}
              </datalist>
            )}
          </div>
        )
      })}
      {error && (
        <p className="text-xs text-[var(--danger)]" role="alert">
          {error}
        </p>
      )}
      <button type="submit" disabled={disabled || busy} className={primaryButtonClass}>
        {busy ? "Adding…" : submitLabel}
      </button>
    </form>
  )
}

export default function OnboardingPage() {
  const router = useRouter()
  const { data: me, isLoading, error, mutate } = useSWR<Me>("/auth/me", fetcher)

  const [step, setStep] = useState(1)
  const [chosen, setChosen] = useState<ModuleKey[]>(ALL_MODULES)
  const [capacity, setCapacity] = useState("40")
  const [budget, setBudget] = useState("200")
  const [hint, setHint] = useState("")
  const [syncNote, setSyncNote] = useState("")
  const [navBusy, setNavBusy] = useState(false)

  const [quick, setQuick] = useState<Record<ModuleKey, Record<string, string>>>(emptyQuickValues)
  const [quickErr, setQuickErr] = useState<Record<ModuleKey, string>>({
    academics: "",
    jobs: "",
    fitness: "",
    finance: "",
  })
  const [addedCount, setAddedCount] = useState(0)
  const [savingModule, setSavingModule] = useState<ModuleKey | null>(null)

  const [briefing, setBriefing] = useState<Briefing | null>(null)
  const [briefingLoading, setBriefingLoading] = useState(false)
  const [briefingFailed, setBriefingFailed] = useState(false)
  const [completing, setCompleting] = useState(false)

  // Guards the started event against React StrictMode double-mounting.
  const startedRef = useRef(false)
  const briefingRef = useRef(false)

  // Load the account, bounce anyone who already finished, and otherwise log
  // the start of the wizard once.
  useEffect(() => {
    if (!me) return
    if (me.onboarding_completed_at) {
      router.replace("/dashboard")
      return
    }
    if (startedRef.current) return
    startedRef.current = true
    setChosen(me.active_modules?.length ? me.active_modules : ALL_MODULES)
    setCapacity(String(me.weekly_capacity_hours ?? 40))
    setBudget(String(me.monthly_budget ?? 200))
    void postEvent({ event: "onboarding_started" })
  }, [me, router])

  // Step 4 fetches the briefing once, then logs that it was seen.
  useEffect(() => {
    if (step !== 4 || briefingRef.current) return
    briefingRef.current = true
    setBriefingLoading(true)
    api
      .post("/ai/briefing")
      .then(async res => {
        setBriefing(res.data as Briefing)
        await postEvent({ event: "first_briefing_viewed" })
      })
      .catch(() => setBriefingFailed(true))
      .finally(() => setBriefingLoading(false))
  }, [step])

  async function patchMe(body: Record<string, unknown>): Promise<boolean> {
    try {
      const res = await api.patch<Me>("/auth/me", body)
      // Keep the SWR cache in step with the server so the dashboard guard
      // does not bounce the user back into the wizard.
      await mutate(res.data, false)
      setSyncNote("")
      return true
    } catch {
      setSyncNote("Couldn't save that just now. You can keep going.")
      return false
    }
  }

  function toggleModule(key: ModuleKey) {
    setHint("")
    setChosen(prev => (prev.includes(key) ? prev.filter(m => m !== key) : [...prev, key]))
  }

  async function nextStep() {
    if (navBusy) return
    setHint("")
    if (step === 1) {
      if (chosen.length === 0) {
        setHint("Pick at least one")
        return
      }
      setNavBusy(true)
      await patchMe({ active_modules: chosen })
      await postEvent({ event: "onboarding_step_completed", step: 1 })
      setNavBusy(false)
      setStep(2)
      return
    }
    if (step === 2) {
      const cap = Number(capacity)
      const showBudget = chosen.includes("finance")
      const bud = Number(budget)
      if (!Number.isFinite(cap) || cap < 0) {
        setHint("Weekly capacity must be 0 or more.")
        return
      }
      if (showBudget && (!Number.isFinite(bud) || bud < 0)) {
        setHint("Monthly budget must be 0 or more.")
        return
      }
      const body: Record<string, unknown> = { weekly_capacity_hours: cap }
      if (showBudget) body.monthly_budget = bud
      setNavBusy(true)
      await patchMe(body)
      await postEvent({ event: "onboarding_step_completed", step: 2 })
      setNavBusy(false)
      setStep(3)
      return
    }
    if (step === 3) {
      setNavBusy(true)
      await postEvent({ event: "onboarding_step_completed", step: 3 })
      setNavBusy(false)
      setStep(4)
    }
  }

  function skipStep() {
    if (step >= 4) return
    setHint("")
    setSyncNote("")
    setStep(step + 1)
  }

  async function handleQuickAdd(moduleKey: ModuleKey) {
    if (addedCount >= 3 || savingModule) return
    const values = quick[moduleKey]
    let payload: Record<string, unknown>

    if (moduleKey === "academics") {
      const parsed = academicsQuickSchema.safeParse(values)
      if (!parsed.success) {
        setQuickErr(prev => ({ ...prev, academics: parsed.error.issues[0]?.message ?? "Check the fields" }))
        return
      }
      payload = {
        title: parsed.data.title,
        course: parsed.data.course.trim() || undefined,
        due_date: new Date(parsed.data.due_date).toISOString(),
        estimated_hours: 1,
      }
    } else if (moduleKey === "jobs") {
      const parsed = jobsQuickSchema.safeParse(values)
      if (!parsed.success) {
        setQuickErr(prev => ({ ...prev, jobs: parsed.error.issues[0]?.message ?? "Check the fields" }))
        return
      }
      payload = {
        company: parsed.data.company,
        role: parsed.data.role,
        applied_date: parsed.data.applied_date,
      }
    } else if (moduleKey === "fitness") {
      const parsed = workoutQuickSchema.safeParse(values)
      if (!parsed.success) {
        setQuickErr(prev => ({ ...prev, fitness: parsed.error.issues[0]?.message ?? "Check the fields" }))
        return
      }
      payload = {
        type: parsed.data.type,
        duration_mins: Number(parsed.data.duration_mins),
        notes: parsed.data.notes.trim() || undefined,
      }
    } else {
      const parsed = expenseQuickSchema.safeParse(values)
      if (!parsed.success) {
        setQuickErr(prev => ({ ...prev, finance: parsed.error.issues[0]?.message ?? "Check the fields" }))
        return
      }
      payload = {
        amount: Number(parsed.data.amount),
        category: parsed.data.category,
        note: parsed.data.note.trim() || undefined,
        spent_at: new Date(todayLocalDate()).toISOString(),
      }
    }

    setSavingModule(moduleKey)
    setQuickErr(prev => ({ ...prev, [moduleKey]: "" }))
    try {
      await api.post(POST_PATHS[moduleKey], payload)
      setQuick(prev => ({ ...prev, [moduleKey]: emptyQuickValues()[moduleKey] }))
      setAddedCount(count => count + 1)
    } catch {
      setQuickErr(prev => ({ ...prev, [moduleKey]: "Couldn't add that. Try again." }))
    } finally {
      setSavingModule(null)
    }
  }

  /**
   * The single completion path. Finishing the last step and skipping the whole
   * wizard both mark onboarding done, so the checklist and the dashboard guard
   * behave the same either way.
   */
  async function completeFlow(skipSetup: boolean) {
    if (completing) return
    setCompleting(true)
    const now = new Date().toISOString()
    // Local flags first, they are read as soon as the dashboard mounts.
    recordWizardDone()
    if (skipSetup) await postEvent({ event: "onboarding_skipped" })
    const saved = await patchMe({ onboarding_completed_at: now })
    if (!saved && me) {
      // Reflect the intended state locally so the dashboard guard does not
      // send the user straight back here if the PATCH failed.
      await mutate({ ...me, onboarding_completed_at: now }, false)
    }
    await postEvent({ event: "onboarding_completed" })
    router.push("/dashboard")
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--background)] px-4">
        <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-xl shadow-sm p-8 max-w-md w-full text-center">
          <p className="text-sm text-[var(--foreground)] mb-4">
            We couldn&apos;t load your account. Please sign in again.
          </p>
          <a
            href="/auth/login"
            className="text-sm text-[var(--accent)] underline underline-offset-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] rounded-sm"
          >
            Go to sign in
          </a>
        </div>
      </div>
    )
  }

  if (!me || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--background)]">
        <p className="text-sm text-[var(--muted)]" role="status">
          Loading…
        </p>
      </div>
    )
  }

  const financeChosen = chosen.includes("finance")

  return (
    <div className="min-h-screen bg-[var(--background)] flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <LeafIcon className="w-5 h-5 text-[var(--accent)]" />
            <span className="text-sm font-semibold text-[var(--foreground)]">LifeOS</span>
          </div>
          <button
            type="button"
            onClick={() => completeFlow(true)}
            disabled={completing}
            className={secondaryButtonClass}
          >
            Skip setup
          </button>
        </div>

        <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-xl shadow-sm p-8">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-medium text-[var(--muted)] uppercase tracking-wide" aria-live="polite">
              Step {step} of 4
            </p>
            {step === 3 && addedCount > 0 && (
              <p className="text-xs text-[var(--muted-2)]">
                {addedCount} of 3 added
              </p>
            )}
          </div>
          <div className="h-1 w-full bg-[var(--rule)] rounded-full overflow-hidden mb-6">
            <div
              className="h-full bg-[var(--accent)] transition-[width] duration-300"
              style={{ width: `${(step / 4) * 100}%` }}
            />
          </div>

          <h1 className="text-xl font-semibold text-[var(--foreground)] mb-1">
            {STEPS[step - 1].title}
          </h1>
          <p className="text-sm text-[var(--muted)] mb-6">{STEPS[step - 1].blurb}</p>

          {step === 1 && (
            <fieldset>
              <legend className="sr-only">Areas to track</legend>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {MODULE_META.map(({ key, label, hint: moduleHint, Icon }) => {
                  const checked = chosen.includes(key)
                  return (
                    <label
                      key={key}
                      className={`flex items-start gap-3 border rounded-md p-4 cursor-pointer transition-colors ${
                        checked
                          ? "border-[var(--accent)] bg-[var(--callout-green)]"
                          : "border-[var(--rule)] bg-[var(--surface)] hover:bg-[var(--surface-hover)]"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleModule(key)}
                        className="mt-0.5 h-4 w-4 shrink-0 accent-[var(--accent)] cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2"
                      />
                      <span className="min-w-0">
                        <span className="flex items-center gap-1.5 text-sm font-medium text-[var(--foreground)]">
                          <Icon className="w-4 h-4 text-[var(--muted)]" />
                          {label}
                        </span>
                        <span className="block text-xs text-[var(--muted)] mt-0.5">
                          {moduleHint}
                        </span>
                      </span>
                    </label>
                  )
                })}
              </div>
            </fieldset>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div>
                <label htmlFor="onboarding-capacity" className="block text-sm font-medium text-[var(--foreground)] mb-1">
                  Weekly capacity (hours)
                </label>
                <input
                  id="onboarding-capacity"
                  type="number"
                  min={0}
                  step={1}
                  value={capacity}
                  onChange={e => setCapacity(e.target.value)}
                  className={inputClass}
                />
                <p className="text-xs text-[var(--muted)] mt-1">
                  Hours a week you can realistically plan for.
                </p>
              </div>
              {financeChosen && (
                <div>
                  <label htmlFor="onboarding-budget" className="block text-sm font-medium text-[var(--foreground)] mb-1">
                    Monthly budget
                  </label>
                  <input
                    id="onboarding-budget"
                    type="number"
                    min={0}
                    step={1}
                    value={budget}
                    onChange={e => setBudget(e.target.value)}
                    className={inputClass}
                  />
                  <p className="text-xs text-[var(--muted)] mt-1">
                    Drives the 50/30/20 envelopes.
                  </p>
                </div>
              )}
            </div>
          )}

          {step === 3 && (
            <div className="space-y-5">
              <p className="text-xs text-[var(--muted)]">
                Optional. Add up to 3 items now, or skip and add them later.
              </p>
              {chosen.length === 0 && (
                <p className="text-sm text-[var(--muted-2)]">
                  No areas selected, so there is nothing to add here.
                </p>
              )}
              {chosen.map(moduleKey => {
                const meta = MODULE_META.find(m => m.key === moduleKey)
                if (!meta) return null
                const ModuleIcon = meta.Icon
                return (
                  <div
                    key={moduleKey}
                    className="border border-[var(--rule)] rounded-md p-4 bg-[var(--surface)]"
                  >
                    <p className="flex items-center gap-1.5 text-sm font-medium text-[var(--foreground)] mb-3">
                      <ModuleIcon className="w-4 h-4 text-[var(--muted)]" />
                      {meta.label}
                    </p>
                    <MiniForm
                      idPrefix={`quick-${moduleKey}`}
                      fields={QUICK_FIELDS[moduleKey]}
                      values={quick[moduleKey]}
                      disabled={addedCount >= 3}
                      busy={savingModule === moduleKey}
                      submitLabel={SUBMIT_LABELS[moduleKey]}
                      error={quickErr[moduleKey]}
                      onChange={(name, value) =>
                        setQuick(prev => ({ ...prev, [moduleKey]: { ...prev[moduleKey], [name]: value } }))
                      }
                      onSubmit={e => {
                        e.preventDefault()
                        void handleQuickAdd(moduleKey)
                      }}
                    />
                  </div>
                )
              })}
            </div>
          )}

          {step === 4 && (
            <div aria-busy={briefingLoading}>
              {briefingLoading ? (
                <p className="text-sm text-[var(--muted)] italic" role="status">
                  Generating your first briefing…
                </p>
              ) : briefingFailed ? (
                <p className="text-sm text-[var(--muted)]">
                  Your briefing could not be loaded right now. You can still head
                  to the dashboard.
                </p>
              ) : briefing ? (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <p className="text-xs font-medium text-[var(--muted)] uppercase tracking-wide">
                      Daily briefing
                    </p>
                    {briefing.sample && <Tag>Sample briefing</Tag>}
                  </div>
                  {(briefing.priorities ?? []).length > 0 && (
                    <ol className="space-y-3 mb-4">
                      {(briefing.priorities ?? []).slice(0, 3).map((priority, i) => (
                        <li key={i} className="flex items-start gap-3">
                          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[var(--accent)] text-white text-xs font-bold shrink-0 mt-0.5">
                            {i + 1}
                          </span>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-[var(--foreground)]">
                              {priority.title}
                            </p>
                            {priority.reason && (
                              <p className="text-xs text-[var(--muted)]">{priority.reason}</p>
                            )}
                          </div>
                        </li>
                      ))}
                    </ol>
                  )}
                  {briefing.summary ? (
                    <p className="text-[15px] leading-relaxed text-[var(--foreground)]">
                      {briefing.summary}
                    </p>
                  ) : (briefing.priorities ?? []).length === 0 ? (
                    <p className="text-sm text-[var(--muted)] italic">No brief yet.</p>
                  ) : null}
                </div>
              ) : (
                <p className="text-sm text-[var(--muted)] italic">No brief yet.</p>
              )}
            </div>
          )}

          {hint && (
            <p className="text-xs text-[var(--danger)] mt-4" role="alert">
              {hint}
            </p>
          )}
          {syncNote && (
            <p className="text-xs text-[var(--muted)] mt-2" role="status">
              {syncNote}
            </p>
          )}

          <div className="mt-8 pt-5 border-t border-[var(--rule)] flex items-center justify-between gap-3">
            {step < 4 ? (
              <>
                <button type="button" onClick={skipStep} className={secondaryButtonClass}>
                  Skip
                </button>
                <button
                  type="button"
                  onClick={() => void nextStep()}
                  disabled={navBusy}
                  className={primaryButtonClass}
                >
                  {navBusy ? "Saving…" : "Next"}
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => void completeFlow(false)}
                  disabled={completing}
                  className={secondaryButtonClass}
                >
                  Skip for now
                </button>
                <button
                  type="button"
                  onClick={() => void completeFlow(false)}
                  disabled={completing}
                  className={primaryButtonClass}
                >
                  {completing ? "Finishing…" : "Go to dashboard"}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
