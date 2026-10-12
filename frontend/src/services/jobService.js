import api from './api'

export function createJob(data) {
  return api.post('/jobs', data).then((res) => res.data)
}

export function getMyJobs() {
  return api.get('/jobs/mine').then((res) => res.data)
}

export function getJob(jobId) {
  return api.get(`/jobs/${jobId}`).then((res) => res.data)
}

export function getJobApplications(jobId, status) {
  return api
    .get(`/jobs/${jobId}/applications`, { params: { status: status || undefined } })
    .then((res) => res.data)
}
