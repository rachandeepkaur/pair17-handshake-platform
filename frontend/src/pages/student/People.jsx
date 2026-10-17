import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { GraduationCap, Search, X } from 'lucide-react'
import Avatar from '../../components/ui/Avatar'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import EmptyState from '../../components/ui/EmptyState'
import Pagination from '../../components/common/Pagination'
import ErrorMessage from '../../components/common/ErrorMessage'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { useFetch } from '../../hooks/useFetch'
import { searchStudents } from '../../services/studentService'

const PAGE_SIZE = 12
const FIELDS = [
  { name: 'q', label: 'Name', placeholder: 'e.g. Maya' },
  { name: 'college', label: 'College', placeholder: 'e.g. San Jose State' },
  { name: 'major', label: 'Major', placeholder: 'e.g. Computer Science' },
]

export default function People() {
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = Object.fromEntries(FIELDS.map(({ name }) => [name, searchParams.get(name) || '']))
  const offset = Number(searchParams.get('offset')) || 0
  const [draft, setDraft] = useState(filters)
  const paramKey = searchParams.toString()

  useEffect(() => {
    setDraft(Object.fromEntries(FIELDS.map(({ name }) => [name, searchParams.get(name) || ''])))
  }, [paramKey]) // Keep form fields in sync with browser navigation.

  const { data, loading, error } = useFetch(
    () => searchStudents({ ...filters, limit: PAGE_SIZE, offset }),
    [paramKey],
  )

  const apply = (next, nextOffset = 0) => {
    const params = Object.fromEntries(
      Object.entries(next).filter(([, value]) => value.trim()),
    )
    if (nextOffset) params.offset = String(nextOffset)
    setSearchParams(params)
  }

  const submit = (event) => {
    event.preventDefault()
    apply(draft)
  }

  const hasFilters = FIELDS.some(({ name }) => filters[name])

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader title="People" description="Browse enrolled students by name, college, or major." />

      <Card className="p-5">
        <form onSubmit={submit} className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_1fr_1fr_auto] sm:items-end" role="search">
          {FIELDS.map(({ name, label, placeholder }) => (
            <div key={name}>
              <label htmlFor={`people-${name}`} className="mb-1 block text-sm font-medium text-gray-700">
                {label}
              </label>
              <input
                id={`people-${name}`}
                value={draft[name]}
                onChange={(event) => setDraft((current) => ({ ...current, [name]: event.target.value }))}
                placeholder={placeholder}
                className="h-10 w-full rounded-xl border border-gray-300 px-3 text-sm focus:border-brand-400"
              />
            </div>
          ))}
          <div className="flex gap-2">
            <Button type="submit" icon={Search}>Search</Button>
            {hasFilters && <Button type="button" variant="ghost" icon={X} onClick={() => apply({ q: '', college: '', major: '' })}>Clear</Button>}
          </div>
        </form>
      </Card>

      {error && <ErrorMessage message={error} />}

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => <Skeleton key={index} className="h-40 rounded-2xl" />)}
        </div>
      ) : data?.items.length ? (
        <>
          <p className="text-sm text-gray-500">{data.total} student{data.total === 1 ? '' : 's'} found</p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((student) => <DirectoryCard key={student.account_id} student={student} />)}
          </div>
          <Pagination total={data.total} limit={data.limit} offset={data.offset} onChange={(nextOffset) => apply(filters, nextOffset)} />
        </>
      ) : !error && (
        <EmptyState
          icon={GraduationCap}
          title={hasFilters ? 'No students match your search' : 'No students yet'}
          description={hasFilters ? 'Try fewer filters or a different spelling.' : 'Enrolled students will appear here.'}
        />
      )}
    </div>
  )
}

function DirectoryCard({ student }) {
  const program = [student.degree, student.major].filter(Boolean).join(' · ')

  return (
    <Card className="h-full p-5">
      <div className="flex items-center gap-3">
        <Avatar name={student.name} />
        <div className="min-w-0">
          <p className="truncate font-medium text-gray-900">{student.name}</p>
          <p className="truncate text-sm text-gray-500">{student.college_name}</p>
        </div>
      </div>
      {(program || student.graduation_year) && (
        <p className="mt-3 text-sm text-gray-600">
          {program}
          {student.graduation_year && ` · ${student.graduation_year}`}
        </p>
      )}
    </Card>
  )
}
