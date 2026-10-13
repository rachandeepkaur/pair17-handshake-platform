import api from './api'

export function getCompanyApplications({ jobId, studentId, status } = {}) {
  return api
    .get('/applications/company', {
      params: { job_id: jobId || undefined, student_id: studentId || undefined, status: status || undefined },
    })
    .then((res) => res.data)
}

export function getApplication(applicationId) {
  return api.get(`/applications/${applicationId}`).then((res) => res.data)
}

export function updateApplicationStatus(applicationId, status) {
  return api.patch(`/applications/${applicationId}/status`, { status }).then((res) => res.data)
}

// The resume endpoint needs the auth header, so it can't be used as a plain
// <iframe src>; fetch it as a blob and let the caller build an object URL.
export function getResumeBlob(applicationId) {
  return api
    .get(`/applications/${applicationId}/resume`, { responseType: 'blob' })
    .then((res) => res.data)
}
