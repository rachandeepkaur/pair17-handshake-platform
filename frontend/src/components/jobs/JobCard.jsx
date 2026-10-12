import { jobCategoryLabel } from '../../utils/constants'

export default function JobCard({ job }) {
  return (
    <div className="rounded-lg border p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold">{job.title}</h3>
        <span className="shrink-0 rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-700">
          {jobCategoryLabel(job.category)}
        </span>
      </div>

      <p className="mt-1 text-sm text-gray-600">
        {job.is_remote ? 'Remote' : job.city}
        {job.location ? ` · ${job.location}` : ''}
      </p>

      {job.salary != null && <p className="mt-1 text-sm text-gray-800">Salary: ${job.salary}</p>}

      {job.description && <p className="mt-2 text-sm text-gray-700">{job.description}</p>}

      {job.skills_required && (
        <p className="mt-2 text-xs text-gray-500">Skills: {job.skills_required}</p>
      )}

      <p className="mt-3 text-xs text-gray-500">
        Posted {job.posting_date} · Apply by {job.deadline}
      </p>
    </div>
  )
}
