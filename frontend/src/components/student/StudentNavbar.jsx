import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ChevronDown, LogOut, Menu, Search, UserRound } from 'lucide-react'
import Avatar from '../ui/Avatar'
import { useAuth } from '../../hooks/useAuth'
import { apiUrl } from '../../services/api'

function useOutsideClose(onClose) {
  const ref = useRef(null)
  useEffect(() => {
    const close = (event) => ref.current && !ref.current.contains(event.target) && onClose()
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [onClose])
  return ref
}

export default function StudentNavbar({ onMenuClick, student }) {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const [query, setQuery] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useOutsideClose(() => setMenuOpen(false))
  const name = student?.name || 'Your profile'

  const searchJobs = (event) => {
    event.preventDefault()
    const q = query.trim()
    navigate(q ? `/student/jobs?q=${encodeURIComponent(q)}` : '/student/jobs')
  }
  const signOut = () => {
    logout()
    navigate('/student/login')
  }

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-gray-200 bg-white/90 px-4 backdrop-blur lg:px-6">
      <button type="button" onClick={onMenuClick} className="rounded-lg p-2 text-gray-600 hover:bg-gray-100 lg:hidden" aria-label="Open navigation"><Menu size={20} /></button>
      <form onSubmit={searchJobs} role="search" className="relative hidden flex-1 md:block">
        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
        <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search jobs or companies…" aria-label="Search jobs or companies" className="h-10 w-full max-w-md rounded-xl border border-gray-200 bg-gray-50 pl-10 pr-4 text-sm placeholder:text-gray-400 focus:border-brand-400 focus:bg-white" />
      </form>
      <div className="relative ml-auto" ref={menuRef}>
        <button type="button" onClick={() => setMenuOpen((open) => !open)} aria-haspopup="menu" aria-expanded={menuOpen} className="flex items-center gap-2 rounded-xl p-1 pr-2 hover:bg-gray-100">
          {student?.profile_picture_url ? <img src={apiUrl(student.profile_picture_url)} alt="" className="h-8 w-8 rounded-full object-cover" /> : <Avatar name={name} size="sm" />}
          <span className="hidden max-w-[12rem] truncate text-sm font-medium text-gray-700 sm:inline">{name}</span>
          <ChevronDown size={16} className="text-gray-400" aria-hidden="true" />
        </button>
        {menuOpen && <div role="menu" className="absolute right-0 mt-2 w-60 animate-fade-in rounded-xl border border-gray-200 bg-white p-1.5 shadow-pop">
          <div className="border-b border-gray-100 px-3 py-2"><p className="truncate text-sm font-medium text-gray-900">{name}</p><p className="truncate text-xs text-gray-500">{student?.email}</p></div>
          <Link to="/student/profile" role="menuitem" onClick={() => setMenuOpen(false)} className="mt-1 flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"><UserRound size={16} aria-hidden="true" /> My profile</Link>
          <button type="button" role="menuitem" onClick={signOut} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"><LogOut size={16} aria-hidden="true" /> Sign out</button>
        </div>}
      </div>
    </header>
  )
}
