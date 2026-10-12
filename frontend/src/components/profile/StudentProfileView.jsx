import { GraduationCap, Mail, MapPin, Phone, Calendar, Award } from 'lucide-react'
import Card, { CardHeader } from '../ui/Card'
import Avatar from '../ui/Avatar'
import SkillTags from '../ui/SkillTags'
import { apiUrl } from '../../services/api'
import { formatDate } from '../../utils/format'

function Detail({ icon: Icon, children }) {
  if (!children) return null
  return (
    <p className="flex items-center gap-2 text-sm text-gray-600">
      <Icon size={16} className="shrink-0 text-gray-400" aria-hidden="true" />
      {children}
    </p>
  )
}

function Section({ title, children, empty = 'Not provided' }) {
  return (
    <Card>
      <CardHeader title={title} />
      <div className="whitespace-pre-line px-5 py-4 text-sm text-gray-700">
        {children || <span className="text-gray-400">{empty}</span>}
      </div>
    </Card>
  )
}

export default function StudentProfileView({ student }) {
  const location = [student.city, student.state, student.country].filter(Boolean).join(', ')
  const education = [student.degree, student.major].filter(Boolean).join(' in ')

  return (
    <div className="space-y-5">
      <Card className="p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
          {student.profile_picture_url ? (
            <img
              src={apiUrl(student.profile_picture_url)}
              alt=""
              className="h-16 w-16 rounded-full object-cover"
            />
          ) : (
            <Avatar name={student.name} size="lg" className="!h-16 !w-16 !text-lg" />
          )}
          <div className="min-w-0 flex-1 space-y-1.5">
            <h2 className="text-xl font-semibold text-gray-900">{student.name}</h2>
            <Detail icon={GraduationCap}>
              {student.college_name}
              {education && ` · ${education}`}
              {student.graduation_year && ` · Class of ${student.graduation_year}`}
            </Detail>
            <Detail icon={MapPin}>{location}</Detail>
            <Detail icon={Mail}>
              <a href={`mailto:${student.email}`} className="text-brand-600 hover:underline">
                {student.email}
              </a>
            </Detail>
            <Detail icon={Phone}>{student.phone}</Detail>
            <Detail icon={Calendar}>
              {student.date_of_birth && `Born ${formatDate(student.date_of_birth)}`}
            </Detail>
            <Detail icon={Award}>{student.cgpa != null && `CGPA ${Number(student.cgpa).toFixed(2)}`}</Detail>
          </div>
        </div>
        <div className="mt-4 border-t border-gray-100 pt-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Skills</p>
          <SkillTags skills={student.skills} />
        </div>
      </Card>

      <Section title="Career objective">{student.career_objective}</Section>
      <Section title="Experience">{student.experience}</Section>
    </div>
  )
}
