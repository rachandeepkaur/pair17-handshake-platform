import { useState } from 'react'
import { Mail, MapPin, Pencil, School } from 'lucide-react'
import ErrorMessage from '../../components/common/ErrorMessage'
import ProfilePicture from '../../components/profile/ProfilePicture'
import StudentProfileForm from '../../components/profile/StudentProfileForm'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { useFetch } from '../../hooks/useFetch'
import { getMyProfile, updateMyProfile, uploadMyPicture } from '../../services/studentProfileService'

const detail = (label, value) => (
  <div>
    <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</dt>
    <dd className="mt-1 whitespace-pre-line text-sm text-gray-800">{value || <span className="text-gray-400">Not added yet</span>}</dd>
  </div>
)

export default function StudentProfile() {
  const { data: profile, loading, error, setData } = useFetch(getMyProfile, [])
  const [editing, setEditing] = useState(false)
  const [saved, setSaved] = useState(false)

  const applyUpdate = (updated) => setData(updated)
  const handleSave = async (values) => {
    applyUpdate(await updateMyProfile(values))
    setEditing(false)
    setSaved(true)
  }
  const handleUpload = async (file) => applyUpdate(await uploadMyPicture(file))

  if (error) return <ErrorMessage message={error} />
  if (loading || !profile) return <Skeleton className="h-96 rounded-2xl" />

  const location = [profile.city, profile.state, profile.country].filter(Boolean).join(', ')

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        title="My Profile"
        description="Keep your academic and career information current for employers."
        actions={!editing && <Button variant="outline" icon={Pencil} onClick={() => { setEditing(true); setSaved(false) }}>Edit profile</Button>}
      />
      {saved && <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm text-emerald-800">Profile saved.</p>}

      <Card className="overflow-hidden">
        <div className="h-28 bg-gradient-to-r from-brand-600 via-brand-500 to-accent-500" aria-hidden="true" />
        <div className="px-6 pb-6">
          <div className="-mt-10 mb-4 rounded-2xl bg-white p-1 shadow-card sm:inline-block">
            <ProfilePicture name={profile.name} pictureUrl={profile.profile_picture_url} onUpload={handleUpload} />
          </div>
          {editing ? (
            <StudentProfileForm profile={profile} onSave={handleSave} onCancel={() => setEditing(false)} />
          ) : (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{profile.name}</h2>
                <p className="mt-1 flex items-center gap-1.5 text-sm text-gray-600"><School size={16} className="text-gray-400" /> {profile.college_name}</p>
                {location && <p className="mt-1 flex items-center gap-1.5 text-sm text-gray-600"><MapPin size={16} className="text-gray-400" /> {location}</p>}
                <p className="mt-1 flex items-center gap-1.5 text-sm text-gray-600"><Mail size={16} className="text-gray-400" /> {profile.email}</p>
              </div>
              <dl className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {detail('Career objective', profile.career_objective)}
                {detail('Degree', profile.degree)}
                {detail('Major', profile.major)}
                {detail('Graduation year', profile.graduation_year)}
                {detail('CGPA', profile.cgpa)}
                {detail('Date of birth', profile.date_of_birth)}
                {detail('Phone', profile.phone)}
                {detail('Skills', profile.skills)}
                {detail('Experience', profile.experience)}
              </dl>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}
