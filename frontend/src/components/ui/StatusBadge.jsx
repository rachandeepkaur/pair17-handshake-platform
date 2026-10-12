// Each status pairs a color with a dot and a text label, so state is never
// communicated by color alone.
const STATUSES = {
  Pending: { dot: 'bg-amber-500', cls: 'bg-amber-50 text-amber-800' },
  Reviewed: { dot: 'bg-brand-500', cls: 'bg-brand-50 text-brand-700' },
  Declined: { dot: 'bg-red-500', cls: 'bg-red-50 text-red-700' },
  Active: { dot: 'bg-emerald-500', cls: 'bg-emerald-50 text-emerald-700' },
  Closed: { dot: 'bg-gray-400', cls: 'bg-gray-100 text-gray-600' },
  Upcoming: { dot: 'bg-accent-500', cls: 'bg-accent-50 text-accent-700' },
  Past: { dot: 'bg-gray-400', cls: 'bg-gray-100 text-gray-600' },
}

export default function StatusBadge({ status }) {
  const config = STATUSES[status] || STATUSES.Closed
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-medium ${config.cls}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${config.dot}`} aria-hidden="true" />
      {status}
    </span>
  )
}
