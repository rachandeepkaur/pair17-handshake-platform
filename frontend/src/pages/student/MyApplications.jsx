import { useState } from 'react'
import { Briefcase } from 'lucide-react'
import ErrorMessage from '../../components/common/ErrorMessage'
import EmptyState from '../../components/ui/EmptyState'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import StatusBadge from '../../components/ui/StatusBadge'
import { useFetch } from '../../hooks/useFetch'
import { getMyApplications } from '../../services/studentApplicationService'
import { APPLICATION_STATUSES } from '../../utils/constants'
import { formatDateTime } from '../../utils/format'

export default function MyApplications() {
  const [status, setStatus] = useState('')
  const { data, loading, error } = useFetch(() => getMyApplications(status), [status])
  return <div className="mx-auto max-w-5xl space-y-6"><PageHeader title="My Applications" description="Track applications and their current status." />
    <select value={status} onChange={(event) => setStatus(event.target.value)} aria-label="Filter application status" className="h-10 rounded-xl border border-gray-300 bg-white px-3 text-sm"><option value="">All statuses</option>{APPLICATION_STATUSES.map((item) => <option key={item}>{item}</option>)}</select>
    {error && <ErrorMessage message={error} />}
    {loading ? <Skeleton className="h-52 rounded-2xl" /> : data?.length ? <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-card"><ul className="divide-y divide-gray-100">{data.map((application) => <li key={application.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4"><div><p className="font-medium text-gray-900">{application.job_title}</p><p className="mt-1 text-sm text-gray-500">{application.company_name} · Applied {formatDateTime(application.applied_at)}</p></div><StatusBadge status={application.status} /></li>)}</ul></div> : !error && <EmptyState icon={Briefcase} title="No applications yet" description="Browse jobs to submit your first application." />}</div>
}
