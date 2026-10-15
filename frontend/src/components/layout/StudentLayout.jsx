import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import StudentNavbar from '../student/StudentNavbar'
import StudentSidebar from '../student/StudentSidebar'
import { useFetch } from '../../hooks/useFetch'
import { getMyProfile } from '../../services/studentProfileService'

export default function StudentLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { data: student, error, reload } = useFetch(getMyProfile, [])
  return (
    <div className="min-h-screen bg-canvas">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:shadow-pop">Skip to content</a>
      <StudentSidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} student={student} />
      <div className="lg:pl-64">
        <StudentNavbar onMenuClick={() => setSidebarOpen(true)} student={student} />
        <main id="main" className="mx-auto max-w-7xl px-4 py-6 lg:px-8"><Outlet context={{ student, studentError: error, reloadStudent: reload }} /></main>
      </div>
    </div>
  )
}
