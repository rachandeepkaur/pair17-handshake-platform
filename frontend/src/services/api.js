import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL

const api = axios.create({ baseURL: API_URL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// An expired or revoked token makes every protected call fail with 401;
// send the user back to sign in instead of leaving broken pages.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthCall = error.config?.url?.startsWith('/auth/')
    if (error.response?.status === 401 && !isAuthCall && localStorage.getItem('token')) {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      window.location.assign('/login')
    }
    return Promise.reject(error)
  },
)

export function apiUrl(path) {
  return path ? `${API_URL}${path}` : null
}

export function errorMessage(error, fallback = 'Something went wrong. Please try again.') {
  return error?.response?.data?.detail || fallback
}

export default api
