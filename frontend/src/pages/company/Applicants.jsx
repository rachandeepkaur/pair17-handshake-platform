import { useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { LayoutGrid, Search, Table2, Users } from 'lucide-react'
import Card from '../../components/ui/Card'
import Avatar from '../../components/ui/Avatar'
import PageHeader from '../../components/ui/PageHeader'
import EmptyState from '../../components/ui/EmptyState'
import Tabs from '../../components/ui/Tabs'
import { RowSkeleton } from '../../components/ui/Skeleton'
import ErrorMessage from '../../components/common/ErrorMessage'
import ApplicantsTable from '../../components/applications/ApplicantsTable'
import StatusUpdater from '../../components/applications/StatusUpdater'
import { useFetch } from '../../hooks/useFetch'
import { getCompanyApplications } from '../../services/applicationService'
import { getMyJobs } from '../../services/jobService'
import { APPLICATION_STATUSES } from '../../utils/constants'
import { formatDate } from '../../utils/format'

const COLUMN_ACCENT = { Pending: 'bg-amber-500', Reviewed: 'bg-brand-500', Declined: 'bg-red-500' }

function BoardView({ applications, onUpdated }) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      {APPLICATION_STATUSES.map((status) => {
        const cards = applications.filter((item) => item.status === status)
        return (
          <section key={status} aria-label={`${status} applicants`}>
            <div className="mb-2 flex items-center gap-2 px-1">
              <span className={`h-2 w-2 rounded-full ${COLUMN_ACCENT[status]}`} aria-hidden="true" />
              <h2 className="text-sm font-semibold text-gray-700">{status}</h2>
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">{cards.length}</span>
            </div>
            <div className="space-y-2">
              {cards.map((item) => (
                <Card key={item.id} className="space-y-3 p-3">
                  <Link to={`/company/applications/${item.id}`} className="flex items-center gap-2 rounded-lg">
                    <Avatar name={item.student.name} size="sm" />
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-medium text-gray-900 hover:text-brand-700">
                        {item.student.name}
                      </span>
                      <span className="block truncate text-xs text-gray-500">{item.student.college_name}</span>
                    </span>
                  </Link>
                  <p className="truncate text-xs text-gray-600">
                    {item.job_title} · {formatDate(item.applied_at)}
                  </p>
                  <StatusUpdater application={item} onUpdated={onUpdated} compact />
                </Card>
              ))}
              {cards.length === 0 && (
                <p className="rounded-xl border border-dashed border-gray-200 py-6 text-center text-xs text-gray-400">
                  No {status.toLowerCase()} applicants
                </p>
              )}
            </div>
          </section>
        )
      })}
    </div>
  )
}

export default function Applicants() {
  const [searchParams, setSearchParams] = useSearchParams()
  const jobId = searchParams.get('job') || ''
  const [status, setStatus] = useState('all')
  const [view, setView] = useState('table')
  const [query, setQuery] = useState('')

  const jobs = useFetch(getMyJobs, [])
  const applications = useFetch(() => getCompanyApplications({ jobId }), [jobId])

  const handleUpdated = (updated) =>
    applications.setData((list) => list.map((item) => (item.id === updated.id ? updated : item)))

  const list = applications.data || []
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return list.filter(
      (item) =>
        (status === 'all' || view === 'board' || item.status === status) &&
        (!q ||
          item.student.name.toLowerCase().includes(q) ||
          item.student.college_name.toLowerCase().includes(q) ||
          (item.student.skills || '').toLowerCase().includes(q)),
    )
  }, [list, status, query, view])

  const tabs = [
    { value: 'all', label: 'All', count: list.length },
    ...APPLICATION_STATUSES.map((value) => ({
      value,
      label: value,
      count: list.filter((item) => item.status === value).length,
    })),
  ]

  const viewButton = (value, Icon, label) => (
    <button
      onClick={() => setView(value)}
      aria-pressed={view === value}
      className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium ${
        view === value ? 'bg-brand-50 text-brand-700' : 'text-gray-500 hover:text-gray-700'
      }`}
    >
      <Icon size={16} aria-hidden="true" /> {label}
    </button>
  )

  return (
    <div className="space-y-5">
      <PageHeader
        title="Applicants"
        description="Review candidates across all of your job postings."
        actions={
          <div className="inline-flex rounded-xl border border-gray-200 bg-white p-1">
            {viewButton('table', Table2, 'Table')}
            {viewButton('board', LayoutGrid, 'Board')}
          </div>
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Filter by name, college, or skill"
            aria-label="Filter applicants by name, college, or skill"
            className="h-10 w-full rounded-xl border border-gray-300 bg-white pl-9 pr-3 text-sm focus:border-brand-400"
          />
        </div>
        <select
          value={jobId}
          onChange={(event) =>
            setSearchParams(event.target.value ? { job: event.target.value } : {}, { replace: true })
          }
          aria-label="Filter by job"
          className="h-10 rounded-xl border border-gray-300 bg-white px-3 text-sm focus:border-brand-400 sm:w-64"
        >
          <option value="">All jobs</option>
          {(jobs.data || []).map((job) => (
            <option key={job.id} value={job.id}>
              {job.title}
            </option>
          ))}
        </select>
      </div>

      <ErrorMessage message={applications.error} />

      {applications.loading ? (
        <Card className="px-5">
          <RowSkeleton />
          <RowSkeleton />
          <RowSkeleton />
        </Card>
      ) : list.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No applicants yet"
          description="Improve your job reach by adding required skills and a clear description to your postings."
        />
      ) : view === 'board' ? (
        <BoardView applications={filtered} onUpdated={handleUpdated} />
      ) : (
        <Card className="overflow-hidden">
          <div className="px-5">
            <Tabs tabs={tabs} value={status} onChange={setStatus} label="Filter applicants by status" />
          </div>
          {filtered.length === 0 ? (
            <p className="px-5 py-10 text-center text-sm text-gray-500">No applicants match these filters.</p>
          ) : (
            <ApplicantsTable applications={filtered} onUpdated={handleUpdated} />
          )}
        </Card>
      )}
    </div>
  )
}
