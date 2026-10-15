import { useRef, useState } from 'react'
import Button from '../ui/Button'
import Modal from '../common/Modal'
import { errorMessage } from '../../services/api'

export default function StudentApplyModal({ job, onApply, onClose }) {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const selectFile = (event) => {
    const next = event.target.files?.[0]
    setError('')
    if (next && (next.type !== 'application/pdf' || next.size > 5 * 1024 * 1024)) {
      setFile(null)
      setError('Choose a PDF resume that is 5 MB or smaller.')
      return
    }
    setFile(next || null)
  }
  const submit = async () => {
    if (!file) return setError('Choose your PDF resume first.')
    setSubmitting(true)
    setError('')
    try { await onApply(file) } catch (err) { setError(errorMessage(err, 'Could not submit application.')) } finally { setSubmitting(false) }
  }
  return <Modal title={`Apply to ${job.title}`} onClose={onClose}>
    <p className="text-sm text-gray-600">Upload the PDF resume you want to send to {job.company_name}.</p>
    <input ref={inputRef} type="file" accept="application/pdf,.pdf" className="sr-only" onChange={selectFile} />
    <button type="button" onClick={() => inputRef.current?.click()} className="mt-5 w-full rounded-xl border border-dashed border-gray-300 px-4 py-5 text-sm font-medium text-gray-700 hover:bg-gray-50">{file ? file.name : 'Choose PDF resume'}</button>
    {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    <div className="mt-5 flex justify-end gap-2"><Button variant="outline" onClick={onClose} disabled={submitting}>Cancel</Button><Button onClick={submit} disabled={submitting}>{submitting ? 'Submitting…' : 'Submit application'}</Button></div>
  </Modal>
}
