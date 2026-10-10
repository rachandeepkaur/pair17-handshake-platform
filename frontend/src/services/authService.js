import api from './api'

export function signupCompany(data) {
  return api.post('/auth/signup/company', data).then((res) => res.data)
}

export function login(credentials) {
  return api.post('/auth/login', credentials).then((res) => res.data)
}
