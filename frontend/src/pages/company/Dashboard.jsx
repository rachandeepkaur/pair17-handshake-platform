import { Link } from 'react-router-dom'
import ErrorMessage from '../../components/common/ErrorMessage'
import Loader from '../../components/common/Loader'
import { useAuth } from '../../hooks/useAuth'
import { useFetch } from '../../hooks/useFetch'
import { getDashboard } from '../../services/companyService'

export default function CompanyDashboard() {
  const { logout } = useAuth()
  const { data, loading, error } = useFetch(getDashboard, [])

  return (
    <div className="mx-auto mt-10 max-w-3xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Company dashboard</h1>
        <button
          onClick={logout}
          className="rounded-md border px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Sign out
        </button>
      </div>

      {loading && <Loader />}
      <ErrorMessage message={error} />

      {data && (
        <>
          <div className="mb-6 rounded-lg border p-4">
            <p className="font-medium">{data.company_name}</p>
            <p className="text-sm text-gray-600">{data.location}</p>
            <p className="text-sm text-gray-600">{data.email}</p>
          </div>

          <div className="mb-6 rounded-lg border p-4 text-center">
            <p className="text-2xl font-semibold">{data.total_jobs}</p>
            <p className="text-sm text-gray-600">Job postings</p>
          </div>

          <div className="flex gap-3">
            <Link
              to="/company/jobs/new"
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white"
            >
              Post a job
            </Link>
            <Link
              to="/company/jobs"
              className="rounded-md border px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              View my jobs
            </Link>
          </div>
        </>
      )}
    </div>
  )
}
