import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function NotFound() {
  const { isAuthenticated, role } = useAuth()
  const home = isAuthenticated && role === 'company' ? '/company/dashboard' : '/login'

  return (
    <div className="mx-auto mt-16 max-w-md p-6 text-center">
      <p className="text-sm font-semibold text-brand-600">404</p>
      <h1 className="mt-1 text-xl font-semibold text-gray-900">Page not found</h1>
      <p className="mt-2 text-sm text-gray-500">The page you’re looking for doesn’t exist or was moved.</p>
      <Link to={home} className="mt-4 inline-block rounded-md text-sm font-medium text-brand-600 hover:text-brand-700">
        {home === '/login' ? 'Back to sign in' : 'Back to dashboard'}
      </Link>
    </div>
  )
}
