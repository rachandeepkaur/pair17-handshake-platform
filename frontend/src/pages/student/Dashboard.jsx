import { Link, useOutletContext } from 'react-router-dom'
import { Briefcase, ClipboardList, FileCheck2, Search, UserRound } from 'lucide-react'
import Card, { CardHeader } from '../../components/ui/Card'
import EmptyState from '../../components/ui/EmptyState'
import StatCard from '../../components/ui/StatCard'
import StatusBadge from '../../components/ui/StatusBadge'
import { RowSkeleton, StatCardSkeleton } from '../../components/ui/Skeleton'
import { useFetch } from '../../hooks/useFetch'
import { getMyApplications } from '../../services/studentApplicationService'
import { getStudentJobs } from '../../services/studentJobService'
import { formatDate } from '../../utils/format'

const completedFields = ['career_objective', 'degree', 'major', 'graduation_year', 'skills', 'city']

export default function StudentDashboard() {
  const { student, studentError } = useOutletContext()
  const applications = useFetch(getMyApplications, [])
  const jobs = useFetch(() => getStudentJobs({ limit: 3 }), [])
  const profileCompletion = student ? Math.round((completedFields.filter((field) => student[field]).length / completedFields.length) * 100) : 0
  const pendingCount = applications.data?.filter((application) => application.status === 'Pending').length || 0

  return (
    <div className="space-y-6">
      {studentError && <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">Your profile summary could not be loaded.</p>}
      <section className="rounded-2xl bg-gradient-to-br from-brand-600 via-brand-600 to-brand-800 p-6 text-white lg:p-8">
        <p className="text-sm font-medium text-brand-100">Welcome back</p>
        <h1 className="mt-1 text-2xl font-bold lg:text-3xl">{student?.name || 'Student'}</h1>
        <p className="mt-1 text-sm text-brand-100">Find opportunities, apply with confidence, and track your progress.</p>
        <div className="mt-5 flex flex-wrap gap-2">
          <Link to="/student/jobs" className="inline-flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2 text-sm font-medium text-white hover:bg-white/25"><Search size={18} aria-hidden="true" /> Find jobs</Link>
          <Link to="/student/profile" className="inline-flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2 text-sm font-medium text-white hover:bg-white/25"><UserRound size={18} aria-hidden="true" /> My profile</Link>
        </div>
      </section>
      {student && profileCompletion < 100 && <Card className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
        <div className="flex-1"><div className="flex items-center justify-between gap-3"><h2 className="font-semibold text-gray-900">Complete your profile</h2><span className="text-lg font-bold text-brand-600">{profileCompletion}%</span></div><div className="mt-3 h-2 overflow-hidden rounded-full bg-gray-100" role="progressbar" aria-label="Profile completion" aria-valuenow={profileCompletion} aria-valuemin="0" aria-valuemax="100"><div className="h-full rounded-full bg-gradient-to-r from-brand-500 to-accent-500" style={{ width: `${profileCompletion}%` }} /></div></div>
        <Link to="/student/profile" className="rounded-xl border border-gray-300 px-4 py-2 text-center text-sm font-semibold text-gray-700 hover:bg-gray-50">Finish profile</Link>
      </Card>}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {applications.loading || jobs.loading ? <><StatCardSkeleton /><StatCardSkeleton /><StatCardSkeleton /></> : <><StatCard icon={ClipboardList} label="Applications" value={applications.data?.length || 0} tone="brand" /><StatCard icon={FileCheck2} label="Pending review" value={pendingCount} tone="amber" /><StatCard icon={Briefcase} label="Open opportunities" value={jobs.data?.total || 0} tone="cyan" /></>}
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card><CardHeader title="Recent applications" action={<Link to="/student/applications" className="text-sm font-medium text-brand-600 hover:text-brand-700">View all</Link>} />
          {applications.loading ? <div className="px-5"><RowSkeleton /><RowSkeleton /></div> : applications.data?.length ? <ul className="divide-y divide-gray-100">{applications.data.slice(0, 4).map((application) => <li key={application.id} className="flex items-center gap-3 px-5 py-4"><span className="min-w-0 flex-1"><span className="block truncate text-sm font-medium text-gray-900">{application.job_title}</span><span className="block truncate text-xs text-gray-500">{application.company_name} · Applied {formatDate(application.applied_at)}</span></span><StatusBadge status={application.status} /></li>)}</ul> : <div className="p-5"><EmptyState icon={ClipboardList} title="No applications yet" description="Browse jobs to apply to your first opportunity." action={<Link to="/student/jobs" className="text-sm font-semibold text-brand-600 hover:text-brand-700">Browse jobs</Link>} /></div>}
        </Card>
        <Card><CardHeader title="Opportunities for you" action={<Link to="/student/jobs" className="text-sm font-medium text-brand-600 hover:text-brand-700">Browse all</Link>} />
          {jobs.loading ? <div className="px-5"><RowSkeleton /><RowSkeleton /></div> : jobs.data?.items?.length ? <ul className="divide-y divide-gray-100">{jobs.data.items.map((job) => <li key={job.id}><Link to={`/student/jobs/${job.id}`} className="block px-5 py-4 hover:bg-gray-50"><span className="block truncate text-sm font-medium text-gray-900">{job.title}</span><span className="mt-1 block truncate text-xs text-gray-500">{job.company_name} · {job.city}</span></Link></li>)}</ul> : <div className="p-5"><EmptyState icon={Briefcase} title="No open jobs right now" description="Check back soon for new opportunities." /></div>}
        </Card>
      </div>
    </div>
  )
}
