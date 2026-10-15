import api from './api'

export function getMyProfile() {
  return api.get('/students/me').then((response) => response.data)
}

export function updateMyProfile(data) {
  return api.put('/students/me', data).then((response) => response.data)
}

export function uploadMyPicture(file) {
  const form = new FormData()
  form.append('file', file)
  return api.post('/students/me/picture', form).then((response) => response.data)
}
