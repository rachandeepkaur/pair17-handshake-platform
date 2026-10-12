import { Link } from 'react-router-dom'
import Avatar from '../ui/Avatar'
import SkillTags from '../ui/SkillTags'
import StatusUpdater from './StatusUpdater'
import { formatDate } from '../../utils/format'

export default function ApplicantsTable({ applications, onUpdated, showJob = true }) {
  return (
    <>
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-100 bg-gray-50/60 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-5 py-3 font-medium">Candidate</th>
              {showJob && <th className="px-5 py-3 font-medium">Applied job</th>}
              <th className="px-5 py-3 font-medium">Skills</th>
              <th className="px-5 py-3 font-medium">Applied</th>
              <th className="px-5 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {applications.map((application) => (
              <tr key={application.id} className="hover:bg-gray-50/60">
                <td className="px-5 py-3">
                  <Link
                    to={`/company/applications/${application.id}`}
                    className="flex items-center gap-3 rounded-lg"
                  >
                    <Avatar name={application.student.name} size="sm" />
                    <span className="min-w-0">
                      <span className="block font-medium text-gray-900 hover:text-brand-700">
                        {application.student.name}
                      </span>
                      <span className="block truncate text-xs text-gray-500">
                        {application.student.college_name}
                        {application.student.major ? ` · ${application.student.major}` : ''}
                      </span>
                    </span>
                  </Link>
                </td>
                {showJob && (
                  <td className="px-5 py-3 text-gray-600">
                    <Link to={`/company/jobs/${application.job_id}`} className="hover:text-brand-700">
                      {application.job_title}
                    </Link>
                  </td>
                )}
                <td className="px-5 py-3">
                  <SkillTags skills={application.student.skills} max={3} />
                </td>
                <td className="whitespace-nowrap px-5 py-3 text-gray-600">
                  {formatDate(application.applied_at)}
                </td>
                <td className="px-5 py-3">
                  <StatusUpdater application={application} onUpdated={onUpdated} compact />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="divide-y divide-gray-100 md:hidden">
        {applications.map((application) => (
          <div key={application.id} className="space-y-3 p-4">
            <Link to={`/company/applications/${application.id}`} className="flex items-center gap-3">
              <Avatar name={application.student.name} size="sm" />
              <span className="min-w-0">
                <span className="block font-medium text-gray-900">{application.student.name}</span>
                <span className="block truncate text-xs text-gray-500">
                  {showJob ? application.job_title : application.student.college_name} · Applied{' '}
                  {formatDate(application.applied_at)}
                </span>
              </span>
            </Link>
            <StatusUpdater application={application} onUpdated={onUpdated} compact />
          </div>
        ))}
      </div>
    </>
  )
}
