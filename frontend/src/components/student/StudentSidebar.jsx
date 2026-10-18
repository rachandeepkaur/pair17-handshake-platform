import { Link, NavLink } from 'react-router-dom'
import { Bot, Briefcase, CalendarDays, ClipboardList, GraduationCap, LayoutDashboard, MessageSquare, Sparkles, UserRound, X } from 'lucide-react'

const navigation = [
  { to: '/student/dashboard', label: 'Home', icon: LayoutDashboard },
  { to: '/student/assistant', label: 'Career assistant', icon: Bot },
  { to: '/student/jobs', label: 'Find jobs', icon: Briefcase },
  { to: '/student/applications', label: 'My applications', icon: ClipboardList },
  { to: '/student/events', label: 'Events', icon: CalendarDays },
  { to: '/student/messages', label: 'Inbox', icon: MessageSquare, badgeKey: 'unreadMessages' },
  { to: '/student/people', label: 'People', icon: GraduationCap },
  { to: '/student/profile', label: 'My profile', icon: UserRound },
]

export default function StudentSidebar({ open, onClose, student, unreadMessages = 0 }) {
  return (
    <>
      {open && <div className="fixed inset-0 z-30 bg-gray-900/40 lg:hidden" onClick={onClose} aria-hidden="true" />}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-gray-200 bg-white transition-transform lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}
        aria-label="Student navigation"
      >
        <div className="flex h-16 items-center justify-between px-5">
          <Link to="/student/dashboard" onClick={onClose} className="flex items-center gap-2 rounded-lg">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-brand-600 text-white"><Sparkles size={18} strokeWidth={2.5} aria-hidden="true" /></span>
            <span className="text-lg font-bold tracking-tight">Hirely</span>
          </Link>
          <button type="button" onClick={onClose} className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 lg:hidden" aria-label="Close navigation"><X size={18} /></button>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
          {navigation.map(({ to, label, icon: Icon, badgeKey }) => (
            <NavLink key={to} to={to} onClick={onClose} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors ${isActive ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}`}>
              <Icon size={18} strokeWidth={2} aria-hidden="true" />
              <span>{label}</span>
              {badgeKey && unreadMessages > 0 && (
                <span className="ml-auto inline-flex min-w-5 items-center justify-center rounded-full bg-brand-600 px-1.5 py-0.5 text-xs font-semibold text-white" aria-label={`${unreadMessages} unread messages`}>
                  {unreadMessages > 99 ? '99+' : unreadMessages}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
        {student && (
          <div className="border-t border-gray-100 p-3">
            <Link to="/student/profile" onClick={onClose} className="block rounded-xl bg-gradient-to-br from-brand-600 to-brand-700 p-4 text-white">
              <p className="text-sm font-semibold">Complete your profile</p>
              <p className="mt-1 text-xs text-brand-100">Help employers learn about your education and skills.</p>
            </Link>
          </div>
        )}
      </aside>
    </>
  )
}
