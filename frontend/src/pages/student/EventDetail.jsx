import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { CalendarDays, Clock, MapPin } from 'lucide-react'
import Button from '../../components/ui/Button'
import ErrorMessage from '../../components/common/ErrorMessage'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { useFetch } from '../../hooks/useFetch'
import { getStudentEvent, registerForEvent } from '../../services/studentEventService'
import { errorMessage } from '../../services/api'
import { formatDate, formatTime } from '../../utils/format'

export default function StudentEventDetail() {
  const { eventId } = useParams()
  const { data: event, loading, error, setData } = useFetch(() => getStudentEvent(eventId), [eventId])
  const [submitting, setSubmitting] = useState(false)
  const [registerError, setRegisterError] = useState('')
  const register = async () => {
    setSubmitting(true)
    setRegisterError('')
    try {
      const registration = await registerForEvent(eventId)
      setData(registration.event)
    } catch (err) {
      setRegisterError(errorMessage(err, 'Could not register for this event.'))
    } finally {
      setSubmitting(false)
    }
  }
  if (loading) return <Skeleton className="h-96 rounded-2xl" />
  if (error || !event) return <div className="space-y-4"><PageHeader title="Event not found" backTo="/student/events" backLabel="Back to events" /><ErrorMessage message={error || 'Event not found'} /></div>
  return <div className="mx-auto max-w-4xl space-y-6">
    <PageHeader title={event.name} description={event.company_name} backTo="/student/events" backLabel="Back to events" actions={event.registered ? <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-800">Registered</span> : <Button onClick={register} disabled={submitting || !event.eligible}>{submitting ? 'Registering…' : event.eligible ? 'Register' : 'Not eligible'}</Button>} />
    {registerError && <ErrorMessage message={registerError} />}
    {event.registered && <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">You are registered for this event. <Link to="/student/events/registrations" className="font-semibold underline">View registrations</Link></p>}
    {!event.registered && !event.eligible && <p role="status" className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">Your profile major does not meet this event's eligibility requirement.</p>}
    <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-card"><div className="grid grid-cols-1 gap-5 sm:grid-cols-2"><p className="flex items-center gap-2 text-sm text-gray-700"><CalendarDays size={18} className="text-violet-600" /> {formatDate(event.event_date)}</p>{event.event_time && <p className="flex items-center gap-2 text-sm text-gray-700"><Clock size={18} className="text-violet-600" /> {formatTime(event.event_time)}</p>}{event.location && <p className="flex items-center gap-2 text-sm text-gray-700"><MapPin size={18} className="text-violet-600" /> {event.location}</p>}<p className="text-sm text-gray-700"><span className="font-semibold">Hosted by:</span> {event.company_name}</p></div>{event.description && <div className="mt-6 border-t border-gray-100 pt-6"><h2 className="font-semibold text-gray-900">About this event</h2><p className="mt-2 whitespace-pre-line text-sm leading-6 text-gray-700">{event.description}</p></div>}{event.eligibility && <div className="mt-6 border-t border-gray-100 pt-6"><h2 className="font-semibold text-gray-900">Eligibility</h2><p className="mt-2 text-sm text-gray-700">{event.eligibility}</p></div>}</section>
  </div>
}
