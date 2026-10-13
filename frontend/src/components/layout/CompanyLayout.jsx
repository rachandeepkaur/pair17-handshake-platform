import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from '../common/Sidebar'
import Navbar from '../common/Navbar'
import { useFetch } from '../../hooks/useFetch'
import { getDashboard } from '../../services/companyService'

export default function CompanyLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { data: company, error, reload, setData } = useFetch(getDashboard, [])

  // Keep the unread-messages badge current without a full reload.
  useEffect(() => {
    const timer = setInterval(() => getDashboard().then(setData).catch(() => {}), 30_000)
    return () => clearInterval(timer)
  }, [setData])

  return (
    <div className="min-h-screen bg-canvas">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:shadow-pop"
      >
        Skip to content
      </a>
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        company={company}
      />

      <div className="lg:pl-64">
        <Navbar onMenuClick={() => setSidebarOpen(true)} company={company} />
        <main id="main" className="mx-auto max-w-7xl px-4 py-6 lg:px-8">
          {/* Pages read the company summary from here and call `reloadCompany`
              after changes that affect it (new job, profile edit, …). */}
          <Outlet context={{ company, companyError: error, reloadCompany: reload }} />
        </main>
      </div>
    </div>
  )
}
