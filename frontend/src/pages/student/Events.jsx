import { useState } from 'react'
import { Link } from 'react-router-dom'
import { CalendarDays, MapPin, Search } from 'lucide-react'
import EmptyState from '../../components/ui/EmptyState'
import ErrorMessage from '../../components/common/ErrorMessage'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { useFetch } from '../../hooks/useFetch'
import { getStudentEvents } from '../../services/studentEventService'
import { formatDate, formatTime } from '../../utils/format'

export default function StudentEvents() {
  const [draft, setDraft] = useState('')
  const [query, setQuery] = useState('')
  const { data: events, loading, error } = useFetch(() => getStudentEvents({ q: query }), [query])

  const submit = (event) => {
    event.preventDefault()
    setQuery(draft.trim())
  }

  const clear = () => {
    setDraft('')
    setQuery('')
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Events"
        description="Meet employers and learn about opportunities."
        actions={<Link to="/student/events/registrations" className="rounded-xl border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">My registrations</Link>}
      />
    <form onSubmit={submit} className="flex flex-col gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-card sm:flex-row">
      <label className="relative flex-1">
        <span className="sr-only">Search events by name</span>
        <Search size={18} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Search events by name"
          className="h-10 w-full rounded-xl border border-gray-300 pl-10 pr-3 text-sm focus:border-brand-400"
        />
      </label>
      <div className="flex gap-2">
        <button type="submit" className="h-10 rounded-xl bg-brand-600 px-4 text-sm font-semibold text-white hover:bg-brand-700">Search</button>
        {query && <button type="button" onClick={clear} className="h-10 rounded-xl border border-gray-300 px-3 text-sm font-medium text-gray-700 hover:bg-gray-50">Clear</button>}
      </div>
    </form>
    {error && <ErrorMessage message={error} />}
    {loading ? (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Skeleton className="h-56 rounded-2xl" />
        <Skeleton className="h-56 rounded-2xl" />
      </div>
    ) : events?.length ? (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {events.map((event) => (
          <Link key={event.id} to={`/student/events/${event.id}`} className="block rounded-2xl border border-gray-200 bg-white p-5 shadow-card transition-shadow hover:shadow-card-hover">
            <div className="flex items-start justify-between gap-3">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-violet-50 text-violet-600"><CalendarDays size={20} aria-hidden="true" /></span>
              {event.registered && <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-800">Registered</span>}
            </div>
            <h2 className="mt-4 text-lg font-semibold text-gray-900">{event.name}</h2>
            <p className="mt-1 text-sm font-medium text-brand-700">{event.company_name}</p>
            {event.description && <p className="mt-3 line-clamp-2 text-sm text-gray-600">{event.description}</p>}
            <div className="mt-4 space-y-1.5 text-sm text-gray-500">
              <p>{formatDate(event.event_date)}{event.event_time && ` · ${formatTime(event.event_time)}`}</p>
              {event.location && <p className="flex items-center gap-1"><MapPin size={14} aria-hidden="true" /> {event.location}</p>}
            </div>
          </Link>
        ))}
      </div>
    ) : !error && (
      <EmptyState
        icon={CalendarDays}
        title={query ? "No matching events" : "No upcoming events"}
        description={query ? "Try a different event name." : "Check back soon for employer events."}
      />
    )}
    </div>
  )
}
