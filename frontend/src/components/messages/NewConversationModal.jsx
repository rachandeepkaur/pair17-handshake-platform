import { useEffect, useState } from 'react'
import { Search } from 'lucide-react'
import Modal from '../common/Modal'
import Avatar from '../ui/Avatar'
import Button from '../ui/Button'
import { errorMessage } from '../../services/api'
import { searchStudents } from '../../services/studentService'

export default function NewConversationModal({ open, onClose, onPick }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(null)

  useEffect(() => {
    if (!open) return undefined
    let cancelled = false
    setLoading(true)
    // Debounce so typing doesn't fire a request per keystroke.
    const timer = setTimeout(() => {
      searchStudents({ q: query.trim(), limit: 8 })
        .then((page) => !cancelled && setResults(page.items))
        .catch((err) => !cancelled && setError(errorMessage(err)))
        .finally(() => !cancelled && setLoading(false))
    }, 250)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [query, open])

  const pick = async (student) => {
    setStarting(student.account_id)
    setError('')
    try {
      await onPick(student)
    } catch (err) {
      setError(errorMessage(err, 'Could not start the conversation'))
    } finally {
      setStarting(null)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New message" footer={<Button variant="outline" onClick={onClose}>Cancel</Button>}>
      <div className="relative mt-2">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
        <input
          type="search"
          autoFocus
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search students by name"
          aria-label="Search students by name"
          className="h-10 w-full rounded-xl border border-gray-300 pl-9 pr-3 text-sm text-gray-900 focus:border-brand-400"
        />
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <ul className="mt-3 max-h-72 divide-y divide-gray-100 overflow-y-auto">
        {!loading && results.length === 0 && <li className="py-6 text-center text-gray-500">No students found.</li>}
        {results.map((student) => (
          <li key={student.account_id}>
            <button
              onClick={() => pick(student)}
              disabled={starting !== null}
              className="flex w-full items-center gap-3 rounded-lg px-2 py-2.5 text-left hover:bg-gray-50 disabled:opacity-60"
            >
              <Avatar name={student.name} size="sm" />
              <span className="min-w-0 flex-1">
                <span className="block truncate font-medium text-gray-900">{student.name}</span>
                <span className="block truncate text-xs text-gray-500">{student.college_name}</span>
              </span>
              {starting === student.account_id && <span className="text-xs text-gray-500">Opening…</span>}
            </button>
          </li>
        ))}
      </ul>
    </Modal>
  )
}
