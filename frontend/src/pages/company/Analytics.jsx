import { Link } from 'react-router-dom'
import { BarChart3 } from 'lucide-react'
import Card, { CardHeader } from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import ErrorMessage from '../../components/common/ErrorMessage'
import { useFetch } from '../../hooks/useFetch'
import { getMyJobs } from '../../services/jobService'
import { getMyEvents } from '../../services/eventService'
import { getDashboard } from '../../services/companyService'
import { APPLICATION_STATUSES } from '../../utils/constants'

const STATUS_COLOR = { Pending: 'bg-amber-500', Reviewed: 'bg-brand-500', Declined: 'bg-red-400' }

function HorizontalBars({ rows, color = 'bg-brand-500', emptyText }) {
  const max = Math.max(1, ...rows.map((row) => row.value))
  if (rows.length === 0) return <p className="px-5 py-6 text-sm text-gray-500">{emptyText}</p>
  return (
    <ul className="space-y-3 p-5">
      {rows.map((row) => (
        <li key={row.key}>
          <div className="mb-1 flex justify-between gap-3 text-sm">
            {row.to ? (
              <Link to={row.to} className="truncate text-gray-700 hover:text-brand-700">
                {row.label}
              </Link>
            ) : (
              <span className="truncate text-gray-700">{row.label}</span>
            )}
            <span className="font-medium tabular-nums text-gray-900">{row.value}</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-gray-100">
            <div
              className={`h-full rounded-full ${row.color || color}`}
              style={{ width: `${(row.value / max) * 100}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  )
}

export default function Analytics() {
  const summary = useFetch(getDashboard, [])
  const jobs = useFetch(getMyJobs, [])
  const events = useFetch(getMyEvents, [])

  const loading = summary.loading || jobs.loading || events.loading
  const error = summary.error || jobs.error || events.error

  if (error) return <ErrorMessage message={error} />

  const byStatus = summary.data?.applications_by_status || {}
  const total = summary.data?.total_applicants || 0
  const reviewedShare = total ? Math.round(((byStatus.Reviewed || 0) * 100) / total) : 0

  const applicantsByJob = [...(jobs.data || [])]
    .sort((a, b) => b.applicant_count - a.applicant_count)
    .slice(0, 8)
    .map((job) => ({ key: job.id, label: job.title, value: job.applicant_count, to: `/company/jobs/${job.id}` }))

  const registrationsByEvent = [...(events.data || [])]
    .sort((a, b) => b.registration_count - a.registration_count)
    .slice(0, 8)
    .map((event) => ({
      key: event.id,
      label: event.name,
      value: event.registration_count,
      to: `/company/events/${event.id}`,
    }))

  return (
    <div className="space-y-5">
      <PageHeader title="Analytics" description="Recruiting performance across your jobs and events." />

      {loading ? (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <Skeleton className="h-64 rounded-2xl" />
          <Skeleton className="h-64 rounded-2xl" />
        </div>
      ) : total === 0 && registrationsByEvent.every((row) => row.value === 0) ? (
        <EmptyState
          icon={BarChart3}
          title="No recruiting activity yet"
          description="Charts appear once students apply to your jobs or register for your events."
        />
      ) : (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <Card>
            <CardHeader
              title="Application pipeline"
              subtitle={`${total} applications · ${reviewedShare}% reviewed`}
            />
            <HorizontalBars
              rows={APPLICATION_STATUSES.map((status) => ({
                key: status,
                label: status,
                value: byStatus[status] || 0,
                color: STATUS_COLOR[status],
              }))}
            />
          </Card>

          <Card>
            <CardHeader title="Applicants by job" subtitle="Top postings by applicant count" />
            <HorizontalBars rows={applicantsByJob} emptyText="No job postings yet." />
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader title="Event registrations" subtitle="Students registered per event" />
            <HorizontalBars rows={registrationsByEvent} color="bg-accent-500" emptyText="No events yet." />
          </Card>
        </div>
      )}
    </div>
  )
}
