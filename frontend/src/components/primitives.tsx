export type IconType = React.ComponentType<{ className?: string }>

export type CalloutTone = "gray" | "green" | "yellow" | "red" | "blue" | "purple"

export const toneBg: Record<CalloutTone, string> = {
  gray: "bg-[var(--callout-gray)]",
  green: "bg-[var(--callout-green)]",
  yellow: "bg-[var(--callout-yellow)]",
  red: "bg-[var(--callout-red)]",
  blue: "bg-[var(--callout-blue)]",
  purple: "bg-[var(--callout-purple)]",
}

export function Callout({
  tone,
  icon: Icon,
  children,
  className = "",
}: {
  tone: CalloutTone
  icon: IconType
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`${toneBg[tone]} rounded-md p-4 flex gap-3 ${className}`}>
      <Icon className="w-5 h-5 shrink-0 mt-0.5 text-[var(--accent)]" />
      {children}
    </div>
  )
}

export function StatCallout({
  icon: Icon,
  tone,
  label,
  value,
  context,
  meter,
  alert,
}: {
  icon: IconType
  tone: CalloutTone
  label: string
  value: string | number
  context: string
  meter?: number
  alert?: boolean
}) {
  return (
    <div className={`${toneBg[tone]} rounded-md p-3.5`}>
      <div className="flex items-start gap-2.5">
        <Icon
          className={`w-[18px] h-[18px] shrink-0 mt-0.5 ${
            alert ? "text-[var(--danger)]" : "text-[var(--muted)]"
          }`}
        />
        <div className="flex-1 min-w-0">
          <p className="text-[11px] font-medium text-[var(--muted)] uppercase tracking-wide">
            {label}
          </p>
          <div className="flex items-baseline gap-1.5 mt-0.5">
            <span
              className={`text-2xl font-semibold tabular-nums ${
                alert ? "text-[var(--danger)]" : "text-[var(--foreground)]"
              }`}
            >
              {value}
            </span>
            <span className="text-xs text-[var(--muted)]">{context}</span>
          </div>
          {meter !== undefined && (
            <div className="mt-2 h-1 w-full bg-[var(--rule)] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-[width] duration-300 ${
                  alert ? "bg-[var(--danger)]" : "bg-[var(--accent)]"
                }`}
                style={{ width: `${Math.min(meter, 100)}%` }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function SectionHeading({
  icon: Icon,
  title,
  count,
}: {
  icon: IconType
  title: string
  count?: number
}) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <Icon className="w-4 h-4 text-[var(--muted)]" />
      <h2 className="text-base font-semibold text-[var(--foreground)]">{title}</h2>
      {count !== undefined && (
        <span className="text-xs text-[var(--muted-2)]">· {count}</span>
      )}
    </div>
  )
}

export function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-[var(--callout-gray)] text-[var(--foreground)] w-fit">
      {children}
    </span>
  )
}

export function EmptyRow({ icon: Icon, text }: { icon: IconType; text: string }) {
  return (
    <div className="border border-dashed border-[var(--rule)] rounded-md py-8 text-center">
      <Icon className="w-7 h-7 mx-auto mb-2 text-[var(--muted-2)]" />
      <p className="text-sm text-[var(--muted)]">{text}</p>
    </div>
  )
}
