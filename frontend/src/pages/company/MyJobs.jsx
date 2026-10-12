import { Link } from 'react-router-dom'
import JobCard from '../../components/jobs/JobCard'
import ErrorMessage from '../../components/common/ErrorMessage'
import Loader from '../../components/common/Loader'
import { useFetch } from '../../hooks/useFetch'
import { getMyJobs } from '../../services/jobService'

export default function MyJobs() {
  const { data: jobs, loading, error } = useFetch(getMyJobs, [])

  return (
    <div className="mx-auto mt-10 max-w-3xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold">My job postings</h1>
        <Link
          to="/company/jobs/new"
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white"
        >
          Post a job
        </Link>
      </div>

      {loading && <Loader />}
      <ErrorMessage message={error} />

      {!loading && !error && jobs?.length === 0 && (
        <p className="text-sm text-gray-600">You haven't posted any jobs yet.</p>
      )}

      <div className="space-y-4">
        {jobs?.map((job) => (
          <JobCard key={job.id} job={job} />
        ))}
      </div>
    </div>
  )
}
