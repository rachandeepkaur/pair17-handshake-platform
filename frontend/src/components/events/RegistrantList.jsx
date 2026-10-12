import { Link } from 'react-router-dom'
import { Users } from 'lucide-react'
import Avatar from '../ui/Avatar'
import EmptyState from '../ui/EmptyState'
import { formatDate } from '../../utils/format'

export default function RegistrantList({ registrations }) {
  if (registrations.length === 0) {
    return (
      <div className="p-5">
        <EmptyState
          icon={Users}
          title="No registrations yet"
          description="Students who register for this event will appear here."
        />
      </div>
    )
  }

  return (
    <ul className="divide-y divide-gray-100">
      {registrations.map(({ id, registered_at: registeredAt, student }) => (
        <li key={id}>
          <Link
            to={`/company/students/${student.account_id}`}
            className="flex items-center gap-3 px-5 py-3 hover:bg-gray-50/60"
          >
            <Avatar name={student.name} size="sm" />
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium text-gray-900">{student.name}</span>
              <span className="block truncate text-xs text-gray-500">
                {student.college_name}
                {student.major ? ` · ${student.major}` : ''}
              </span>
            </span>
            <span className="hidden text-xs text-gray-500 sm:block">
              Registered {formatDate(registeredAt)}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  )
}
