import api from './api'

export function getStudentJobs({ q, category, city, limit = 20, offset = 0 } = {}) {
  return api.get('/student/jobs', {
    params: {
      q: q || undefined,
      category: category || undefined,
      city: city || undefined,
      limit,
      offset,
    },
  }).then((response) => response.data)
}

export function getStudentJob(jobId) {
  return api.get(`/student/jobs/${jobId}`).then((response) => response.data)
}
