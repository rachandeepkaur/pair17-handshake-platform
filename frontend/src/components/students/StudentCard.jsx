import { Link } from 'react-router-dom'
import Card from '../ui/Card'
import Avatar from '../ui/Avatar'
import SkillTags from '../ui/SkillTags'

export default function StudentCard({ student }) {
  const program = [student.degree, student.major].filter(Boolean).join(' · ')
  return (
    <Link to={`/company/students/${student.account_id}`} className="block rounded-2xl">
      <Card className="h-full p-5 transition-shadow hover:shadow-card-hover">
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
        <div className="mt-3">
          <SkillTags skills={student.skills} max={4} />
        </div>
      </Card>
    </Link>
  )
}
