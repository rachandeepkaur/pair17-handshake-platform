import api from './api'

export function getPreferences() {
  return api.get('/student/preferences').then((response) => response.data)
}

export function updatePreferences(data) {
  return api.put('/student/preferences', data).then((response) => response.data)
}
