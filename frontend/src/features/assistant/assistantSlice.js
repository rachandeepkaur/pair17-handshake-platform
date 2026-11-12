import { createSlice } from '@reduxjs/toolkit'

export const ASSISTANT_STORAGE_KEY = 'assistant-conversation'

function loadConversation() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(ASSISTANT_STORAGE_KEY) || '[]')
    return Array.isArray(saved) ? saved : []
  } catch {
    return []
  }
}

const assistantSlice = createSlice({
  name: 'assistant',
  initialState: { conversation: loadConversation() },
  reducers: {
    conversationCleared(state) {
      state.conversation = []
    },
    conversationSet(state, action) {
      state.conversation = action.payload
    },
  },
})

export const { conversationCleared, conversationSet } = assistantSlice.actions
export const selectConversation = (state) => state.assistant.conversation
export default assistantSlice.reducer
