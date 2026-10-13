import { useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import { Briefcase, CalendarDays, CheckCircle2, Circle, Mail, MapPin, Pencil } from 'lucide-react'
import Card, { CardHeader } from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import ErrorMessage from '../../components/common/ErrorMessage'
import CompanyProfileForm from '../../components/profile/CompanyProfileForm'
import ProfilePicture from '../../components/profile/ProfilePicture'
import { useFetch } from '../../hooks/useFetch'
import { usePermissions } from '../../hooks/usePermissions'
import { getProfile, updateProfile, uploadPicture } from '../../services/companyService'
import { getMyJobs } from '../../services/jobService'
import { getMyEvents } from '../../services/eventService'
import { jobCategoryLabel } from '../../utils/constants'
import { formatDate, isOnOrAfterToday } from '../../utils/format'

function Checklist({ profile }) {
  const items = [
    ['Company name and location', profile.company_name && profile.location],
    ['Company description', profile.description],
    ['Contact information', profile.contact_info],
    ['Profile picture', profile.profile_picture_url],
  ]
  return (
    <Card>
      <CardHeader title="Profile checklist" />
      <ul className="space-y-2.5 px-5 py-4">
        {items.map(([label, done]) => (
          <li key={label} className="flex items-center gap-2 text-sm">
            {done ? (
              <CheckCircle2 size={18} className="text-emerald-600" aria-hidden="true" />
            ) : (
              <Circle size={18} className="text-gray-300" aria-hidden="true" />
            )}
            <span className={done ? 'text-gray-700' : 'text-gray-500'}>{label}</span>
            <span className="sr-only">{done ? '(complete)' : '(missing)'}</span>
          </li>
        ))}
      </ul>
    </Card>
  )
}

export default function CompanyProfile() {
  const { reloadCompany } = useOutletContext()
  const { data: profile, loading, error, setData } = useFetch(getProfile, [])
  const jobs = useFetch(getMyJobs, [])
  const events = useFetch(getMyEvents, [])
  const [editing, setEditing] = useState(false)
  const { can } = usePermissions()
  const canEdit = can('profile:write')
  const [saved, setSaved] = useState(false)

  const applyUpdate = (updated) => {
    setData(updated)
    reloadCompany()
  }

  const handleSave = async (values) => {
    applyUpdate(await updateProfile(values))
    setEditing(false)
    setSaved(true)
  }

  const handleUpload = async (file) => applyUpdate(await uploadPicture(file))

  if (error) return <ErrorMessage message={error} />
  if (loading || !profile) return <Skeleton className="h-96 rounded-2xl" />

  const openJobs = (jobs.data || []).filter((job) => isOnOrAfterToday(job.deadline))
  const upcomingEvents = (events.data || []).filter((event) => isOnOrAfterToday(event.event_date))

  return (
    <div className="space-y-6">
      <PageHeader
        title="Company Profile"
        description="This is how students see your company."
        actions={
          !editing && canEdit && (
            <Button
              variant="outline"
              icon={Pencil}
              onClick={() => {
                setEditing(true)
                setSaved(false)
              }}
            >
              Edit profile
            </Button>
          )
        }
      />

      {saved && (
        <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm text-emerald-800">
          Profile saved.
        </p>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card className="overflow-hidden">
            <div className="h-28 bg-gradient-to-r from-brand-600 via-brand-500 to-accent-500" aria-hidden="true" />
            <div className="px-6 pb-6">
              <div className="-mt-10 mb-4 rounded-2xl bg-white p-1 shadow-card sm:inline-block">
                <ProfilePicture name={profile.company_name} pictureUrl={profile.profile_picture_url} onUpload={handleUpload} canEdit={canEdit} />
              </div>

              {editing ? (
                <CompanyProfileForm profile={profile} onSave={handleSave} onCancel={() => setEditing(false)} />
              ) : (
                <div className="space-y-4">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">{profile.company_name}</h2>
                    <p className="mt-1 flex items-center gap-1.5 text-sm text-gray-600">
                      <MapPin size={16} className="text-gray-400" aria-hidden="true" /> {profile.location}
                    </p>
                  </div>
                  <div>
                    <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">About</h3>
                    <p className="whitespace-pre-line text-sm text-gray-700">
                      {profile.description || <span className="text-gray-400">No description yet.</span>}
                    </p>
                  </div>
                  <div>
                    <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">Contact</h3>
                    <p className="flex items-center gap-1.5 text-sm text-gray-700">
                      <Mail size={16} className="text-gray-400" aria-hidden="true" />
                      {profile.contact_info || <span className="text-gray-400">No contact information yet.</span>}
                    </p>
                    <p className="mt-1 text-xs text-gray-500">Account email: {profile.email}</p>
                  </div>
                </div>
              )}
            </div>
          </Card>

          <Card>
            <CardHeader title="Open jobs" subtitle={`${openJobs.length} accepting applications`} />
            {openJobs.length === 0 ? (
              <p className="px-5 py-4 text-sm text-gray-500">No open jobs right now.</p>
            ) : (
              <ul className="divide-y divide-gray-100">
                {openJobs.map((job) => (
                  <li key={job.id}>
                    <Link to={`/company/jobs/${job.id}`} className="flex items-center gap-3 px-5 py-3 hover:bg-gray-50/60">
                      <Briefcase size={16} className="text-gray-400" aria-hidden="true" />
                      <span className="min-w-0 flex-1 truncate text-sm font-medium text-gray-900">{job.title}</span>
                      <span className="text-xs text-gray-500">
                        {jobCategoryLabel(job.category)} · {job.city}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          <Checklist profile={profile} />
          <Card>
            <CardHeader title="Upcoming events" />
            {upcomingEvents.length === 0 ? (
              <p className="px-5 py-4 text-sm text-gray-500">No upcoming events.</p>
            ) : (
              <ul className="divide-y divide-gray-100">
                {upcomingEvents.map((event) => (
                  <li key={event.id}>
                    <Link to={`/company/events/${event.id}`} className="flex items-center gap-3 px-5 py-3 hover:bg-gray-50/60">
                      <CalendarDays size={16} className="text-gray-400" aria-hidden="true" />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-medium text-gray-900">{event.name}</span>
                        <span className="text-xs text-gray-500">{formatDate(event.event_date)}</span>
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
