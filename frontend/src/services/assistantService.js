import api from './api'

export function sendAssistantMessage(message, conversation) {
  return api.post('/assistant/chat', { message, conversation }).then((response) => response.data)
}
