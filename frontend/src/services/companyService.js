import api from './api'

export function getDashboard() {
  return api.get('/dashboards/company').then((res) => res.data)
}

export function getProfile() {
  return api.get('/companies/me').then((res) => res.data)
}

export function updateProfile(data) {
  return api.put('/companies/me', data).then((res) => res.data)
}

export function uploadPicture(file) {
  const form = new FormData()
  form.append('file', file)
  return api.post('/companies/me/picture', form).then((res) => res.data)
}
