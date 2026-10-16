import api from './api'

export function getStudentEvents({ q } = {}) {
  return api.get('/student/events', {
    params: { q: q || undefined },
  }).then((response) => response.data)
}

export function getStudentEvent(eventId) {
  return api.get(`/student/events/${eventId}`).then((response) => response.data)
}

export function registerForEvent(eventId) {
  return api.post(`/student/events/${eventId}/register`).then((response) => response.data)
}

export function getMyRegistrations() {
  return api.get('/student/events/registrations').then((response) => response.data)
}
