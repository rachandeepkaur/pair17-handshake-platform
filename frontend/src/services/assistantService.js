import api from './api'

export function sendAssistantMessage(message, conversation, confirmation) {
  return api.post('/assistant/chat', { message, conversation, confirmation }).then((response) => response.data)
}
