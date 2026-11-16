import api from './api'

export function signupCompany(data) {
  return api.post('/auth/signup/company', data).then((res) => res.data)
}

export function login(credentials) {
  return api.post('/auth/login', credentials).then((res) => res.data)
}

export function changePassword(currentPassword, newPassword) {
  return api.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}

// Ends the server-side session; the token is rejected from then on. The token
// is read up front because the caller clears storage right after calling this.
export async function logout() {
  const token = localStorage.getItem('token')
  if (!token) return
  await api.post('/auth/logout', null, { headers: { Authorization: `Bearer ${token}` } })
}
