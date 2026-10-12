import { useParams } from 'react-router-dom'
import { CalendarDays, Clock, MapPin, ShieldCheck, Users } from 'lucide-react'
import Card, { CardHeader } from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'
import StatusBadge from '../../components/ui/StatusBadge'
import Skeleton, { RowSkeleton } from '../../components/ui/Skeleton'
import ErrorMessage from '../../components/common/ErrorMessage'
import RegistrantList from '../../components/events/RegistrantList'
import { useFetch } from '../../hooks/useFetch'
import { getEvent, getEventRegistrations } from '../../services/eventService'
import { formatDate, formatTime, isOnOrAfterToday } from '../../utils/format'

function Fact({ icon: Icon, label, children }) {
  return (
    <div className="flex items-start gap-3">
      <Icon size={18} className="mt-0.5 shrink-0 text-gray-400" aria-hidden="true" />
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p>
        <p className="text-sm text-gray-900">{children || '—'}</p>
      </div>
    </div>
  )
}

export default function EventRegistrations() {
  const { eventId } = useParams()
  const event = useFetch(() => getEvent(eventId), [eventId])
  const registrations = useFetch(() => getEventRegistrations(eventId), [eventId])

  if (event.error) {
    return (
      <div className="space-y-4">
        <PageHeader title="Event not found" backTo="/company/events" backLabel="Back to events" />
        <ErrorMessage message={event.error} />
      </div>
    )
  }

  const data = event.data
  return (
    <div className="space-y-6">
      <PageHeader
        title={data ? data.name : <Skeleton className="h-8 w-64" />}
        backTo="/company/events"
        backLabel="Back to events"
        actions={data && <StatusBadge status={isOnOrAfterToday(data.event_date) ? 'Upcoming' : 'Past'} />}
      />

      {data && (
        <Card className="p-5">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <Fact icon={CalendarDays} label="Date">
              {formatDate(data.event_date)}
            </Fact>
            <Fact icon={Clock} label="Time">
              {formatTime(data.event_time)}
            </Fact>
            <Fact icon={MapPin} label="Location">
              {data.location}
            </Fact>
            <Fact icon={ShieldCheck} label="Eligibility">
              {data.eligibility || 'All students'}
            </Fact>
          </div>
          {data.description && (
            <p className="mt-5 whitespace-pre-line border-t border-gray-100 pt-4 text-sm text-gray-700">
              {data.description}
            </p>
          )}
        </Card>
      )}

      <Card className="overflow-hidden">
        <CardHeader
          title="Registered students"
          subtitle={registrations.data && `${registrations.data.length} registered`}
          action={<Users size={18} className="text-gray-400" aria-hidden="true" />}
        />
        <ErrorMessage message={registrations.error} />
        {registrations.loading ? (
          <div className="px-5">
            <RowSkeleton />
            <RowSkeleton />
          </div>
        ) : (
          registrations.data && <RegistrantList registrations={registrations.data} />
        )}
      </Card>
    </div>
  )
}
