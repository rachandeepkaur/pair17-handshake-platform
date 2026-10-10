import { useAuth } from '../../hooks/useAuth'

export default function CompanyDashboard() {
  const { logout } = useAuth()

  return (
    <div className="max-w-2xl mx-auto mt-16 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Company dashboard</h1>
        <button
          onClick={logout}
          className="rounded-md border px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Sign out
        </button>
      </div>
      <p className="mt-4 text-sm text-gray-600">You are signed in.</p>
    </div>
  )
}
