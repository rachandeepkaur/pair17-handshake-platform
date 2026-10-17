import { Bot } from 'lucide-react'
import { useState } from 'react'
import { errorMessage } from '../../services/api'
import { sendAssistantMessage } from '../../services/assistantService'
import Card, { CardHeader } from '../ui/Card'
import ChatWindow from './ChatWindow'

export default function ChatWidget() {
  const [conversation, setConversation] = useState([])
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [toolCallCount, setToolCallCount] = useState(0)
  const [pendingConfirmation, setPendingConfirmation] = useState(null)

  async function sendMessage() {
    const message = draft.trim()
    if (!message || loading) return

    const priorConversation = conversation
    setConversation([...priorConversation, { role: 'user', content: message }])
    setDraft('')
    setError('')
    setToolCallCount(0)
    setLoading(true)

    try {
      const response = await sendAssistantMessage(message, priorConversation)
      setConversation(response.conversation)
      setToolCallCount(response.tool_call_count)
      setPendingConfirmation(response.pending_confirmation)
    } catch (requestError) {
      setConversation(priorConversation)
      setDraft(message)
      setError(errorMessage(requestError, 'The assistant could not respond. Please try again.'))
    } finally {
      setLoading(false)
    }
  }

  async function respondToConfirmation(approved) {
    if (!pendingConfirmation || loading) return
    setLoading(true)
    setError('')
    try {
      const response = await sendAssistantMessage(approved ? 'Yes, save it.' : 'No, do not save it.', conversation, { ...pendingConfirmation, approved })
      setConversation(response.conversation)
      setToolCallCount(response.tool_call_count)
      setPendingConfirmation(null)
    } catch (requestError) {
      setError(errorMessage(requestError, 'The confirmation could not be processed.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader title="Career assistant" subtitle="Search jobs and upcoming events using your Handshake data." action={<Bot className="text-brand-600" size={22} aria-hidden="true" />} />
      {error && <p className="mx-5 mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      <ChatWindow conversation={conversation} draft={draft} onDraftChange={setDraft} onSubmit={sendMessage} loading={loading} toolCallCount={toolCallCount} pendingConfirmation={pendingConfirmation} onConfirm={respondToConfirmation} />
    </Card>
  )
}
