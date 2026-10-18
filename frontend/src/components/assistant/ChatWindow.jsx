import { LoaderCircle, Send } from 'lucide-react'
import { useEffect, useRef } from 'react'
import Button from '../ui/Button'
import MessageBubble from './MessageBubble'
import ToolCallIndicator from './ToolCallIndicator'
import ConfirmActionDialog from './ConfirmActionDialog'
import { toTurns } from '../../hooks/useAssistantChat'

export const SUGGESTIONS = [
  'Find an internship in my city.',
  'Find a remote data science internship.',
  'Find an event for computer science students next month.',
  'Show me higher-paying full-time jobs.',
]

export default function ChatWindow({ chat, heightClass = 'h-[28rem]', showSuggestions = true }) {
  const { conversation, draft, setDraft, loading, send, pendingAction, decide } = chat
  const bottomRef = useRef(null)
  const turns = toTurns(conversation)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [conversation.length, loading, pendingAction])

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      send()
    }
  }

  return (
    <div className={`flex min-h-0 flex-col ${heightClass}`}>
      <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4" aria-live="polite">
        {turns.length === 0 && (
          <div className="rounded-xl bg-gray-50 p-4 text-sm text-gray-600">
            <p>Ask about internships, jobs, or upcoming events. Answers come only from Hirely’s listings.</p>
            {showSuggestions && (
              <div className="mt-3 flex flex-wrap gap-2">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => send(suggestion)}
                    disabled={loading}
                    className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:border-brand-300 hover:text-brand-700 disabled:opacity-60"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {turns.map((turn, index) => (
          <div key={index} className="space-y-3">
            <MessageBubble role="user" content={turn.question} />
            {turn.answer && (
              <MessageBubble role="assistant" content={turn.answer}>
                <ToolCallIndicator calls={turn.toolCalls} />
              </MessageBubble>
            )}
          </div>
        ))}

        {pendingAction && !loading && <ConfirmActionDialog action={pendingAction} onDecide={decide} busy={loading} />}

        {loading && (
          <div className="flex items-center gap-2 text-sm text-gray-500" role="status">
            <LoaderCircle className="animate-spin" size={16} aria-hidden="true" />
            Searching Hirely… the local model can take a minute or more.
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        className="flex gap-2 border-t border-gray-100 p-4"
        onSubmit={(event) => {
          event.preventDefault()
          send()
        }}
      >
        <label className="sr-only" htmlFor="assistant-message">
          Message the assistant
        </label>
        <textarea
          id="assistant-message"
          rows="2"
          value={draft}
          maxLength={2000}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading || Boolean(pendingAction)}
          placeholder={pendingAction ? 'Approve or decline the change above first.' : 'Ask about jobs or events…'}
          className="min-h-10 flex-1 resize-none rounded-xl border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 disabled:bg-gray-50"
        />
        <Button type="submit" icon={Send} aria-label="Send message" disabled={loading || Boolean(pendingAction) || !draft.trim()} className="self-end">
          Send
        </Button>
      </form>
    </div>
  )
}
