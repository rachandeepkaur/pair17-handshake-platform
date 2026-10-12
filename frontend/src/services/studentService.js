import api from './api'

export function searchStudents({ q, college, skills, major, limit = 12, offset = 0 } = {}) {
  return api
    .get('/students', {
      params: {
        q: q || undefined,
        college: college || undefined,
        skills: skills || undefined,
        major: major || undefined,
        limit,
        offset,
      },
    })
    .then((res) => res.data)
}

export function getStudent(studentId) {
  return api.get(`/students/${studentId}`).then((res) => res.data)
}
