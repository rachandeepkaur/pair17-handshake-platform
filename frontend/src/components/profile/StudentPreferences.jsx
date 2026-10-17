import { useState } from 'react'
import Button from '../ui/Button'
import Card, { CardHeader } from '../ui/Card'
import { errorMessage } from '../../services/api'
import { updatePreferences } from '../../services/preferenceService'

export default function StudentPreferences({ preferences, onSaved }) {
  const [values, setValues] = useState(preferences)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const change = (event) => setValues((current) => ({ ...current, [event.target.name]: event.target.type === 'checkbox' ? event.target.checked : event.target.value }))
  const save = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const saved = await updatePreferences({ ...values, min_salary: values.min_salary === '' ? null : Number(values.min_salary) })
      setValues(saved)
      onSaved(saved)
    } catch (requestError) {
      setError(errorMessage(requestError, 'Preferences could not be saved.'))
    } finally {
      setSaving(false)
    }
  }

  return <Card className="p-5"><CardHeader title="Career preferences" subtitle="Used by the career assistant to personalize recommendations." />
    <form onSubmit={save} className="mt-4 space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <label className="text-sm font-medium text-gray-700">Preferred categories<input name="preferred_categories" value={values.preferred_categories || ''} onChange={change} placeholder="Internship, full time" className="mt-1 block h-10 w-full rounded-xl border border-gray-300 px-3 text-sm" /></label>
        <label className="text-sm font-medium text-gray-700">Preferred cities<input name="preferred_cities" value={values.preferred_cities || ''} onChange={change} placeholder="Palo Alto, Menlo Park" className="mt-1 block h-10 w-full rounded-xl border border-gray-300 px-3 text-sm" /></label>
        <label className="text-sm font-medium text-gray-700">Minimum salary<input name="min_salary" type="number" min="0" value={values.min_salary ?? ''} onChange={change} placeholder="e.g. 60000" className="mt-1 block h-10 w-full rounded-xl border border-gray-300 px-3 text-sm" /></label>
        <label className="flex items-center gap-2 self-end pb-2 text-sm font-medium text-gray-700"><input name="remote_ok" type="checkbox" checked={values.remote_ok || false} onChange={change} /> Open to remote work</label>
      </div>
      <label className="block text-sm font-medium text-gray-700">Preferred skills<textarea name="preferred_skills" value={values.preferred_skills || ''} onChange={change} rows="2" placeholder="Python, SQL, React" className="mt-1 block w-full rounded-xl border border-gray-300 px-3 py-2 text-sm" /></label>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <Button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save preferences'}</Button>
    </form>
  </Card>
}
