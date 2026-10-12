import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Menu, Search, ChevronDown, LogOut, Building2 } from 'lucide-react'
import Avatar from '../ui/Avatar'
import { useAuth } from '../../hooks/useAuth'
import { apiUrl } from '../../services/api'

function useOutsideClose(onClose) {
  const ref = useRef(null)
  useEffect(() => {
    function handle(event) {
      if (ref.current && !ref.current.contains(event.target)) onClose()
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [onClose])
  return ref
}

function CompanyMark({ name, pictureUrl }) {
  return pictureUrl ? (
    <img src={apiUrl(pictureUrl)} alt="" className="h-8 w-8 rounded-full object-cover" />
  ) : (
    <Avatar name={name} size="sm" />
  )
}

export default function Navbar({ onMenuClick, company }) {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const [query, setQuery] = useState('')
  const menuRef = useOutsideClose(() => setMenuOpen(false))

  const name = company?.company_name || 'Your company'

  const handleSearch = (event) => {
    event.preventDefault()
    const q = query.trim()
    navigate(q ? `/company/students?q=${encodeURIComponent(q)}` : '/company/students')
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-gray-200 bg-white/90 px-4 backdrop-blur lg:px-6">
      <button
        onClick={onMenuClick}
        className="rounded-lg p-2 text-gray-600 hover:bg-gray-100 lg:hidden"
        aria-label="Open navigation"
      >
        <Menu size={20} />
      </button>

      <form onSubmit={handleSearch} role="search" className="relative hidden flex-1 md:block">
        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search students by name…"
          aria-label="Search students by name"
          className="h-10 w-full max-w-md rounded-xl border border-gray-200 bg-gray-50 pl-10 pr-4 text-sm placeholder:text-gray-400 focus:border-brand-400 focus:bg-white"
        />
      </form>

      <div className="relative ml-auto" ref={menuRef}>
        <button
          onClick={() => setMenuOpen((open) => !open)}
          aria-haspopup="menu"
          aria-expanded={menuOpen}
          className="flex items-center gap-2 rounded-xl p-1 pr-2 hover:bg-gray-100"
        >
          <CompanyMark name={name} pictureUrl={company?.profile_picture_url} />
          <span className="hidden max-w-[12rem] truncate text-sm font-medium text-gray-700 sm:inline">
            {name}
          </span>
          <ChevronDown size={16} className="text-gray-400" aria-hidden="true" />
        </button>
        {menuOpen && (
          <div
            role="menu"
            className="absolute right-0 mt-2 w-60 animate-fade-in rounded-xl border border-gray-200 bg-white p-1.5 shadow-pop"
          >
            <div className="border-b border-gray-100 px-3 py-2">
              <p className="truncate text-sm font-medium text-gray-900">{name}</p>
              <p className="truncate text-xs text-gray-500">{company?.email}</p>
            </div>
            <Link
              to="/company/profile"
              role="menuitem"
              onClick={() => setMenuOpen(false)}
              className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              <Building2 size={16} aria-hidden="true" />
              Company profile
            </Link>
            <button
              role="menuitem"
              onClick={handleLogout}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              <LogOut size={16} aria-hidden="true" />
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
