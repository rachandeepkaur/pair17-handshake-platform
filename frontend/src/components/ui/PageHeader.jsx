import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

export default function PageHeader({ title, description, actions, backTo, backLabel = 'Back' }) {
  return (
    <div>
      {backTo && (
        <Link
          to={backTo}
          className="mb-2 inline-flex items-center gap-1 rounded-md text-sm font-medium text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft size={16} /> {backLabel}
        </Link>
      )}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          {description && <p className="mt-0.5 text-sm text-gray-500">{description}</p>}
        </div>
        {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
      </div>
    </div>
  )
}
