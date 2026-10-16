import { Link } from 'react-router-dom'
import { CalendarCheck2 } from 'lucide-react'
import EmptyState from '../../components/ui/EmptyState'
import ErrorMessage from '../../components/common/ErrorMessage'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { useFetch } from '../../hooks/useFetch'
import { getMyRegistrations } from '../../services/studentEventService'
import { formatDate, formatDateTime, formatTime } from '../../utils/format'

export default function RegisteredEvents() {
  const { data: registrations, loading, error } = useFetch(getMyRegistrations, [])
  return <div className="mx-auto max-w-5xl space-y-6">
    <PageHeader title="My event registrations" description="Events you have registered to attend." backTo="/student/events" backLabel="Browse events" />
    {error && <ErrorMessage message={error} />}
    {loading ? <Skeleton className="h-56 rounded-2xl" /> : registrations?.length ? <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-card"><ul className="divide-y divide-gray-100">{registrations.map(({ id, registered_at: registeredAt, event }) => <li key={id}><Link to={`/student/events/${event.id}`} className="block px-5 py-4 hover:bg-gray-50"><p className="font-medium text-gray-900">{event.name}</p><p className="mt-1 text-sm text-gray-600">{event.company_name} · {formatDate(event.event_date)}{event.event_time && ` · ${formatTime(event.event_time)}`}</p><p className="mt-1 text-xs text-gray-500">Registered {formatDateTime(registeredAt)}</p></Link></li>)}</ul></div> : !error && <EmptyState icon={CalendarCheck2} title="No event registrations" description="Browse employer events to register." action={<Link to="/student/events" className="text-sm font-semibold text-brand-600 hover:text-brand-700">Browse events</Link>} />}
  </div>
}
