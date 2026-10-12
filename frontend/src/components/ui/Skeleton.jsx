export default function Skeleton({ className = '' }) {
  return <div className={`skeleton rounded-md ${className}`} />
}

export function StatCardSkeleton() {
  return (
    <div className="rounded-2xl border border-gray-200/80 bg-white p-5 shadow-card">
      <Skeleton className="h-9 w-9 rounded-xl" />
      <Skeleton className="mt-4 h-7 w-16" />
      <Skeleton className="mt-2 h-4 w-24" />
    </div>
  )
}

export function RowSkeleton() {
  return (
    <div className="flex items-center gap-3 py-3">
      <Skeleton className="h-10 w-10 rounded-full" />
      <div className="flex-1">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="mt-2 h-3 w-24" />
      </div>
      <Skeleton className="h-6 w-20 rounded-full" />
    </div>
  )
}
