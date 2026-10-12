import api from './api'

export function getDashboard() {
  return api.get('/dashboards/company').then((res) => res.data)
}
