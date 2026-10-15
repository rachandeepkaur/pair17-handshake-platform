import api from './api'

export function signupStudent(data) {
  return api.post('/auth/signup/student', data).then((response) => response.data)
}
