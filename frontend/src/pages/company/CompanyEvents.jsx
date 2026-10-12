import { useState } from 'react'
import { Link } from 'react-router-dom'
import { CalendarDays, CalendarPlus, Clock, MapPin, Users } from 'lucide-react'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import PageHeader from '../../components/ui/PageHeader'
import StatusBadge from '../../components/ui/StatusBadge'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import Tabs from '../../components/ui/Tabs'
import ErrorMessage from '../../components/common/ErrorMessage'
import { useFetch } from '../../hooks/useFetch'
import { getMyEvents } from '../../services/eventService'
import { formatDate, formatTime, isOnOrAfterToday } from '../../utils/format'

function EventCard({ event }) {
  const upcoming = isOnOrAfterToday(event.event_date)
  return (
    <Link to={`/company/events/${event.id}`} className="block rounded-2xl">
      <Card className="flex h-full flex-col p-5 transition-shadow hover:shadow-card-hover">
        <div className="flex items-start justify-between gap-2">
          <span className="rounded-lg bg-accent-50 px-2 py-1 text-xs font-semibold text-accent-700">
            {formatDate(event.event_date)}
          </span>
          <StatusBadge status={upcoming ? 'Upcoming' : 'Past'} />
        </div>
        <h2 className="mt-3 font-semibold text-gray-900">{event.name}</h2>
        {event.description && <p className="mt-1 line-clamp-2 text-sm text-gray-600">{event.description}</p>}
        <div className="mt-auto space-y-1.5 pt-4 text-sm text-gray-600">
          {event.event_time && (
            <p className="flex items-center gap-1.5">
              <Clock size={14} className="text-gray-400" aria-hidden="true" /> {formatTime(event.event_time)}
            </p>
          )}
          {event.location && (
            <p className="flex items-center gap-1.5">
              <MapPin size={14} className="text-gray-400" aria-hidden="true" /> {event.location}
            </p>
          )}
          <p className="flex items-center gap-1.5 font-medium text-accent-700">
            <Users size={14} aria-hidden="true" /> {event.registration_count} registered
          </p>
        </div>
      </Card>
    </Link>
  )
}

export default function CompanyEvents() {
  const { data, loading, error } = useFetch(getMyEvents, [])
  const [tab, setTab] = useState('upcoming')

  const events = data || []
  const upcoming = events.filter((event) => isOnOrAfterToday(event.event_date))
  // Past events read most-recent first; upcoming soonest first (API order).
  const past = events.filter((event) => !isOnOrAfterToday(event.event_date)).reverse()
  const visible = tab === 'upcoming' ? upcoming : past

  return (
    <div className="space-y-5">
      <PageHeader
        title="Events"
        description="Host events and see which students registered."
        actions={
          <Button as={Link} to="/company/events/new" variant="secondary" icon={CalendarPlus}>
            Create Event
          </Button>
        }
      />

      <Tabs
        label="Event timing"
        value={tab}
        onChange={setTab}
        tabs={[
          { value: 'upcoming', label: 'Upcoming', count: data ? upcoming.length : undefined },
          { value: 'past', label: 'Past', count: data ? past.length : undefined },
        ]}
      />

      <ErrorMessage message={error} />

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-2xl" />
          ))}
        </div>
      ) : visible.length === 0 ? (
        <EmptyState
          icon={CalendarDays}
          title={tab === 'upcoming' ? 'No upcoming events' : 'No past events'}
          description={tab === 'upcoming' ? 'Create an event to meet qualified students.' : 'Events appear here after their date passes.'}
          action={
            tab === 'upcoming' && (
              <Button as={Link} to="/company/events/new" variant="secondary" icon={CalendarPlus}>
                Create Event
              </Button>
            )
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {visible.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      )}
    </div>
  )
}
