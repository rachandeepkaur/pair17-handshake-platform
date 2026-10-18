import { useCallback, useEffect, useMemo, useState } from 'react'
import { errorMessage } from '../services/api'
import { confirmAssistantAction, sendAssistantMessage } from '../services/assistantService'

// Shared by the dashboard widget and the full assistant page, so a chat
// started in one continues in the other. Cleared on sign-out (AuthContext).
export const ASSISTANT_STORAGE_KEY = 'assistant-conversation'

function loadConversation() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(ASSISTANT_STORAGE_KEY) || '[]')
    return Array.isArray(saved) ? saved : []
  } catch {
    return []
  }
}

// Tools that change data; the backend pauses before running them.
const GATED_TOOLS = new Set(['save_job_or_event'])

function describeAction(name, args) {
  if (name === 'save_job_or_event') return `Save ${args.item_type} ${args.item_id} to your saved ${args.item_type}s`
  return `Run ${name}`
}

// A gated call in the last assistant message that has no tool result yet.
export function pendingActionFrom(conversation) {
  const index = conversation.findLastIndex((message) => message.role !== 'tool')
  const message = conversation[index]
  if (!message || message.role !== 'assistant' || !message.tool_calls?.length) return null
  const answered = conversation.length - index - 1
  const call = message.tool_calls[answered]
  const fn = call?.function || call
  if (!fn || !GATED_TOOLS.has(fn.name)) return null
  const args = fn.arguments || {}
  return { tool_name: fn.name, arguments: args, summary: describeAction(fn.name, args) }
}

export function useAssistantChat() {
  const [conversation, setConversation] = useState(loadConversation)
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    try {
      sessionStorage.setItem(ASSISTANT_STORAGE_KEY, JSON.stringify(conversation))
    } catch {
      // Storage full or blocked: the chat still works for this page view.
    }
  }, [conversation])

  const send = useCallback(
    async (text) => {
      const message = (text ?? draft).trim()
      if (!message || loading) return

      const prior = conversation
      setConversation([...prior, { role: 'user', content: message }])
      setDraft('')
      setError('')
      setLoading(true)
      try {
        const response = await sendAssistantMessage(message, prior)
        setConversation(response.conversation)
      } catch (requestError) {
        setConversation(prior)
        setDraft(message)
        setError(errorMessage(requestError, 'The assistant could not respond. Please try again.'))
      } finally {
        setLoading(false)
      }
    },
    [conversation, draft, loading],
  )

  const pendingAction = useMemo(() => pendingActionFrom(conversation), [conversation])

  const decide = useCallback(
    async (approved) => {
      if (!pendingAction || loading) return
      setError('')
      setLoading(true)
      try {
        const response = await confirmAssistantAction(conversation, approved)
        setConversation(response.conversation)
      } catch (requestError) {
        setError(errorMessage(requestError, 'The assistant could not continue. Please try again.'))
      } finally {
        setLoading(false)
      }
    },
    [conversation, loading, pendingAction],
  )

  const reset = useCallback(() => {
    setConversation([])
    setDraft('')
    setError('')
  }, [])

  return { conversation, draft, setDraft, loading, error, send, reset, pendingAction, decide }
}

function resultStatus(content) {
  if (content.startsWith('CANCELLED:')) return 'cancelled'
  if (content.startsWith('TOOL CALL ERROR:') || content.startsWith('Not run:') || content.startsWith('Unknown tool:')) {
    return 'rejected'
  }
  return 'done'
}

// Groups the raw history into turns: each user message plus the tool calls
// the assistant made (with what happened to each) and the final answer.
export function toTurns(conversation) {
  const turns = []
  for (const message of conversation) {
    const turn = turns[turns.length - 1]
    if (message.role === 'user') {
      turns.push({ question: message.content, toolCalls: [], answer: null })
    } else if (message.role === 'assistant' && turn) {
      for (const call of message.tool_calls || []) {
        const fn = call.function || call
        turn.toolCalls.push({ name: fn.name, arguments: fn.arguments || {}, status: 'pending' })
      }
      if (message.content) turn.answer = message.content
    } else if (message.role === 'tool' && turn) {
      const call = turn.toolCalls.find((item) => item.status === 'pending')
      if (call) call.status = resultStatus(message.content || '')
    }
  }
  return turns
}
