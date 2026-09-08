"use client"
import useSWR from "swr"
import api from "@/lib/api"
import { BookIcon } from "@/components/icons"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import toast from "react-hot-toast"
import { TableSkeleton } from "@/components/skeletons"

const fetcher = (url: string) => api.get(url).then(r => r.data)

const assignmentSchema = z.object({
  title: z.string().min(1, "Title is required"),
  course: z.string().optional(),
  dueDate: z.string().min(1, "Due date is required"),
  hours: z.string().refine((val) => {
    const num = Number(val)
    return !isNaN(num) && num >= 0.5 && num <= 100
  }, "Must be between 0.5 and 100 hours"),
})

type AssignmentForm = z.infer<typeof assignmentSchema>

const STATUS_STYLES: Record<string, string> = {
  pending: "text-[var(--foreground)]",
  done: "text-[var(--muted-2)]",
  overdue: "text-[var(--danger)]",
}

function ProgressRing({ complete }: { complete: boolean }) {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" className="shrink-0">
      <circle cx="9" cy="9" r="7" fill="none" stroke="var(--rule)" strokeWidth="2" />
      {complete ? (
        <circle cx="9" cy="9" r="7" fill="var(--accent)" stroke="var(--accent)" strokeWidth="2" />
      ) : (
        <circle
          cx="9" cy="9" r="7" fill="none" stroke="var(--accent)" strokeWidth="2"
          strokeDasharray="44" strokeDashoffset="11"
        />
      )}
    </svg>
  )
}

export default function AssignmentsPage() {
  const { data, mutate } = useSWR("/assignments", fetcher)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AssignmentForm>({
    resolver: zodResolver(assignmentSchema),
    defaultValues: { title: "", course: "", dueDate: "", hours: "1" },
  })

  async function onSubmit(values: AssignmentForm) {
    try {
      await api.post("/assignments", {
        title: values.title,
        course: values.course || undefined,
        due_date: new Date(values.dueDate).toISOString(),
        estimated_hours: parseFloat(values.hours),
      })
      reset()
      mutate()
      toast.success("Assignment added")
    } catch {
      toast.error("Failed to add assignment")
    }
  }

  async function handleDelete(id: string) {
    try {
      await api.delete(`/assignments/${id}`)
      mutate()
      toast.success("Assignment deleted")
    } catch {
      toast.error("Failed to delete assignment")
    }
  }

  async function handleStatusChange(id: string, status: string) {
    try {
      await api.patch(`/assignments/${id}`, { status })
      mutate()
      toast.success("Status updated")
    } catch {
      toast.error("Failed to update status")
    }
  }

  const inputClass =
    "border border-[var(--rule)] bg-[var(--surface)] text-[var(--foreground)] placeholder:text-[var(--muted-2)] rounded px-3 py-2 text-sm outline-none transition-colors focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/25"
  const errorClass = "border-[var(--danger)]"

  return (
    <div className="max-w-3xl mx-auto px-16 py-16">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-lg bg-[var(--callout-blue)] flex items-center justify-center shrink-0">
          <BookIcon className="w-5 h-5 text-[var(--foreground)]" />
        </div>
        <h1 className="text-2xl font-bold text-[var(--foreground)]">Assignments</h1>
      </div>

      {/* Add Form */}
      <div className="bg-[var(--surface)] rounded-lg p-6 shadow-sm border border-[var(--rule)] mb-8">
        <h2 className="text-sm font-semibold text-[var(--foreground)] mb-4">Add Assignment</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-2 gap-3 mb-4">
          <div className="col-span-2">
            <input
              placeholder="Title *"
              {...register("title")}
              className={`${inputClass} w-full ${errors.title ? errorClass : ""}`}
            />
            {errors.title && (
              <p className="text-xs text-[var(--danger)] mt-1">{errors.title.message}</p>
            )}
          </div>
          <div>
            <input
              placeholder="Course"
              {...register("course")}
              className={`${inputClass} w-full`}
            />
          </div>
          <div>
            <input
              type="number"
              step="0.5"
              placeholder="Estimated hours"
              {...register("hours")}
              className={`${inputClass} w-full ${errors.hours ? errorClass : ""}`}
            />
            {errors.hours && (
              <p className="text-xs text-[var(--danger)] mt-1">{errors.hours.message}</p>
            )}
          </div>
          <div className="col-span-2">
            <input
              type="datetime-local"
              {...register("dueDate")}
              className={`${inputClass} w-full ${errors.dueDate ? errorClass : ""}`}
            />
            {errors.dueDate && (
              <p className="text-xs text-[var(--danger)] mt-1">{errors.dueDate.message}</p>
            )}
          </div>
          <div className="col-span-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-[var(--accent)] text-white px-4 py-2 rounded-md text-sm font-medium cursor-pointer transition-opacity hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-offset-2 focus:ring-offset-[var(--surface)]"
            >
              {isSubmitting ? "Adding..." : "Add Assignment"}
            </button>
          </div>
        </form>
      </div>

      {/* Assignment List */}
      <div className="bg-[var(--surface)] rounded-lg shadow-sm border border-[var(--rule)] divide-y divide-[var(--rule)]">
        {!data ? (
          <div className="p-4"><TableSkeleton rows={4} /></div>
        ) : data.length === 0 ? (
          <p className="p-6 text-sm text-[var(--muted-2)]">No assignments yet. Add one above.</p>
        ) : (
          data.map((a: any) => (
            <div
              key={a.id}
              className={`p-4 flex items-center justify-between gap-4 transition-colors hover:bg-[var(--surface-hover)] ${
                a.status === "done" ? "opacity-50" : ""
              }`}
            >
              <div className="flex items-center gap-3 min-w-0">
                <ProgressRing complete={a.status === "done"} />
                <div className="min-w-0">
                  <p
                    className={`font-medium text-sm truncate ${
                      a.status === "done" ? "line-through text-[var(--muted-2)]" : "text-[var(--foreground)]"
                    }`}
                  >
                    {a.title}
                  </p>
                  <p className="text-xs text-[var(--muted-2)] mt-0.5">
                    {a.course && `${a.course} · `}
                    Due {new Date(a.due_date).toLocaleDateString()} · {a.estimated_hours}h
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <select
                  value={a.status}
                  onChange={e => handleStatusChange(a.id, e.target.value)}
                  className={`text-xs border border-[var(--rule)] bg-[var(--surface)] rounded px-2 py-1 cursor-pointer outline-none transition-colors focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/25 ${
                    STATUS_STYLES[a.status] ?? "text-[var(--foreground)]"
                  }`}
                >
                  <option value="pending">Pending</option>
                  <option value="done">Done</option>
                  <option value="overdue">Overdue</option>
                </select>
                <button
                  onClick={() => handleDelete(a.id)}
                  className="text-xs text-[var(--muted-2)] hover:text-[var(--danger)] cursor-pointer transition-colors outline-none focus:text-[var(--danger)] focus:ring-2 focus:ring-[var(--accent)]/25 rounded px-1 py-0.5"
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
