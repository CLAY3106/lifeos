export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse bg-[var(--callout-gray)] rounded ${className}`}
      aria-hidden="true"
    />
  )
}

export function CardSkeleton() {
  return (
    <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-4 shadow-sm space-y-3">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-3 w-2/3" />
      <Skeleton className="h-3 w-1/2" />
    </div>
  )
}

export function ListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-[var(--surface)] border border-[var(--rule)] rounded-md p-4 flex items-center gap-3"
        >
          <Skeleton className="h-5 w-5 rounded-full shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3.5 w-1/3" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <Skeleton className="h-6 w-16 rounded" />
        </div>
      ))}
    </div>
  )
}

export function DashboardSkeleton() {
  return (
    <div className="max-w-5xl mx-auto px-16">
      <div className="h-28 bg-[var(--callout-gray)] rounded-t-lg" />
      <div className="-mt-8 space-y-6">
        <Skeleton className="w-11 h-11 rounded-full" />
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-4 w-40" />
        <CardSkeleton />
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8">
          <CardSkeleton />
          <div className="space-y-3">
            <Skeleton className="h-3 w-20" />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </div>
        </div>
      </div>
    </div>
  )
}

export function KanbanSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="bg-[var(--surface)] rounded-lg border border-[var(--rule)] flex flex-col">
          <div className="p-3 border-b border-[var(--rule)] bg-[var(--callout-gray)] rounded-t-lg">
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
          <div className="p-3 space-y-2">
            <Skeleton className="h-20 rounded-md" />
            <Skeleton className="h-20 rounded-md" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="border border-[var(--rule)] rounded-md overflow-hidden">
      <div className="grid grid-cols-[24px_1fr_120px_100px_100px] gap-3 px-3 py-2 bg-[var(--callout-gray)]">
        <Skeleton className="h-3 w-3" />
        <Skeleton className="h-3 w-1/3" />
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-12" />
        <Skeleton className="h-3 w-12" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="grid grid-cols-[24px_1fr_120px_100px_100px] gap-3 px-3 py-2.5 border-b border-[var(--rule)] last:border-b-0">
          <Skeleton className="h-4 w-4 rounded-full" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-8" />
          <Skeleton className="h-4 w-10" />
        </div>
      ))}
    </div>
  )
}
