import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Briefcase, Search } from 'lucide-react'
import ErrorMessage from '../../components/common/ErrorMessage'
import StudentJobCard from '../../components/jobs/StudentJobCard'
import EmptyState from '../../components/ui/EmptyState'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { useFetch } from '../../hooks/useFetch'
import { getStudentJobs } from '../../services/studentJobService'
import { JOB_CATEGORIES } from '../../utils/constants'

export default function StudentJobs() {
  const [searchParams] = useSearchParams()
  const urlQuery = searchParams.get('q') || ''
  const [draft, setDraft] = useState({ q: urlQuery, category: '', city: '' })
  const [filters, setFilters] = useState({ q: urlQuery, category: '', city: '' })
  const { data, loading, error } = useFetch(() => getStudentJobs(filters), [filters])

  useEffect(() => {
    setDraft((current) => ({ ...current, q: urlQuery }))
    setFilters((current) => ({ ...current, q: urlQuery }))
  }, [urlQuery])

  const change = (event) => setDraft((current) => ({ ...current, [event.target.name]: event.target.value }))
  const submit = (event) => {
    event.preventDefault()
    setFilters({ q: draft.q.trim(), category: draft.category, city: draft.city.trim() })
  }
  const clear = () => {
    const empty = { q: '', category: '', city: '' }
    setDraft(empty)
    setFilters(empty)
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader title="Find jobs" description="Search current opportunities posted by employers." />
      <form onSubmit={submit} className="grid grid-cols-1 gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-card md:grid-cols-[1fr_11rem_11rem_auto]">
        <label className="relative">
          <span className="sr-only">Search jobs or companies</span>
          <Search size={18} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input name="q" value={draft.q} onChange={change} placeholder="Job title or company" className="h-10 w-full rounded-xl border border-gray-300 pl-10 pr-3 text-sm focus:border-brand-400" />
        </label>
        <select name="category" value={draft.category} onChange={change} aria-label="Job category" className="h-10 rounded-xl border border-gray-300 bg-white px-3 text-sm focus:border-brand-400">
          <option value="">All categories</option>
          {JOB_CATEGORIES.map((category) => <option key={category.value} value={category.value}>{category.label}</option>)}
        </select>
        <input name="city" value={draft.city} onChange={change} placeholder="City" aria-label="City" className="h-10 rounded-xl border border-gray-300 px-3 text-sm focus:border-brand-400" />
        <div className="flex gap-2">
          <button type="submit" className="h-10 rounded-xl bg-brand-600 px-4 text-sm font-semibold text-white hover:bg-brand-700">Search</button>
          {(filters.q || filters.category || filters.city) && <button type="button" onClick={clear} className="h-10 rounded-xl border border-gray-300 px-3 text-sm font-medium text-gray-700 hover:bg-gray-50">Clear</button>}
        </div>
      </form>
      {error && <ErrorMessage message={error} />}
      {loading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2"><Skeleton className="h-56 rounded-2xl" /><Skeleton className="h-56 rounded-2xl" /></div>
      ) : data?.items?.length ? (
        <>
          <p className="text-sm text-gray-500">{data.total} {data.total === 1 ? 'job' : 'jobs'} found</p>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">{data.items.map((job) => <StudentJobCard key={job.id} job={job} />)}</div>
        </>
      ) : !error && (
        <EmptyState icon={Briefcase} title="No matching jobs" description="Try a different job title, company, category, or city." />
      )}
    </div>
  )
}
