import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Briefcase, CalendarClock, DollarSign, MapPin, Users } from 'lucide-react'
import Card, { CardHeader } from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'
import StatusBadge from '../../components/ui/StatusBadge'
import SkillTags from '../../components/ui/SkillTags'
import Skeleton, { RowSkeleton } from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import Tabs from '../../components/ui/Tabs'
import ErrorMessage from '../../components/common/ErrorMessage'
import ApplicantsTable from '../../components/applications/ApplicantsTable'
import { useFetch } from '../../hooks/useFetch'
import { getJob, getJobApplications } from '../../services/jobService'
import { APPLICATION_STATUSES, jobCategoryLabel } from '../../utils/constants'
import { formatDate, formatSalary, isOnOrAfterToday } from '../../utils/format'

function Fact({ icon: Icon, label, children }) {
  return (
    <div className="flex items-start gap-3">
      <Icon size={18} className="mt-0.5 shrink-0 text-gray-400" aria-hidden="true" />
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p>
        <p className="text-sm text-gray-900">{children}</p>
      </div>
    </div>
  )
}

export default function JobDetail() {
  const { jobId } = useParams()
  const job = useFetch(() => getJob(jobId), [jobId])
  const applications = useFetch(() => getJobApplications(jobId), [jobId])
  const [tab, setTab] = useState('all')

  const handleUpdated = (updated) =>
    applications.setData((list) => list.map((item) => (item.id === updated.id ? updated : item)))

  const list = applications.data || []
  const visible = tab === 'all' ? list : list.filter((item) => item.status === tab)
  const tabs = [
    { value: 'all', label: 'All', count: list.length },
    ...APPLICATION_STATUSES.map((status) => ({
      value: status,
      label: status,
      count: list.filter((item) => item.status === status).length,
    })),
  ]

  if (job.error) {
    return (
      <div className="space-y-4">
        <PageHeader title="Job not found" backTo="/company/jobs" backLabel="Back to jobs" />
        <ErrorMessage message={job.error} />
      </div>
    )
  }

  const data = job.data
  return (
    <div className="space-y-6">
      <PageHeader
        title={data ? data.title : <Skeleton className="h-8 w-64" />}
        description={data && `${jobCategoryLabel(data.category)} · Posted ${formatDate(data.posting_date)}`}
        backTo="/company/jobs"
        backLabel="Back to jobs"
        actions={data && <StatusBadge status={isOnOrAfterToday(data.deadline) ? 'Active' : 'Closed'} />}
      />

      {data && (
        <Card className="p-5">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <Fact icon={MapPin} label="Location">
              {data.location || data.city}
              {data.is_remote && ' · Remote'}
            </Fact>
            <Fact icon={DollarSign} label="Salary">
              {formatSalary(data.salary) || 'Not listed'}
            </Fact>
            <Fact icon={CalendarClock} label="Deadline">
              {formatDate(data.deadline)}
            </Fact>
            <Fact icon={Users} label="Applicants">
              {data.applicant_count}
            </Fact>
          </div>
          {data.description && (
            <div className="mt-5 border-t border-gray-100 pt-4">
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">Description</p>
              <p className="whitespace-pre-line text-sm text-gray-700">{data.description}</p>
            </div>
          )}
          <div className="mt-5 border-t border-gray-100 pt-4">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">Required skills</p>
            <SkillTags skills={data.skills_required} />
          </div>
        </Card>
      )}

      <Card className="overflow-hidden">
        <CardHeader title="Applicants" subtitle="Open a candidate to preview their resume." />
        <div className="px-5">
          <Tabs tabs={tabs} value={tab} onChange={setTab} label="Filter applicants by status" />
        </div>
        <ErrorMessage message={applications.error} />
        {applications.loading ? (
          <div className="px-5">
            <RowSkeleton />
            <RowSkeleton />
          </div>
        ) : visible.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={Briefcase}
              title={list.length === 0 ? 'No applicants yet' : `No ${tab.toLowerCase()} applicants`}
              description={
                list.length === 0
                  ? 'Improve your reach by adding required skills and a clear description.'
                  : 'Try another status filter.'
              }
            />
          </div>
        ) : (
          <ApplicantsTable applications={visible} onUpdated={handleUpdated} showJob={false} />
        )}
      </Card>
    </div>
  )
}
