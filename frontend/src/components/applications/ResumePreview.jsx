import { useEffect, useState } from 'react'
import { Download, ExternalLink, FileText } from 'lucide-react'
import Card, { CardHeader } from '../ui/Card'
import Skeleton from '../ui/Skeleton'
import EmptyState from '../ui/EmptyState'
import { getResumeBlob } from '../../services/applicationService'

export default function ResumePreview({ applicationId, studentName }) {
  const [url, setUrl] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let objectUrl
    let cancelled = false
    setUrl(null)
    setError('')

    getResumeBlob(applicationId)
      .then((blob) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }))
        setUrl(objectUrl)
      })
      .catch(() => !cancelled && setError('This applicant’s resume could not be loaded.'))

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [applicationId])

  const filename = `${(studentName || 'applicant').replace(/\s+/g, '_')}_resume.pdf`

  return (
    <Card className="overflow-hidden">
      <CardHeader
        title="Resume"
        action={
          url && (
            <div className="flex gap-1">
              <a
                href={url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-sm font-medium text-brand-600 hover:bg-brand-50"
              >
                <ExternalLink size={15} /> Open
              </a>
              <a
                href={url}
                download={filename}
                className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-sm font-medium text-brand-600 hover:bg-brand-50"
              >
                <Download size={15} /> Download
              </a>
            </div>
          )
        }
      />
      {error ? (
        <div className="p-5">
          <EmptyState icon={FileText} title="Resume unavailable" description={error} />
        </div>
      ) : url ? (
        <iframe src={url} title={`${studentName}'s resume`} className="h-[640px] w-full bg-gray-100" />
      ) : (
        <Skeleton className="h-[640px] w-full rounded-none" />
      )}
    </Card>
  )
}
