import { Link, useParams } from 'react-router-dom'
import { Briefcase } from 'lucide-react'
import Card, { CardHeader } from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'
import StatusBadge from '../../components/ui/StatusBadge'
import Skeleton from '../../components/ui/Skeleton'
import ErrorMessage from '../../components/common/ErrorMessage'
import StatusUpdater from '../../components/applications/StatusUpdater'
import ResumePreview from '../../components/applications/ResumePreview'
import StudentProfileView from '../../components/profile/StudentProfileView'
import { useFetch } from '../../hooks/useFetch'
import { getApplication } from '../../services/applicationService'
import { formatDate } from '../../utils/format'

export default function ApplicantProfile() {
  const { applicationId } = useParams()
  const { data, loading, error, setData } = useFetch(() => getApplication(applicationId), [applicationId])

  const handleUpdated = (updated) =>
    setData((current) => ({ ...current, status: updated.status, updated_at: updated.updated_at }))

  if (error) {
    return (
      <div className="space-y-4">
        <PageHeader title="Application not found" backTo="/company/applicants" backLabel="Back to applicants" />
        <ErrorMessage message={error} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={data ? data.student.name : <Skeleton className="h-8 w-56" />}
        description={data && `Applied ${formatDate(data.applied_at)}`}
        backTo={data ? `/company/jobs/${data.job_id}` : '/company/applicants'}
        backLabel="Back to job"
        actions={data && <StatusBadge status={data.status} />}
      />

      {loading || !data ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          <Skeleton className="h-96 lg:col-span-2" />
          <Skeleton className="h-96 lg:col-span-3" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          <div className="space-y-5 lg:col-span-2">
            <Card>
              <CardHeader title="Application" />
              <div className="space-y-4 px-5 py-4">
                <Link
                  to={`/company/jobs/${data.job_id}`}
                  className="flex items-center gap-2 rounded-md text-sm font-medium text-brand-700 hover:underline"
                >
                  <Briefcase size={16} aria-hidden="true" /> {data.job_title}
                </Link>
                <StatusUpdater application={data} onUpdated={handleUpdated} />
                <p className="text-xs text-gray-500">Last updated {formatDate(data.updated_at)}</p>
              </div>
            </Card>
            <StudentProfileView student={data.student} />
          </div>

          <div className="lg:col-span-3">
            <ResumePreview applicationId={data.id} studentName={data.student.name} />
          </div>
        </div>
      )}
    </div>
  )
}
