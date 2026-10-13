import { useEffect } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import {
  Briefcase,
  BriefcaseBusiness,
  Users,
  ClipboardList,
  CalendarDays,
  UserCheck,
  Plus,
  CalendarPlus,
  UserSearch,
  UserPlus,
  MessageSquare,
  ArrowRight,
  Clock,
} from 'lucide-react'
import Card, { CardHeader } from '../../components/ui/Card'
import StatCard from '../../components/ui/StatCard'
import { RowSkeleton, StatCardSkeleton } from '../../components/ui/Skeleton'
import StatusBadge from '../../components/ui/StatusBadge'
import Avatar from '../../components/ui/Avatar'
import Button from '../../components/ui/Button'
import EmptyState from '../../components/ui/EmptyState'
import ErrorMessage from '../../components/common/ErrorMessage'
import { useFetch } from '../../hooks/useFetch'
import { usePermissions } from '../../hooks/usePermissions'
import { getMyJobs } from '../../services/jobService'
import { getMyEvents } from '../../services/eventService'
import { APPLICATION_STATUSES } from '../../utils/constants'
import { daysFromToday, formatDate, formatTime, isOnOrAfterToday } from '../../utils/format'

const QUICK_ACTIONS = [
  { to: '/company/jobs/new', label: 'Post a Job', icon: Plus, permission: 'jobs:write' },
  { to: '/company/events/new', label: 'Create Event', icon: CalendarPlus, permission: 'events:write' },
  { to: '/company/students', label: 'Find Students', icon: UserSearch },
  { to: '/company/team', label: 'Invite Teammate', icon: UserPlus, permission: 'team:manage' },
]

const STATUS_BAR = { Pending: 'bg-amber-500', Reviewed: 'bg-brand-500', Declined: 'bg-red-400' }

function ViewAll({ to }) {
  return (
    <Link to={to} className="inline-flex items-center gap-1 rounded-md text-sm font-medium text-brand-600 hover:text-brand-700">
      View all <ArrowRight size={15} aria-hidden="true" />
    </Link>
  )
}

export default function CompanyDashboard() {
  const { company, companyError, reloadCompany } = useOutletContext()
  const { can } = usePermissions()
  const jobs = useFetch(getMyJobs, [])
  const events = useFetch(getMyEvents, [])

  // The layout fetched the summary once; refresh it so counts reflect jobs,
  // events, or status changes made since.
  useEffect(() => {
    reloadCompany()
  }, [reloadCompany])

  const closingSoon = (jobs.data || [])
    .filter((job) => isOnOrAfterToday(job.deadline) && daysFromToday(job.deadline) <= 7)
    .slice(0, 4)
  const upcomingEvents = (events.data || []).filter((event) => isOnOrAfterToday(event.event_date)).slice(0, 3)

  const metrics = company && [
    { icon: Briefcase, label: 'Active jobs', value: company.active_jobs, tone: 'brand' },
    { icon: BriefcaseBusiness, label: 'Total job postings', value: company.total_jobs, tone: 'cyan' },
    { icon: Users, label: 'Total applicants', value: company.total_applicants, tone: 'accent' },
    { icon: ClipboardList, label: 'Pending review', value: company.pending_applications, tone: 'amber' },
    { icon: CalendarDays, label: 'Upcoming events', value: company.upcoming_events, tone: 'violet' },
    { icon: UserCheck, label: 'Event registrations', value: company.total_registrations, tone: 'rose' },
  ]

  return (
    <div className="space-y-6">
      <ErrorMessage message={companyError} />

      <div className="rounded-2xl bg-gradient-to-br from-brand-600 via-brand-600 to-brand-800 p-6 text-white lg:p-8">
        <p className="text-sm font-medium text-brand-100">Welcome back</p>
        <h1 className="mt-1 text-2xl font-bold lg:text-3xl">{company?.company_name || 'Your company'}</h1>
        <p className="mt-1 text-sm text-brand-100">Here’s what’s happening with your recruiting today.</p>
        <div className="mt-5 flex flex-wrap gap-2">
          {QUICK_ACTIONS.filter(({ permission }) => !permission || can(permission)).map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className="inline-flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-white/25 focus-visible:ring-white focus-visible:ring-offset-brand-700"
            >
              <Icon size={18} aria-hidden="true" />
              {label}
            </Link>
          ))}
        </div>
      </div>

      {company && company.profile_completion < 100 && (
        <Card className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
          <div className="flex-1">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-semibold text-gray-900">Complete your company profile</h2>
              <span className="text-lg font-bold text-brand-600">{company.profile_completion}%</span>
            </div>
            <div
              className="mt-3 h-2 w-full overflow-hidden rounded-full bg-gray-100"
              role="progressbar"
              aria-valuenow={company.profile_completion}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Profile completion"
            >
              <div
                className="h-full rounded-full bg-gradient-to-r from-brand-500 to-accent-500"
                style={{ width: `${company.profile_completion}%` }}
              />
            </div>
          </div>
          <Button as={Link} to="/company/profile" variant="outline">
            Finish profile
          </Button>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
        {metrics
          ? metrics.map((metric) => <StatCard key={metric.label} {...metric} />)
          : Array.from({ length: 6 }).map((_, i) => <StatCardSkeleton key={i} />)}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader title="Recent applicants" action={<ViewAll to="/company/applicants" />} />
            {!company ? (
              <div className="px-5">
                <RowSkeleton />
                <RowSkeleton />
              </div>
            ) : company.recent_applications.length === 0 ? (
              <div className="p-5">
                <EmptyState
                  icon={Users}
                  title="No applicants yet"
                  description="Improve your reach by adding required skills and a clear description to your job posts."
                />
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {company.recent_applications.map((application) => (
                  <li key={application.id}>
                    <Link
                      to={`/company/applications/${application.id}`}
                      className="flex items-center gap-3 px-5 py-3 hover:bg-gray-50/60"
                    >
                      <Avatar name={application.student_name} />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-medium text-gray-900">
                          {application.student_name}
                        </span>
                        <span className="block truncate text-xs text-gray-500">
                          {application.college_name} · {application.job_title}
                        </span>
                      </span>
                      <span className="hidden text-xs text-gray-500 sm:block">
                        {formatDate(application.applied_at)}
                      </span>
                      <StatusBadge status={application.status} />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <CardHeader title="Jobs that need attention" subtitle="Deadlines within the next 7 days" action={<ViewAll to="/company/jobs" />} />
            <div className="p-5">
              {jobs.loading ? (
                <RowSkeleton />
              ) : jobs.data?.length === 0 ? (
                <EmptyState
                  icon={Briefcase}
                  title="Your first job post is one step away."
                  description="Publish a role to start receiving applicants."
                  action={
                    can('jobs:write') && (
                      <Button as={Link} to="/company/jobs/new" icon={Plus}>
                        Post a Job
                      </Button>
                    )
                  }
                />
              ) : closingSoon.length === 0 ? (
                <p className="text-sm text-gray-500">No postings close in the next week.</p>
              ) : (
                <ul className="space-y-3">
                  {closingSoon.map((job) => {
                    const days = daysFromToday(job.deadline)
                    return (
                      <li key={job.id}>
                        <Link
                          to={`/company/jobs/${job.id}`}
                          className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50/60 p-3 hover:bg-amber-50"
                        >
                          <Clock size={18} className="shrink-0 text-amber-600" aria-hidden="true" />
                          <span className="min-w-0 flex-1 text-sm">
                            <span className="block truncate font-medium text-amber-950">{job.title}</span>
                            <span className="text-amber-800">
                              {days === 0 ? 'Closes today' : `Closes in ${days} day${days === 1 ? '' : 's'}`} ·{' '}
                              {job.applicant_count} applicant{job.applicant_count === 1 ? '' : 's'}
                            </span>
                          </span>
                          <ArrowRight size={16} className="text-amber-700" aria-hidden="true" />
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Link to="/company/messages" className="block rounded-2xl">
            <Card className="flex items-center gap-3 p-5 transition-shadow hover:shadow-card-hover">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                <MessageSquare size={20} aria-hidden="true" />
              </span>
              <span className="flex-1">
                <span className="block font-semibold text-gray-900">Messages</span>
                <span className="block text-sm text-gray-500">
                  {company ? `${company.unread_messages} unread from students` : 'Loading…'}
                </span>
              </span>
              <ArrowRight size={18} className="text-gray-400" aria-hidden="true" />
            </Card>
          </Link>

          <Card>
            <CardHeader title="Applications by status" />
            <div className="space-y-3 p-5">
              {APPLICATION_STATUSES.map((status) => {
                const count = company?.applications_by_status?.[status] ?? 0
                const total = company?.total_applicants || 0
                return (
                  <div key={status}>
                    <div className="mb-1 flex justify-between text-sm">
                      <span className="text-gray-600">{status}</span>
                      <span className="font-medium text-gray-900">{count}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                      <div
                        className={`h-full rounded-full ${STATUS_BAR[status]}`}
                        style={{ width: total ? `${(count / total) * 100}%` : 0 }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </Card>

          <Card>
            <CardHeader title="Upcoming events" action={<ViewAll to="/company/events" />} />
            <div className="p-5">
              {events.loading ? (
                <RowSkeleton />
              ) : upcomingEvents.length === 0 ? (
                <EmptyState
                  icon={CalendarDays}
                  title="No upcoming events"
                  description="Create an event to meet qualified students."
                  action={
                    can('events:write') && (
                      <Button as={Link} to="/company/events/new" variant="secondary" size="sm" icon={CalendarPlus}>
                        Create Event
                      </Button>
                    )
                  }
                />
              ) : (
                <ul className="space-y-3">
                  {upcomingEvents.map((event) => (
                    <li key={event.id}>
                      <Link
                        to={`/company/events/${event.id}`}
                        className="block rounded-xl border border-gray-100 p-3 hover:border-gray-200 hover:bg-gray-50/60"
                      >
                        <span className="block text-sm font-medium text-gray-900">{event.name}</span>
                        <span className="mt-0.5 block text-xs text-gray-500">
                          {formatDate(event.event_date)}
                          {event.event_time && ` · ${formatTime(event.event_time)}`}
                        </span>
                        <span className="mt-1 block text-xs font-medium text-accent-700">
                          {event.registration_count} registered
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
