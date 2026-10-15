import api from './api'

export function applyToJob(jobId, resume) {
  const form = new FormData()
  form.append('resume', resume)
  return api.post(`/student/jobs/${jobId}/apply`, form).then((response) => response.data)
}

export function getMyApplications(status) {
  return api.get('/student/applications', { params: { status: status || undefined } }).then((response) => response.data)
}
