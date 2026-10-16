import { Link } from 'react-router-dom'
import { CalendarDays, Clock, MapPin } from 'lucide-react'
import EmptyState from '../../components/ui/EmptyState'
import ErrorMessage from '../../components/common/ErrorMessage'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { useFetch } from '../../hooks/useFetch'
import { getStudentEvents } from '../../services/studentEventService'
import { formatDate, formatTime } from '../../utils/format'

export default function StudentEvents() {
  const { data: events, loading, error } = useFetch(getStudentEvents, [])
  return <div className="mx-auto max-w-6xl space-y-6">
    <PageHeader title="Events" description="Meet employers and learn about opportunities." actions={<Link to="/student/events/registrations" className="rounded-xl border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">My registrations</Link>} />
    {error && <ErrorMessage message={error} />}
    {loading ? <div className="grid grid-cols-1 gap-4 md:grid-cols-2"><Skeleton className="h-56 rounded-2xl" /><Skeleton className="h-56 rounded-2xl" /></div> : events?.length ? <div className="grid grid-cols-1 gap-4 md:grid-cols-2">{events.map((event) => <Link key={event.id} to={`/student/events/${event.id}`} className="block rounded-2xl border border-gray-200 bg-white p-5 shadow-card transition-shadow hover:shadow-card-hover"><div className="flex items-start justify-between gap-3"><span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-violet-50 text-violet-600"><CalendarDays size={20} aria-hidden="true" /></span>{event.registered && <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-800">Registered</span>}</div><h2 className="mt-4 text-lg font-semibold text-gray-900">{event.name}</h2><p className="mt-1 text-sm font-medium text-brand-700">{event.company_name}</p>{event.description && <p className="mt-3 line-clamp-2 text-sm text-gray-600">{event.description}</p>}<div className="mt-4 space-y-1.5 text-sm text-gray-500"><p>{formatDate(event.event_date)}{event.event_time && ` · ${formatTime(event.event_time)}`}</p>{event.location && <p className="flex items-center gap-1"><MapPin size={14} aria-hidden="true" /> {event.location}</p>}</div></Link>)}</div> : !error && <EmptyState icon={CalendarDays} title="No upcoming events" description="Check back soon for employer events." />}
  </div>
}
