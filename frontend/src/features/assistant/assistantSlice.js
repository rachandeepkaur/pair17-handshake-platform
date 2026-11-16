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
  initialState: {
    conversation: loadConversation(),
    tokenUsage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0, context_percentage: 0, inference_calls: 0, context_is_estimate: false, compacted: false, before_compaction_tokens: 0, after_compaction_estimate: 0 },
  },
  reducers: {
    conversationCleared(state) {
      state.conversation = []
      state.tokenUsage = { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0, context_percentage: 0, inference_calls: 0, context_is_estimate: false, compacted: false, before_compaction_tokens: 0, after_compaction_estimate: 0 }
    },
    conversationSet(state, action) {
      state.conversation = action.payload
    },
    tokenUsageSet(state, action) {
      state.tokenUsage = action.payload
    },
  },
})

export const { conversationCleared, conversationSet, tokenUsageSet } = assistantSlice.actions
export const selectConversation = (state) => state.assistant.conversation
export const selectTokenUsage = (state) => state.assistant.tokenUsage
export default assistantSlice.reducer
