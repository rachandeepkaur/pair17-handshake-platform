import { Link } from 'react-router-dom'
import { Building2, MapPin } from 'lucide-react'
import Card from '../ui/Card'
import SkillTags from '../ui/SkillTags'
import { jobCategoryLabel } from '../../utils/constants'
import { formatDate, formatSalary } from '../../utils/format'

export default function StudentJobCard({ job }) {
  return (
    <Card className="p-5 transition-shadow hover:shadow-pop">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <Link to={`/student/jobs/${job.id}`} className="text-lg font-semibold text-gray-900 hover:text-brand-700">{job.title}</Link>
          <p className="mt-1 flex items-center gap-1.5 text-sm text-gray-600"><Building2 size={15} className="text-gray-400" /> {job.company_name}</p>
        </div>
        <span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-medium text-brand-700">{jobCategoryLabel(job.category)}</span>
      </div>
      <p className="mt-3 flex items-center gap-1.5 text-sm text-gray-600"><MapPin size={15} className="text-gray-400" /> {job.is_remote ? 'Remote' : job.city}{job.location ? ` · ${job.location}` : ''}</p>
      {job.description && <p className="mt-3 line-clamp-2 text-sm text-gray-700">{job.description}</p>}
      <div className="mt-4"><SkillTags skills={job.skills_required} /></div>
      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-gray-100 pt-3 text-xs text-gray-500">
        <span>{formatSalary(job.salary) || 'Salary not listed'}</span>
        <span>Apply by {formatDate(job.deadline)}</span>
      </div>
    </Card>
  )
}
