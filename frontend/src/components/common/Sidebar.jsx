import { Link, NavLink } from 'react-router-dom'
import { Sparkles, X } from 'lucide-react'
import { companyNav } from './navConfig'

function NavItem({ to, label, icon: Icon, onClick, badge }) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors ${
          isActive ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
        }`
      }
    >
      <Icon size={18} strokeWidth={2} aria-hidden="true" />
      <span className="flex-1">{label}</span>
      {badge > 0 && (
        <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-brand-600 px-1.5 text-xs font-semibold text-white">
          {badge}
          <span className="sr-only"> unread</span>
        </span>
      )}
    </NavLink>
  )
}

export default function Sidebar({ open, onClose, company }) {
  const profileCompletion = company?.profile_completion
  return (
    <>
      {open && (
        <div className="fixed inset-0 z-30 bg-gray-900/40 lg:hidden" onClick={onClose} aria-hidden="true" />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-gray-200 bg-white transition-transform lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Primary navigation"
      >
        <div className="flex h-16 items-center justify-between px-5">
          <Link to="/company/dashboard" className="flex items-center gap-2 rounded-lg">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-brand-600 text-white">
              <Sparkles size={18} strokeWidth={2.5} aria-hidden="true" />
            </span>
            <span className="text-lg font-bold tracking-tight">Hirely</span>
          </Link>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 lg:hidden"
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
          {companyNav.map(({ badgeKey, ...item }) => (
            <NavItem key={item.to} {...item} onClick={onClose} badge={badgeKey ? company?.[badgeKey] : 0} />
          ))}
        </nav>

        {profileCompletion != null && profileCompletion < 100 && (
          <div className="border-t border-gray-100 p-3">
            <Link
              to="/company/profile"
              onClick={onClose}
              className="block rounded-xl bg-gradient-to-br from-brand-600 to-brand-700 p-4 text-white"
            >
              <p className="text-sm font-semibold">Profile {profileCompletion}% complete</p>
              <p className="mt-1 text-xs text-brand-100">
                Add a description, contact info, and logo to attract more applicants.
              </p>
            </Link>
          </div>
        )}
      </aside>
    </>
  )
}
