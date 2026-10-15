import { useState } from 'react'
import { Building2, CalendarClock, DollarSign, Mail, MapPin } from 'lucide-react'
import Button from '../../components/ui/Button'
import StudentApplyModal from '../../components/applications/StudentApplyModal'
import { useParams } from 'react-router-dom'
import ErrorMessage from '../../components/common/ErrorMessage'
import Card from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import SkillTags from '../../components/ui/SkillTags'
import { useFetch } from '../../hooks/useFetch'
import { getStudentJob } from '../../services/studentJobService'
import { jobCategoryLabel } from '../../utils/constants'
import { formatDate, formatSalary } from '../../utils/format'
import { applyToJob } from '../../services/studentApplicationService'

function Fact({ icon: Icon, label, children }) {
  return <div className="flex items-start gap-3"><Icon size={18} className="mt-0.5 text-gray-400" /><div><p className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p><p className="text-sm text-gray-900">{children}</p></div></div>
}

export default function StudentJobDetail() {
  const { jobId } = useParams()
  const { data: job, loading, error } = useFetch(() => getStudentJob(jobId), [jobId])
  const [applying, setApplying] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  if (error) return <div className="space-y-4"><PageHeader title="Job not found" backTo="/student/jobs" backLabel="Back to jobs" /><ErrorMessage message={error} /></div>
  if (loading || !job) return <Skeleton className="h-96 rounded-2xl" />

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader title={job.title} description={`${job.company_name} · ${jobCategoryLabel(job.category)}`} backTo="/student/jobs" backLabel="Back to jobs" actions={!submitted && <Button onClick={() => setApplying(true)}>Apply now</Button>} />
      {submitted && <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm text-emerald-800">Application submitted with Pending status.</p>}
      <Card className="p-5">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <Fact icon={MapPin} label="Location">{job.location || job.city}{job.is_remote && ' · Remote'}</Fact>
          <Fact icon={DollarSign} label="Salary">{formatSalary(job.salary) || 'Not listed'}</Fact>
          <Fact icon={CalendarClock} label="Application deadline">{formatDate(job.deadline)}</Fact>
          <Fact icon={Building2} label="Company">{job.company_name}</Fact>
        </div>
        <section className="mt-6 border-t border-gray-100 pt-5"><h2 className="text-sm font-semibold text-gray-900">Job description</h2><p className="mt-2 whitespace-pre-line text-sm text-gray-700">{job.description || 'No description provided.'}</p></section>
        <section className="mt-6 border-t border-gray-100 pt-5"><h2 className="text-sm font-semibold text-gray-900">Required skills</h2><div className="mt-2"><SkillTags skills={job.skills_required} /></div></section>
      </Card>
      <Card className="p-5"><h2 className="text-lg font-semibold text-gray-900">About {job.company_name}</h2><p className="mt-2 whitespace-pre-line text-sm text-gray-700">{job.company_description || 'No company description provided.'}</p><p className="mt-4 flex items-center gap-2 text-sm text-gray-700"><MapPin size={16} className="text-gray-400" />{job.company_location}</p><p className="mt-2 flex items-center gap-2 text-sm text-gray-700"><Mail size={16} className="text-gray-400" />{job.company_contact_info || 'Contact information not provided.'}</p></Card>
      {applying && <StudentApplyModal job={job} onClose={() => setApplying(false)} onApply={async (file) => { await applyToJob(job.id, file); setApplying(false); setSubmitted(true) }} />}
    </div>
  )
}
