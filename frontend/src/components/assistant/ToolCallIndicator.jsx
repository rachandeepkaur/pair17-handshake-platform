import { Wrench } from 'lucide-react'

const LABELS = {
  get_student_preferences: 'Checked your preferences',
  search_jobs: 'Searched jobs',
  get_job_details: 'Opened job details',
  search_events: 'Searched events',
  save_job_or_event: 'Save to your list',
}

const STATUS_NOTES = {
  cancelled: { text: 'cancelled by you', className: 'text-amber-700' },
  rejected: { text: 'invalid call, not run', className: 'text-red-600' },
  pending: { text: 'waiting for your approval', className: 'text-amber-700' },
}

function describe(args) {
  return Object.entries(args)
    .map(([key, value]) => `${key.replace(/_/g, ' ')}: ${value}`)
    .join(', ')
}

// Shows which tools produced an answer, so students can see where it came from.
export default function ToolCallIndicator({ calls }) {
  if (!calls?.length) return null

  return (
    <details className="mt-2 text-xs text-gray-500">
      <summary className="inline-flex cursor-pointer select-none items-center gap-1 rounded hover:text-gray-700">
        <Wrench size={12} aria-hidden="true" />
        Used {calls.length} {calls.length === 1 ? 'tool' : 'tools'}
      </summary>
      <ul className="mt-1.5 space-y-1">
        {calls.map((call, index) => (
          <li key={index} className="rounded-lg bg-white/70 px-2 py-1">
            <span className="font-medium text-gray-700">{LABELS[call.name] || call.name}</span>
            <span className="text-gray-400"> · {call.name}</span>
            {STATUS_NOTES[call.status] && (
              <span className={STATUS_NOTES[call.status].className}> · {STATUS_NOTES[call.status].text}</span>
            )}
            {Object.keys(call.arguments).length > 0 && <span className="block text-gray-500">{describe(call.arguments)}</span>}
          </li>
        ))}
      </ul>
    </details>
  )
}
