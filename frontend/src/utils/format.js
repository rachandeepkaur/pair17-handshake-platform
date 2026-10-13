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

const MINUTE = 60_000
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

// "just now", "5m ago", "3h ago", "2d ago", then a date.
export function formatRelative(value) {
  if (!value) return 'Never'
  const elapsed = Date.now() - new Date(value).getTime()
  if (elapsed < MINUTE) return 'Just now'
  if (elapsed < HOUR) return `${Math.floor(elapsed / MINUTE)}m ago`
  if (elapsed < DAY) return `${Math.floor(elapsed / HOUR)}h ago`
  if (elapsed < 7 * DAY) return `${Math.floor(elapsed / DAY)}d ago`
  return formatDate(value)
}

// Message timestamps: time today, weekday this week, otherwise a date.
export function formatMessageTime(value) {
  const date = new Date(value)
  const now = new Date()
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
  }
  if (now - date < 6 * DAY) return date.toLocaleDateString('en-US', { weekday: 'short' })
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function formatDateTime(value) {
  return new Date(value).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}
