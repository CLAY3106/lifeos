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
import { Skeleton } from "@/components/skeletons"
import {
  ActivityIcon,
  AlertCircleIcon,
  ArrowRightIcon,
  BookIcon,
  BriefcaseIcon,
  CheckIcon,
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

const STEP_LABELS = ["Areas", "Limits", "Quick add", "Briefing"]

const focusRing =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-strong)] focus-visible:ring-offset-2"

const inputClass =
  "w-full min-h-11 border border-[var(--rule)] bg-[var(--surface)] text-[var(--foreground)] placeholder:text-[var(--muted)] rounded-lg px-3 py-2 text-base sm:text-sm outline-none transition-colors hover:border-[var(--muted-2)] focus:border-[var(--accent-strong)] focus-visible:ring-2 focus-visible:ring-[var(--accent-strong)]/30 disabled:opacity-60 disabled:cursor-not-allowed"

const primaryButtonClass = `inline-flex items-center justify-center gap-2 min-h-11 bg-[var(--accent-strong)] text-[var(--on-accent)] px-5 rounded-lg text-sm font-semibold cursor-pointer transition-[opacity,transform] duration-150 hover:opacity-90 active:scale-[0.98] motion-reduce:transform-none disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 ${focusRing} focus-visible:ring-offset-[var(--surface)]`

const secondaryButtonClass = `inline-flex items-center justify-center min-h-11 px-3 rounded-lg text-sm font-medium text-[var(--muted)] cursor-pointer transition-colors hover:text-[var(--foreground)] hover:bg-[var(--surface-hover)] disabled:opacity-50 disabled:cursor-not-allowed ${focusRing} focus-visible:ring-offset-[var(--surface)]`

function StepProgress({ step }: { step: number }) {
  const label = STEP_LABELS[step - 1]
  return (
    <div className="mb-8">
      <div className="flex items-baseline justify-between gap-3 mb-2.5">
        <p className="text-xs font-semibold tracking-wide text-[var(--accent-strong)]">
          Step {step} of {STEP_LABELS.length}
        </p>
        <p className="text-xs text-[var(--muted)]">{label}</p>
      </div>
      <div
        role="progressbar"
        aria-label="Setup progress"
        aria-valuemin={1}
        aria-valuemax={STEP_LABELS.length}
        aria-valuenow={step}
        aria-valuetext={`Step ${step} of ${STEP_LABELS.length}: ${label}`}
        className="grid grid-cols-4 gap-1.5"
      >
        {STEP_LABELS.map((l, i) => (
          <span
            key={l}
            className={`h-1.5 rounded-full transition-colors duration-300 motion-reduce:transition-none ${
              i < step ? "bg-[var(--accent-strong)]" : "bg-[var(--rule)]"
            }`}
          />
        ))}
      </div>
    </div>
  )
}

function InlineError({ children }: { children: React.ReactNode }) {
  return (
    <p className="flex items-start gap-1.5 text-sm text-[var(--danger)]" role="alert">
      <AlertCircleIcon className="w-4 h-4 shrink-0 mt-0.5" />
      <span>{children}</span>
    </p>
  )
}

function Brand() {
  return (
    <div className="flex items-center gap-2">
      <LeafIcon className="w-5 h-5 text-[var(--accent-strong)]" />
      <span className="text-sm font-semibold text-[var(--foreground)]">LifeOS</span>
    </div>
  )
}

function WizardSkeleton() {
  return (
    <div className="min-h-dvh bg-[var(--background)] flex justify-center px-4 py-8 sm:py-16">
      <div className="w-full max-w-xl" role="status" aria-label="Loading your setup">
        <div className="flex items-center justify-between mb-4 min-h-11">
          <Brand />
        </div>
        <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-2xl shadow-sm p-6 sm:p-10">
          <Skeleton className="h-3 w-24 mb-3" />
          <div className="grid grid-cols-4 gap-1.5 mb-8">
            {[0, 1, 2, 3].map(i => (
              <Skeleton key={i} className="h-1.5 rounded-full" />
            ))}
          </div>
          <Skeleton className="h-6 w-2/3 mb-3" />
          <Skeleton className="h-4 w-1/2 mb-8" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[0, 1, 2, 3].map(i => (
              <Skeleton key={i} className="h-20 rounded-xl" />
            ))}
          </div>
        </div>
        <span className="sr-only">Loading your setup</span>
      </div>
    </div>
  )
}

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
  // Move focus to the new step's heading so keyboard and screen reader users
  // land at the top of the step instead of on a button that no longer exists.
  const headingRef = useRef<HTMLHeadingElement>(null)
  const shownStepRef = useRef(step)

  useEffect(() => {
    if (shownStepRef.current === step) return
    shownStepRef.current = step
    headingRef.current?.focus()
  }, [step])

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
   *
   * The PATCH is the source of truth: the dashboard guard reads the same
   * /auth/me cache, so writing the local "wizard done" flags or navigating
   * before the PATCH succeeds would let the guard bounce the user straight
   * back here once it revalidates against the real (unsaved) server state.
   */
  async function completeFlow(skipSetup: boolean) {
    if (completing) return
    setCompleting(true)
    setSyncNote("")
    const now = new Date().toISOString()
    const saved = await patchMe({ onboarding_completed_at: now })
    if (!saved) {
      setCompleting(false)
      setSyncNote("Couldn't finish setup. Check your connection and try again.")
      return
    }
    recordWizardDone()
    if (skipSetup) await postEvent({ event: "onboarding_skipped" })
    await postEvent({ event: "onboarding_completed" })
    router.push("/dashboard")
  }

  if (error) {
    return (
      <div className="min-h-dvh flex justify-center bg-[var(--background)] px-4 py-8 sm:py-16">
        <div className="w-full max-w-md">
          <div className="flex items-center mb-4 min-h-11">
            <Brand />
          </div>
          <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-2xl shadow-sm p-6 sm:p-10 text-center">
            <span className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--callout-red)] text-[var(--callout-red-text)]">
              <AlertCircleIcon className="w-6 h-6" />
            </span>
            <h1 className="text-lg font-semibold text-[var(--foreground)] mb-1">
              We couldn&apos;t load your account
            </h1>
            <p className="text-sm text-[var(--muted)] mb-6">
              Your session may have expired. Sign in again to pick up where you left off.
            </p>
            <a href="/auth/login" className={primaryButtonClass}>
              Go to sign in
            </a>
          </div>
        </div>
      </div>
    )
  }

  if (!me || isLoading) {
    return <WizardSkeleton />
  }

  const financeChosen = chosen.includes("finance")

  return (
    <div className="min-h-dvh bg-[var(--background)] flex justify-center px-4 py-6 sm:py-16">
      <div className="w-full max-w-xl sm:my-auto">
        <div className="flex items-center justify-between mb-4">
          <Brand />
          <button
            type="button"
            onClick={() => completeFlow(true)}
            disabled={completing}
            className={`${secondaryButtonClass} -mr-3 focus-visible:ring-offset-[var(--background)]`}
          >
            Skip setup
          </button>
        </div>

        <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-2xl shadow-sm px-5 py-6 sm:p-10">
          <StepProgress step={step} />

          <h1
            ref={headingRef}
            tabIndex={-1}
            className="text-2xl font-semibold tracking-tight text-[var(--foreground)] mb-1.5 outline-none [text-wrap:balance]"
          >
            <span className="sr-only">
              Step {step} of {STEP_LABELS.length}:{" "}
            </span>
            {STEPS[step - 1].title}
          </h1>
          <p className="text-[15px] text-[var(--muted)] mb-7">{STEPS[step - 1].blurb}</p>

          {step === 1 && (
            <fieldset>
              <legend className="sr-only">Areas to track</legend>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {MODULE_META.map(({ key, label, hint: moduleHint, Icon }) => {
                  const checked = chosen.includes(key)
                  return (
                    <label
                      key={key}
                      className={`relative flex items-start gap-4 rounded-xl border p-4 cursor-pointer select-none transition-colors duration-150 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-[var(--accent-strong)] has-[:focus-visible]:ring-offset-2 has-[:focus-visible]:ring-offset-[var(--surface)] ${
                        checked
                          ? "border-[var(--accent)] bg-[var(--callout-green)]"
                          : "border-[var(--rule)] bg-[var(--surface)] hover:border-[var(--muted-2)] hover:bg-[var(--surface-hover)]"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleModule(key)}
                        className="sr-only"
                      />
                      <span
                        className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-lg transition-colors ${
                          checked
                            ? "bg-[var(--surface)] text-[var(--accent-strong)]"
                            : "bg-[var(--callout-gray)] text-[var(--muted)]"
                        }`}
                      >
                        <Icon className="w-6 h-6" />
                      </span>
                      <span className="min-w-0 flex-1 pt-0.5 pr-6">
                        <span className="block text-[15px] font-semibold text-[var(--foreground)]">
                          {label}
                        </span>
                        <span className="block text-sm text-[var(--muted)] mt-0.5">
                          {moduleHint}
                        </span>
                      </span>
                      <span
                        aria-hidden="true"
                        className={`absolute top-4 right-4 flex h-5 w-5 items-center justify-center rounded-full border-2 transition-colors ${
                          checked
                            ? "border-[var(--accent-strong)] bg-[var(--accent-strong)] text-[var(--on-accent)]"
                            : "border-[var(--muted)] bg-[var(--surface)]"
                        }`}
                      >
                        {checked && <CheckIcon className="w-3 h-3 [stroke-width:3]" />}
                      </span>
                    </label>
                  )
                })}
              </div>
              <p className="mt-4 text-sm text-[var(--muted)]" aria-live="polite">
                {chosen.length} of {MODULE_META.length} selected
              </p>
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
                {addedCount > 0 && ` ${addedCount} of 3 added.`}
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
            <div className="mt-4">
              <InlineError>{hint}</InlineError>
            </div>
          )}
          {syncNote && (
            <p
              className="mt-4 flex items-start gap-2 rounded-lg bg-[var(--callout-yellow)] px-3 py-2.5 text-sm text-[var(--callout-yellow-text)]"
              role="status"
            >
              <AlertCircleIcon className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{syncNote}</span>
            </p>
          )}

          <div className="mt-8 pt-6 border-t border-[var(--rule)] flex flex-col-reverse gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-3">
            {step < 4 ? (
              <>
                <button type="button" onClick={skipStep} className={`${secondaryButtonClass} sm:-ml-3`}>
                  Skip this step
                </button>
                <button
                  type="button"
                  onClick={() => void nextStep()}
                  disabled={navBusy}
                  aria-busy={navBusy}
                  className={`${primaryButtonClass} w-full sm:w-auto`}
                >
                  {navBusy ? "Saving…" : "Continue"}
                  {!navBusy && <ArrowRightIcon className="w-4 h-4" />}
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
