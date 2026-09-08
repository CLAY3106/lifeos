"use client"
import { useState, useMemo } from "react"
import useSWR from "swr"
import api from "@/lib/api"
import { ActivityIcon, PlusIcon, TrashIcon } from "@/components/icons"
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from "chart.js"
import { Bar } from "react-chartjs-2"
import { ListSkeleton } from "@/components/skeletons"
import toast from "react-hot-toast"

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

ChartJS.defaults.plugins.tooltip.backgroundColor = "rgb(24, 24, 27)"
ChartJS.defaults.plugins.tooltip.titleColor = "#fafafa"
ChartJS.defaults.plugins.tooltip.bodyColor = "#d4d4d8"
ChartJS.defaults.plugins.tooltip.borderColor = "#27272a"
ChartJS.defaults.plugins.tooltip.borderWidth = 1
ChartJS.defaults.plugins.tooltip.cornerRadius = 6
ChartJS.defaults.plugins.tooltip.padding = 10
ChartJS.defaults.plugins.tooltip.displayColors = true
ChartJS.defaults.plugins.tooltip.boxPadding = 4

const fetcher = (url: string) => api.get(url).then(r => r.data)

const WORKOUT_COLORS: Record<string, string> = {
  Run: "#3b82f6",
  Gym: "#22c55e",
  Yoga: "#a855f7",
  Basketball: "#eab308",
  Swimming: "#06b6d4",
  Cycling: "#f97316",
}

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

const inputClass =
  "border border-[var(--rule)] bg-[var(--surface)] text-[var(--foreground)] placeholder:text-[var(--muted-2)] rounded-md px-3 py-2.5 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:border-[var(--accent)] transition-colors"

type Tab = "workouts" | "routines"

export default function FitnessPage() {
  const [tab, setTab] = useState<Tab>("workouts")
  const { data: workouts, mutate: mutateWorkouts } = useSWR("/workouts", fetcher)
  const { data: routines, mutate: mutateRoutines } = useSWR("/routines", fetcher)

  // Workout form
  const [type, setType] = useState("")
  const [duration, setDuration] = useState("30")
  const [loading, setLoading] = useState(false)

  // Routine form
  const [routineName, setRoutineName] = useState("")
  const [routineLoading, setRoutineLoading] = useState(false)
  const [addingToRoutine, setAddingToRoutine] = useState<string | null>(null)
  const [itemName, setItemName] = useState("")
  const [itemSets, setItemSets] = useState("")
  const [itemReps, setItemReps] = useState("")
  const [itemDuration, setItemDuration] = useState("")
  const [itemDay, setItemDay] = useState("")
  const [itemLoading, setItemLoading] = useState(false)

  // Track which routine we're logging from
  const [loggingFromRoutine, setLoggingFromRoutine] = useState<any>(null)

  // Routine usage counts
  const routineUsage = useMemo(() => {
    if (!workouts) return {}
    const counts: Record<string, number> = {}
    for (const w of workouts) {
      if (w.routine_id) counts[w.routine_id] = (counts[w.routine_id] || 0) + 1
    }
    return counts
  }, [workouts])

  async function handleAddWorkout(routineId?: string) {
    if (!type) return
    setLoading(true)
    try {
      await api.post("/workouts", {
        type,
        duration_mins: parseInt(duration),
        routine_id: routineId || undefined,
      })
      setType("")
      setDuration("30")
      setLoggingFromRoutine(null)
      mutateWorkouts()
      toast.success("Workout logged")
    } finally {
      setLoading(false)
    }
  }

  function handleLogFromRoutine(routine: any) {
    setType(routine.name)
    setDuration("30")
    setLoggingFromRoutine(routine)
    setTab("workouts")
  }

  async function handleDeleteWorkout(id: string) {
    try {
      await api.delete(`/workouts/${id}`)
      mutateWorkouts()
      toast.success("Workout deleted")
    } catch {
      toast.error("Failed to delete workout")
    }
  }

  async function handleCreateRoutine() {
    if (!routineName.trim()) return
    setRoutineLoading(true)
    try {
      await api.post("/routines", { name: routineName.trim() })
      setRoutineName("")
      mutateRoutines()
      toast.success("Routine created")
    } finally {
      setRoutineLoading(false)
    }
  }

  async function handleAddItem(routineId: string) {
    if (!itemName.trim()) return
    setItemLoading(true)
    try {
      await api.post(`/routines/${routineId}/items`, {
        exercise_name: itemName.trim(),
        sets: itemSets ? parseInt(itemSets) : null,
        reps: itemReps ? parseInt(itemReps) : null,
        duration_mins: itemDuration ? parseInt(itemDuration) : null,
        day_of_week: itemDay || null,
      })
      setItemName("")
      setItemSets("")
      setItemReps("")
      setItemDuration("")
      setItemDay("")
      setAddingToRoutine(null)
      mutateRoutines()
      toast.success("Exercise added")
    } finally {
      setItemLoading(false)
    }
  }

  async function handleDeleteRoutine(id: string) {
    try {
      await api.delete(`/routines/${id}`)
      mutateRoutines()
      toast.success("Routine deleted")
    } catch {
      toast.error("Failed to delete routine")
    }
  }

  async function handleDeleteItem(routineId: string, itemId: string) {
    try {
      await api.delete(`/routines/${routineId}/items/${itemId}`)
      mutateRoutines()
      toast.success("Exercise removed")
    } catch {
      toast.error("Failed to remove exercise")
    }
  }

  // Weekly chart data
  const weeklyData = useMemo(() => {
    if (!workouts || workouts.length === 0) return null
    const now = new Date()
    const weeks: { label: string; totalMins: number }[] = []
    for (let i = 7; i >= 0; i--) {
      const weekStart = new Date(now)
      weekStart.setDate(weekStart.getDate() - (i * 7 + weekStart.getDay()))
      weekStart.setHours(0, 0, 0, 0)
      const weekEnd = new Date(weekStart)
      weekEnd.setDate(weekEnd.getDate() + 7)
      const wos = workouts.filter((w: any) => {
        const d = new Date(w.logged_at)
        return d >= weekStart && d < weekEnd
      })
      weeks.push({
        label: weekStart.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
        totalMins: wos.reduce((sum: number, w: any) => sum + w.duration_mins, 0),
      })
    }
    return weeks
  }, [workouts])

  const typeBreakdown = useMemo(() => {
    if (!workouts || workouts.length === 0) return {}
    const counts: Record<string, number> = {}
    for (const w of workouts) counts[w.type] = (counts[w.type] || 0) + 1
    return counts
  }, [workouts])

  const barData = weeklyData ? {
    labels: weeklyData.map(w => w.label),
    datasets: [{ label: "Minutes", data: weeklyData.map(w => w.totalMins), backgroundColor: "#22c55e", borderRadius: 4 }],
  } : null

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { color: "#a1a1aa", font: { size: 10 } } },
      y: { grid: { color: "#27272a" }, ticks: { color: "#a1a1aa", font: { size: 10 }, callback: (v: any) => `${v}m` } },
    },
  }

  const totalMins = workouts?.reduce((sum: number, w: any) => sum + w.duration_mins, 0) ?? 0

  return (
    <div className="max-w-3xl mx-auto px-16 py-16">
      <div className="flex items-center gap-2.5 mb-6">
        <div className="w-10 h-10 rounded-lg bg-[var(--callout-green)] flex items-center justify-center shrink-0">
          <ActivityIcon className="w-5 h-5 text-[var(--foreground)]" />
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-[var(--foreground)]">Fitness</h1>
      </div>

      {/* Sub-tabs */}
      <div className="flex gap-1 mb-8 border-b border-[var(--rule)]">
        <button
          onClick={() => setTab("workouts")}
          className={`px-4 py-2 text-sm font-medium cursor-pointer transition-colors border-b-2 -mb-px ${
            tab === "workouts"
              ? "border-[var(--accent)] text-[var(--foreground)]"
              : "border-transparent text-[var(--muted)] hover:text-[var(--foreground)]"
          }`}
        >
          Workouts
        </button>
        <button
          onClick={() => setTab("routines")}
          className={`px-4 py-2 text-sm font-medium cursor-pointer transition-colors border-b-2 -mb-px ${
            tab === "routines"
              ? "border-[var(--accent)] text-[var(--foreground)]"
              : "border-transparent text-[var(--muted)] hover:text-[var(--foreground)]"
          }`}
        >
          Routines
        </button>
      </div>

      {/* ===== WORKOUTS TAB ===== */}
      {tab === "workouts" && (
        <>
          {/* Stats */}
          {workouts && workouts.length > 0 && (
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-4 shadow-sm">
                <p className="text-xs font-medium text-[var(--muted)] uppercase tracking-wide">Total Workouts</p>
                <p className="text-3xl font-bold text-[var(--foreground)] tabular-nums mt-0.5">{workouts.length}</p>
              </div>
              <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-4 shadow-sm">
                <p className="text-xs font-medium text-[var(--muted)] uppercase tracking-wide">Total Time</p>
                <p className="text-3xl font-bold text-[var(--foreground)] tabular-nums mt-0.5">
                  {totalMins >= 60 ? `${Math.floor(totalMins / 60)}h ${totalMins % 60}m` : `${totalMins}m`}
                </p>
              </div>
            </div>
          )}

          {/* Charts */}
          {workouts && workouts.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-[1fr_200px] gap-4 mb-6">
              <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-4 shadow-sm">
                <p className="text-xs font-medium text-[var(--muted)] uppercase tracking-wide mb-3">Weekly Volume (8 weeks)</p>
                <div className="h-48"><Bar data={barData!} options={barOptions} /></div>
              </div>
              <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-4 shadow-sm">
                <p className="text-xs font-medium text-[var(--muted)] uppercase tracking-wide mb-3">By Type</p>
                <div className="space-y-2">
                  {Object.entries(typeBreakdown)
                    .sort(([, a], [, b]) => (b as number) - (a as number))
                    .map(([t, count]) => (
                      <div key={t} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: WORKOUT_COLORS[t] || "#9ca3af" }} />
                          <span className="text-sm text-[var(--foreground)]">{t}</span>
                        </div>
                        <span className="text-sm text-[var(--muted)] tabular-nums">{count as number}</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          )}

          {/* Add Form */}
          <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-xl p-6 shadow-sm mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-[var(--foreground)]">Log Workout</h2>
              {loggingFromRoutine && (
                <span className="text-xs text-[var(--accent)]">
                  From routine: {loggingFromRoutine.name}
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <input
                placeholder="Type (e.g. Run, Gym, Yoga) *"
                value={type}
                onChange={e => setType(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleAddWorkout()}
                className={`${inputClass} col-span-2`}
              />
              <input
                type="number"
                placeholder="Duration (minutes)"
                value={duration}
                onChange={e => setDuration(e.target.value)}
                className={inputClass}
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleAddWorkout(loggingFromRoutine?.id)}
                disabled={loading}
                className="bg-[var(--accent)] text-white px-4 py-2 rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-opacity"
              >
                {loading ? "Adding..." : "Log Workout"}
              </button>
              {loggingFromRoutine && (
                <button
                  onClick={() => { setLoggingFromRoutine(null); setType(""); }}
                  className="text-xs text-[var(--muted)] hover:text-[var(--foreground)] cursor-pointer transition-colors px-3"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Workout List */}
          <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-xl shadow-sm divide-y divide-[var(--rule)] overflow-hidden">
            {!workouts ? (
              <div className="p-4"><ListSkeleton count={3} /></div>
            ) : workouts.length === 0 ? (
              <div className="p-10 flex flex-col items-center text-center gap-2">
                <ActivityIcon className="w-6 h-6 text-[var(--muted-2)]" />
                <p className="text-sm text-[var(--muted-2)]">No workouts yet. Log one above.</p>
              </div>
            ) : (
              workouts.map((w: any) => (
                <div key={w.id} className="p-4 flex items-center justify-between gap-4 hover:bg-[var(--surface-hover)] transition-colors">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: WORKOUT_COLORS[w.type] || "#9ca3af" }} />
                      <p className="font-medium text-sm text-[var(--foreground)] truncate">{w.type}</p>
                      {w.routine_id && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--callout-blue)] text-[var(--foreground)]">
                          routine
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-[var(--muted-2)] mt-0.5">
                      {w.duration_mins} min · {new Date(w.logged_at).toLocaleDateString()}
                    </p>
                  </div>
                  <button onClick={() => handleDeleteWorkout(w.id)} className="text-xs text-[var(--danger)] hover:opacity-75 cursor-pointer transition-opacity shrink-0">
                    Delete
                  </button>
                </div>
              ))
            )}
          </div>
        </>
      )}

      {/* ===== ROUTINES TAB ===== */}
      {tab === "routines" && (
        <>
          {/* Create Routine */}
          <div className="bg-[var(--surface)] rounded-lg p-6 shadow-sm border border-[var(--rule)] mb-8">
            <h2 className="text-sm font-semibold text-[var(--foreground)] mb-4">New Routine</h2>
            <div className="flex gap-3">
              <input
                placeholder="Routine name (e.g. Push Day) *"
                value={routineName}
                onChange={e => setRoutineName(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleCreateRoutine()}
                className={`${inputClass} flex-1`}
              />
              <button
                onClick={handleCreateRoutine}
                disabled={routineLoading}
                className="bg-[var(--accent)] text-white px-4 py-2 rounded-md text-sm font-medium cursor-pointer transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {routineLoading ? "Creating..." : "Create"}
              </button>
            </div>
          </div>

          {/* Routines List */}
          <div className="space-y-4">
            {!routines ? (
              <ListSkeleton count={2} />
            ) : routines.length === 0 ? (
              <div className="bg-[var(--surface)] rounded-lg border border-dashed border-[var(--rule)] py-12 text-center">
                <ActivityIcon className="w-8 h-8 mx-auto mb-3 text-[var(--muted-2)]" />
                <p className="text-sm text-[var(--muted)]">No routines yet. Create one above.</p>
              </div>
            ) : (
              routines.map((routine: any) => (
                <div key={routine.id} className="bg-[var(--surface)] rounded-lg border border-[var(--rule)] shadow-sm overflow-hidden">
                  <div className="px-5 py-4 flex items-center justify-between border-b border-[var(--rule)]">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-[var(--foreground)]">{routine.name}</h3>
                        {routineUsage[routine.id] > 0 && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--callout-green)] text-[var(--foreground)] tabular-nums">
                            {routineUsage[routine.id]}x logged
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[var(--muted)] mt-0.5">
                        {routine.items.length} exercise{routine.items.length !== 1 ? "s" : ""}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleLogFromRoutine(routine)}
                        className="text-xs bg-[var(--accent)] text-white px-3 py-1.5 rounded-md font-medium cursor-pointer transition-opacity hover:opacity-90 flex items-center gap-1"
                      >
                        <ActivityIcon className="w-3 h-3" />
                        Log Workout
                      </button>
                      <button
                        onClick={() => setAddingToRoutine(addingToRoutine === routine.id ? null : routine.id)}
                        className="text-xs text-[var(--accent)] hover:opacity-80 cursor-pointer transition-opacity flex items-center gap-1"
                      >
                        <PlusIcon className="w-3.5 h-3.5" />
                        Exercise
                      </button>
                      <button
                        onClick={() => handleDeleteRoutine(routine.id)}
                        className="p-1.5 rounded-md text-[var(--muted-2)] hover:text-[var(--danger)] hover:bg-[var(--callout-red)] cursor-pointer transition-colors"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {addingToRoutine === routine.id && (
                    <div className="px-5 py-4 bg-[var(--callout-gray)] border-b border-[var(--rule)]">
                      <div className="grid grid-cols-2 gap-2 mb-3">
                        <input placeholder="Exercise name *" value={itemName} onChange={e => setItemName(e.target.value)} className={`${inputClass} col-span-2`} />
                        <input type="number" placeholder="Sets" value={itemSets} onChange={e => setItemSets(e.target.value)} className={inputClass} />
                        <input type="number" placeholder="Reps" value={itemReps} onChange={e => setItemReps(e.target.value)} className={inputClass} />
                        <input type="number" placeholder="Duration (min)" value={itemDuration} onChange={e => setItemDuration(e.target.value)} className={inputClass} />
                        <select value={itemDay} onChange={e => setItemDay(e.target.value)} className={inputClass}>
                          <option value="">Any day</option>
                          {DAYS.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
                        </select>
                      </div>
                      <div className="flex gap-2">
                        <button onClick={() => handleAddItem(routine.id)} disabled={itemLoading} className="bg-[var(--accent)] text-white px-3 py-1.5 rounded-md text-xs font-medium cursor-pointer transition-opacity hover:opacity-90 disabled:opacity-50">
                          {itemLoading ? "Adding..." : "Add"}
                        </button>
                        <button onClick={() => setAddingToRoutine(null)} className="text-xs text-[var(--muted)] hover:text-[var(--foreground)] cursor-pointer transition-colors">
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}

                  {routine.items.length === 0 ? (
                    <div className="px-5 py-6 text-center">
                      <p className="text-sm text-[var(--muted-2)]">No exercises yet.</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-[var(--rule)]">
                      {routine.items.map((item: any) => (
                        <div key={item.id} className="px-5 py-3 flex items-center justify-between hover:bg-[var(--surface-hover)] transition-colors">
                          <div className="min-w-0">
                            <p className="font-medium text-sm text-[var(--foreground)]">{item.exercise_name}</p>
                            <p className="text-xs text-[var(--muted-2)] mt-0.5">
                              {[
                                item.sets && item.reps ? `${item.sets}x${item.reps}` : null,
                                item.duration_mins && `${item.duration_mins} min`,
                                item.day_of_week && item.day_of_week.charAt(0).toUpperCase() + item.day_of_week.slice(1),
                              ].filter(Boolean).join(" · ")}
                            </p>
                          </div>
                          <button onClick={() => handleDeleteItem(routine.id, item.id)} className="text-xs text-[var(--muted-2)] hover:text-[var(--danger)] cursor-pointer transition-colors shrink-0">
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  )
}
