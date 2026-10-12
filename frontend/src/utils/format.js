// Date-only strings ("2026-11-04") are parsed as UTC by `new Date()`, which
// shifts them a day back in US time zones; parse them as local dates instead.
function toDate(value) {
  if (!value) return null
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [year, month, day] = value.split('-').map(Number)
    return new Date(year, month - 1, day)
  }
  return new Date(value)
}

export function formatDate(value) {
  const date = toDate(value)
  return date
    ? date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : '—'
}

export function formatTime(value) {
  if (!value) return null
  const [hours, minutes] = value.split(':').map(Number)
  return new Date(2000, 0, 1, hours, minutes).toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function isOnOrAfterToday(value) {
  const date = toDate(value)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date >= today
}

export function daysFromToday(value) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return Math.round((toDate(value) - today) / 86_400_000)
}

export function formatSalary(value) {
  if (value == null || value === '') return null
  return Number(value).toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

export function splitSkills(value) {
  return (value || '')
    .split(',')
    .map((skill) => skill.trim())
    .filter(Boolean)
}

export function todayISO() {
  const today = new Date()
  const offset = today.getTimezoneOffset() * 60_000
  return new Date(today - offset).toISOString().slice(0, 10)
}
