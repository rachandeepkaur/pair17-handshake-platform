import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="max-w-md mx-auto mt-16 p-6 text-center">
      <h1 className="text-xl font-semibold">Page not found</h1>
      <Link to="/login" className="mt-4 inline-block text-blue-600">
        Back to sign in
      </Link>
    </div>
  )
}
