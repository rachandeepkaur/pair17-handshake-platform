import { useNavigate, useParams } from 'react-router-dom'
import { MessageSquare } from 'lucide-react'
import Button from '../../components/ui/Button'
import { usePermissions } from '../../hooks/usePermissions'
import { useMessageStudent } from '../../hooks/useMessageStudent'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import ErrorMessage from '../../components/common/ErrorMessage'
import StudentProfileView from '../../components/profile/StudentProfileView'
import { useFetch } from '../../hooks/useFetch'
import { getStudent } from '../../services/studentService'

export default function StudentProfile() {
  const { studentId } = useParams()
  const navigate = useNavigate()
  const { data, loading, error } = useFetch(() => getStudent(studentId), [studentId])
  const { can } = usePermissions()
  const { messageStudent, busy, error: messageError } = useMessageStudent()

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div className="flex items-center justify-between gap-3">
        <button
          onClick={() => navigate(-1)}
          className="rounded-md text-sm font-medium text-gray-500 hover:text-gray-700"
        >
          ← Back
        </button>
        {data && can('messages:write') && (
          <Button icon={MessageSquare} onClick={() => messageStudent(data.account_id)} disabled={busy}>
            {busy ? 'Opening…' : 'Message'}
          </Button>
        )}
      </div>
      <ErrorMessage message={messageError} />
      {error ? (
        <>
          <PageHeader title="Student not found" />
          <ErrorMessage message={error} />
        </>
      ) : loading || !data ? (
        <Skeleton className="h-80 rounded-2xl" />
      ) : (
        <StudentProfileView student={data} />
      )}
    </div>
  )
}
