import api from './api'

export function sendAssistantMessage(message, conversation) {
  return api.post('/assistant/chat', { message, conversation }).then((response) => response.data)
}

export function confirmAssistantAction(conversation, approved) {
  return api.post('/assistant/confirm', { conversation, approved }).then((response) => response.data)
}
