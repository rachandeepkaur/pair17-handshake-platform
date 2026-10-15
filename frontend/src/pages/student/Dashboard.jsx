import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

export default function StudentDashboard() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate('/student/login', { replace: true })
  }

  return (
    <main className="mx-auto mt-16 max-w-2xl rounded-2xl border border-gray-200 bg-white p-8 shadow-card">
      <p className="text-sm font-semibold text-brand-600">Student portal</p>
      <h1 className="mt-1 text-3xl font-bold tracking-tight text-gray-900">You are signed in</h1>
      <p className="mt-3 text-gray-600">Start by completing your profile. Job search, applications, and events will be added in the next sections.</p>
      <Link to="/student/profile" className="mt-5 inline-flex rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
        Complete profile
      </Link>
      <button type="button" onClick={handleLogout} className="mt-6 rounded-xl border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">
        Sign out
      </button>
    </main>
  )
}
