import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { GraduationCap, Search, X } from 'lucide-react'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import ErrorMessage from '../../components/common/ErrorMessage'
import Pagination from '../../components/common/Pagination'
import StudentCard from '../../components/students/StudentCard'
import { useFetch } from '../../hooks/useFetch'
import { searchStudents } from '../../services/studentService'

const PAGE_SIZE = 12
const FIELDS = [
  { name: 'q', label: 'Name', placeholder: 'e.g. Maya' },
  { name: 'college', label: 'College', placeholder: 'e.g. San Jose State' },
  { name: 'skills', label: 'Skills', placeholder: 'e.g. Python, SQL' },
]

export default function StudentSearch() {
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = Object.fromEntries(FIELDS.map(({ name }) => [name, searchParams.get(name) || '']))
  const offset = Number(searchParams.get('offset')) || 0
  const [draft, setDraft] = useState(filters)

  // Keep the inputs in sync when the URL changes from outside this form,
  // e.g. a search submitted from the top bar.
  const paramKey = searchParams.toString()
  useEffect(() => {
    setDraft(Object.fromEntries(FIELDS.map(({ name }) => [name, searchParams.get(name) || ''])))
  }, [paramKey]) // eslint-disable-line react-hooks/exhaustive-deps

  const { data, loading, error } = useFetch(
    () => searchStudents({ ...filters, limit: PAGE_SIZE, offset }),
    [paramKey],
  )

  const apply = (next, nextOffset = 0) => {
    const params = Object.fromEntries(Object.entries(next).filter(([, value]) => value.trim()))
    if (nextOffset) params.offset = String(nextOffset)
    setSearchParams(params)
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    apply(draft)
  }

  const hasFilters = FIELDS.some(({ name }) => filters[name])

  return (
    <div className="space-y-5">
      <PageHeader title="Students" description="Search students by name, college, or skillset and view their profiles." />

      <Card className="p-5">
        <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_1fr_1fr_auto] sm:items-end" role="search">
          {FIELDS.map(({ name, label, placeholder }) => (
            <div key={name}>
              <label htmlFor={`search-${name}`} className="mb-1 block text-sm font-medium text-gray-700">
                {label}
              </label>
              <input
                id={`search-${name}`}
                value={draft[name]}
                onChange={(event) => setDraft((prev) => ({ ...prev, [name]: event.target.value }))}
                placeholder={placeholder}
                className="h-10 w-full rounded-xl border border-gray-300 px-3 text-sm focus:border-brand-400"
              />
            </div>
          ))}
          <div className="flex gap-2">
            <Button type="submit" icon={Search}>
              Search
            </Button>
            {hasFilters && (
              <Button type="button" variant="ghost" icon={X} onClick={() => apply({ q: '', college: '', skills: '' })}>
                Clear
              </Button>
            )}
          </div>
        </form>
      </Card>

      <ErrorMessage message={error} />

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-2xl" />
          ))}
        </div>
      ) : data?.items.length === 0 ? (
        <EmptyState
          icon={GraduationCap}
          title={hasFilters ? 'No students match your search' : 'No students yet'}
          description={hasFilters ? 'Try fewer filters or a different spelling.' : 'Enrolled students will appear here.'}
        />
      ) : (
        data && (
          <>
            <p className="text-sm text-gray-500">
              {data.total} student{data.total === 1 ? '' : 's'} found
            </p>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data.items.map((student) => (
                <StudentCard key={student.account_id} student={student} />
              ))}
            </div>
            <Pagination
              total={data.total}
              limit={data.limit}
              offset={data.offset}
              onChange={(nextOffset) => apply(filters, nextOffset)}
            />
          </>
        )
      )}
    </div>
  )
}
