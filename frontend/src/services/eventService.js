import api from './api'

export function createEvent(data) {
  return api.post('/events', data).then((res) => res.data)
}

export function getMyEvents() {
  return api.get('/events/mine').then((res) => res.data)
}

export function getEvent(eventId) {
  return api.get(`/events/${eventId}`).then((res) => res.data)
}

export function getEventRegistrations(eventId) {
  return api.get(`/events/${eventId}/registrations`).then((res) => res.data)
}
