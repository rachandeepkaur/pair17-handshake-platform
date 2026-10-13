import {
  LayoutDashboard,
  Briefcase,
  Users,
  CalendarDays,
  GraduationCap,
  MessageSquare,
  BarChart3,
  Building2,
  Shield,
  Settings,
} from 'lucide-react'

export const companyNav = [
  { to: '/company/dashboard', label: 'Home', icon: LayoutDashboard },
  { to: '/company/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/company/applicants', label: 'Applicants', icon: Users },
  { to: '/company/events', label: 'Events', icon: CalendarDays },
  { to: '/company/students', label: 'Students', icon: GraduationCap },
  { to: '/company/messages', label: 'Messages', icon: MessageSquare, badgeKey: 'unread_messages' },
  { to: '/company/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/company/profile', label: 'Company Profile', icon: Building2 },
  { to: '/company/team', label: 'Team & Permissions', icon: Shield },
  { to: '/company/settings', label: 'Settings', icon: Settings },
]
