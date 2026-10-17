import { LoaderCircle, Send } from 'lucide-react'
import { useEffect, useRef } from 'react'
import Button from '../ui/Button'
import MessageBubble from './MessageBubble'
import ToolCallIndicator from './ToolCallIndicator'

export default function ChatWindow({ conversation, draft, onDraftChange, onSubmit, loading, toolCallCount, pendingConfirmation, onConfirm }) {
  const bottomRef = useRef(null)
  const visibleMessages = conversation.filter((message) => message.role === 'user' || message.role === 'assistant')

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversation, loading])

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      onSubmit()
    }
  }

  return (
    <div className="flex h-[28rem] flex-col">
      <div className="flex-1 space-y-3 overflow-y-auto px-5 py-4" aria-live="polite">
        {visibleMessages.length ? visibleMessages.map((message, index) => {
          const isLatestAssistant = message.role === 'assistant' && index === visibleMessages.length - 1
          return <MessageBubble key={`${message.role}-${index}-${message.content}`} role={message.role} content={message.content}><ToolCallIndicator count={isLatestAssistant ? toolCallCount : 0} /></MessageBubble>
        }) : <p className="rounded-xl bg-gray-50 p-4 text-sm text-gray-600">Ask about internships, jobs, or upcoming events. For example: “Find a remote data science internship.”</p>}
        {loading && <div className="flex items-center gap-2 text-sm text-gray-500"><LoaderCircle className="animate-spin" size={16} aria-hidden="true" /> Searching the platform…</div>}
        {pendingConfirmation && <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900"><p>{pendingConfirmation.prompt}</p><div className="mt-2 flex gap-2"><Button size="sm" onClick={() => onConfirm(true)} disabled={loading}>Save item</Button><Button size="sm" variant="outline" onClick={() => onConfirm(false)} disabled={loading}>Cancel</Button></div></div>}
        <div ref={bottomRef} />
      </div>
      <form className="flex gap-2 border-t border-gray-100 p-4" onSubmit={(event) => { event.preventDefault(); onSubmit() }}>
        <label className="sr-only" htmlFor="assistant-message">Message the assistant</label>
        <textarea id="assistant-message" rows="2" value={draft} onChange={(event) => onDraftChange(event.target.value)} onKeyDown={handleKeyDown} disabled={loading} placeholder="Ask about jobs or events…" className="min-h-10 flex-1 resize-none rounded-xl border border-gray-300 px-3 py-2 text-sm text-gray-900 outline-none placeholder:text-gray-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 disabled:bg-gray-50" />
        <Button type="submit" icon={Send} aria-label="Send message" disabled={loading || !draft.trim()} className="self-end">Send</Button>
      </form>
    </div>
  )
}
