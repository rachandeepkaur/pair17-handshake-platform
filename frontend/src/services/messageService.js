import api from './api'

export function getConversations({ q, unreadOnly } = {}) {
  return api
    .get('/messages/conversations', { params: { q: q || undefined, unread_only: unreadOnly || undefined } })
    .then((res) => res.data)
}

export function startConversation(studentId) {
  return api.post('/messages/conversations', { student_id: studentId }).then((res) => res.data)
}

export function getConversation(conversationId) {
  return api.get(`/messages/conversations/${conversationId}`).then((res) => res.data)
}

export function sendMessage(conversationId, { body, jobId, eventId }) {
  return api
    .post(`/messages/conversations/${conversationId}/messages`, {
      body,
      job_id: jobId || null,
      event_id: eventId || null,
    })
    .then((res) => res.data)
}

export function markConversationRead(conversationId) {
  return api.post(`/messages/conversations/${conversationId}/read`)
}
