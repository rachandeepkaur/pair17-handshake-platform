import api from './api'

export function sendAssistantMessage(message, conversation, confirmation) {
  return api.post('/assistant/chat', { message, conversation, confirmation }).then((response) => response.data)
}

export function confirmAssistantAction(conversation, approved) {
  return api.post('/assistant/confirm', { conversation, approved }).then((response) => response.data)
}
