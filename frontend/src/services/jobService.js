import api from './api'

export function createJob(data) {
  return api.post('/jobs', data).then((res) => res.data)
}

export function getMyJobs() {
  return api.get('/jobs/mine').then((res) => res.data)
}
