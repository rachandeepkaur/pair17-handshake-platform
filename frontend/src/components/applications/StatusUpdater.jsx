import { useState } from 'react'
import { ConfirmDialog } from '../common/Modal'
import StatusBadge from '../ui/StatusBadge'
import { usePermissions } from '../../hooks/usePermissions'
import { updateApplicationStatus } from '../../services/applicationService'
import { errorMessage } from '../../services/api'
import { APPLICATION_STATUSES } from '../../utils/constants'
import Select from '../ui/Select'

export default function StatusUpdater({ application, onUpdated, compact = false }) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [pendingDecline, setPendingDecline] = useState(false)
  const { can, loaded } = usePermissions()

  const save = async (status) => {
    setSaving(true)
    setError('')
    try {
      const updated = await updateApplicationStatus(application.id, status)
      onUpdated?.(updated)
    } catch (err) {
      setError(errorMessage(err, 'Could not update status'))
    } finally {
      setSaving(false)
      setPendingDecline(false)
    }
  }

  const handleChange = (event) => {
    const status = event.target.value
    if (status === application.status) return
    if (status === 'Declined') setPendingDecline(true)
    else save(status)
  }

  // Read-only roles see the status but can't change it.
  if (!loaded || !can('applicants:write')) return <StatusBadge status={application.status} />

  const id = `status-${application.id}`
  return (
    <div>
      {!compact && (
        <label htmlFor={id} className="mb-1 block text-sm font-medium text-gray-700">
          Application status
        </label>
      )}
      <Select
        id={id}
        size="sm"
        value={application.status}
        onChange={handleChange}
        disabled={saving}
        options={APPLICATION_STATUSES.map((status) => ({ value: status, label: status }))}
        aria-label={compact ? `Status for ${application.student.name}` : undefined}
        className="w-36"
      />
      {saving && <span className="ml-2 text-xs text-gray-500">Saving…</span>}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}

      <ConfirmDialog
        open={pendingDecline}
        title="Decline this applicant?"
        message={`${application.student.name} will be marked as Declined for ${application.job_title}. You can change this later.`}
        confirmLabel="Decline"
        busy={saving}
        onConfirm={() => save('Declined')}
        onCancel={() => setPendingDecline(false)}
      />
    </div>
  )
}
