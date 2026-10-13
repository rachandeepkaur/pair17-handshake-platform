import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Briefcase, MapPin, CalendarClock, Users, Search } from 'lucide-react'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import PageHeader from '../../components/ui/PageHeader'
import StatusBadge from '../../components/ui/StatusBadge'
import EmptyState from '../../components/ui/EmptyState'
import Tabs from '../../components/ui/Tabs'
import { RowSkeleton } from '../../components/ui/Skeleton'
import ErrorMessage from '../../components/common/ErrorMessage'
import { useFetch } from '../../hooks/useFetch'
import { usePermissions } from '../../hooks/usePermissions'
import { getMyJobs } from '../../services/jobService'
import { JOB_CATEGORIES, jobCategoryLabel } from '../../utils/constants'
import { formatDate, formatSalary, isOnOrAfterToday } from '../../utils/format'

const jobStatus = (job) => (isOnOrAfterToday(job.deadline) ? 'Active' : 'Closed')

export default function MyJobs() {
  const { data: jobs, loading, error } = useFetch(getMyJobs, [])
  const { can } = usePermissions()
  const [tab, setTab] = useState('all')
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return (jobs || []).filter(
      (job) =>
        (tab === 'all' || jobStatus(job) === tab) &&
        (!category || job.category === category) &&
        (!q || job.title.toLowerCase().includes(q) || job.city.toLowerCase().includes(q)),
    )
  }, [jobs, tab, query, category])

  const countFor = (status) => (jobs || []).filter((job) => jobStatus(job) === status).length
  const tabs = [
    { value: 'all', label: 'All', count: jobs?.length },
    { value: 'Active', label: 'Active', count: jobs ? countFor('Active') : undefined },
    { value: 'Closed', label: 'Closed', count: jobs ? countFor('Closed') : undefined },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Jobs"
        description="Manage your postings and see who applied."
        actions={
          can('jobs:write') && (
            <Button as={Link} to="/company/jobs/new" icon={Plus}>
              Post a Job
            </Button>
          )
        }
      />

      <ErrorMessage message={error} />

      <Card className="overflow-hidden">
        <div className="space-y-3 px-5 pt-4">
          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search by title or city"
                aria-label="Search jobs by title or city"
                className="h-10 w-full rounded-xl border border-gray-300 pl-9 pr-3 text-sm focus:border-brand-400"
              />
            </div>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              aria-label="Filter by employment type"
              className="h-10 rounded-xl border border-gray-300 bg-white px-3 text-sm focus:border-brand-400"
            >
              <option value="">All types</option>
              {JOB_CATEGORIES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <Tabs tabs={tabs} value={tab} onChange={setTab} label="Job status" />
        </div>

        {loading && (
          <div className="divide-y divide-gray-100 px-5">
            <RowSkeleton />
            <RowSkeleton />
            <RowSkeleton />
          </div>
        )}

        {!loading && !error && jobs?.length === 0 && (
          <div className="p-5">
            <EmptyState
              icon={Briefcase}
              title="Your first job post is one step away."
              description="Post a role to start receiving applicants."
              action={
                can('jobs:write') && (
                  <Button as={Link} to="/company/jobs/new" icon={Plus}>
                    Post a Job
                  </Button>
                )
              }
            />
          </div>
        )}

        {!loading && jobs?.length > 0 && filtered.length === 0 && (
          <p className="px-5 py-10 text-center text-sm text-gray-500">No jobs match these filters.</p>
        )}

        {!loading && filtered.length > 0 && (
          <>
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-gray-100 bg-gray-50/60 text-xs uppercase tracking-wide text-gray-500">
                  <tr>
                    <th className="px-5 py-3 font-medium">Job title</th>
                    <th className="px-5 py-3 font-medium">Type</th>
                    <th className="px-5 py-3 font-medium">Location</th>
                    <th className="px-5 py-3 font-medium">Salary</th>
                    <th className="px-5 py-3 font-medium">Applicants</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium">Posted</th>
                    <th className="px-5 py-3 font-medium">Deadline</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filtered.map((job) => (
                    <tr key={job.id} className="hover:bg-gray-50/60">
                      <td className="px-5 py-3">
                        <Link to={`/company/jobs/${job.id}`} className="font-medium text-gray-900 hover:text-brand-700">
                          {job.title}
                        </Link>
                      </td>
                      <td className="px-5 py-3 text-gray-600">{jobCategoryLabel(job.category)}</td>
                      <td className="px-5 py-3 text-gray-600">{job.is_remote ? `Remote · ${job.city}` : job.city}</td>
                      <td className="px-5 py-3 text-gray-600">{formatSalary(job.salary) || '—'}</td>
                      <td className="px-5 py-3">
                        <Link
                          to={`/company/jobs/${job.id}`}
                          className="inline-flex items-center gap-1 font-medium text-brand-600 hover:text-brand-700"
                        >
                          <Users size={14} aria-hidden="true" /> {job.applicant_count}
                        </Link>
                      </td>
                      <td className="px-5 py-3">
                        <StatusBadge status={jobStatus(job)} />
                      </td>
                      <td className="whitespace-nowrap px-5 py-3 text-gray-600">{formatDate(job.posting_date)}</td>
                      <td className="whitespace-nowrap px-5 py-3 text-gray-600">{formatDate(job.deadline)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <ul className="divide-y divide-gray-100 md:hidden">
              {filtered.map((job) => (
                <li key={job.id}>
                  <Link to={`/company/jobs/${job.id}`} className="block p-4 hover:bg-gray-50/60">
                    <span className="flex items-start justify-between gap-2">
                      <span className="font-medium text-gray-900">{job.title}</span>
                      <StatusBadge status={jobStatus(job)} />
                    </span>
                    <span className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                      <span className="inline-flex items-center gap-1">
                        <Briefcase size={13} aria-hidden="true" /> {jobCategoryLabel(job.category)}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <MapPin size={13} aria-hidden="true" /> {job.is_remote ? 'Remote' : job.city}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <CalendarClock size={13} aria-hidden="true" /> {formatDate(job.deadline)}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Users size={13} aria-hidden="true" /> {job.applicant_count} applicants
                      </span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}
      </Card>
    </div>
  )
}
