import { Link } from 'react-router-dom'
import { GraduationCap, MapPin } from 'lucide-react'
import Avatar from '../ui/Avatar'
import SkillTags from '../ui/SkillTags'
import StatusBadge from '../ui/StatusBadge'
import Skeleton from '../ui/Skeleton'
import { useFetch } from '../../hooks/useFetch'
import { getCompanyApplications } from '../../services/applicationService'
import { formatDate } from '../../utils/format'

export default function ContactPanel({ student }) {
  const applications = useFetch(() => getCompanyApplications({ studentId: student.account_id }), [student.account_id])
  const program = [student.degree, student.major].filter(Boolean).join(' in ')

  return (
    <aside className="space-y-5 overflow-y-auto p-4" aria-label={`About ${student.name}`}>
      <div className="flex flex-col items-center text-center">
        <Avatar name={student.name} size="lg" />
        <p className="mt-2 font-semibold text-gray-900">{student.name}</p>
        <p className="mt-1 flex items-center gap-1 text-sm text-gray-600">
          <GraduationCap size={15} aria-hidden="true" /> {student.college_name}
        </p>
        {program && <p className="text-sm text-gray-500">{program}</p>}
        {student.graduation_year && <p className="text-sm text-gray-500">Class of {student.graduation_year}</p>}
        {student.city && (
          <p className="mt-1 flex items-center gap-1 text-sm text-gray-500">
            <MapPin size={14} aria-hidden="true" /> {student.city}
          </p>
        )}
        <Link
          to={`/company/students/${student.account_id}`}
          className="mt-3 rounded-md text-sm font-medium text-brand-600 hover:text-brand-700"
        >
          View full profile
        </Link>
      </div>

      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Skills</h3>
        <SkillTags skills={student.skills} />
      </div>

      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Applications to you</h3>
        {applications.loading ? (
          <Skeleton className="h-12 rounded-xl" />
        ) : applications.data?.length === 0 ? (
          <p className="text-sm text-gray-500">Hasn't applied to your jobs yet.</p>
        ) : (
          <ul className="space-y-2">
            {applications.data?.map((application) => (
              <li key={application.id}>
                <Link
                  to={`/company/applications/${application.id}`}
                  className="block rounded-xl border border-gray-100 p-2.5 hover:bg-gray-50"
                >
                  <span className="flex items-start justify-between gap-2">
                    <span className="min-w-0 truncate text-sm font-medium text-gray-900">{application.job_title}</span>
                    <StatusBadge status={application.status} />
                  </span>
                  <span className="text-xs text-gray-500">Applied {formatDate(application.applied_at)}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  )
}
