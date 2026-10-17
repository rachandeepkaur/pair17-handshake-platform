import { Search } from 'lucide-react'
import Avatar from '../ui/Avatar'
import Skeleton from '../ui/Skeleton'
import { formatMessageTime } from '../../utils/format'

export default function ConversationList({
  conversations,
  loading,
  activeId,
  onSelect,
  query,
  onQueryChange,
  unreadOnly,
  onUnreadOnlyChange,
  participantSide = 'company',
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="space-y-2 border-b border-gray-100 p-3">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder={`Search by ${participantSide === 'company' ? 'student' : 'company'} name`}
            aria-label={`Search conversations by ${participantSide === 'company' ? 'student' : 'company'} name`}
            className="h-9 w-full rounded-xl border border-gray-200 bg-gray-50 pl-9 pr-3 text-sm focus:border-brand-400 focus:bg-white"
          />
        </div>
        <div className="flex gap-1" role="group" aria-label="Filter conversations">
          {[
            [false, 'All'],
            [true, 'Unread'],
          ].map(([value, label]) => (
            <button
              key={label}
              onClick={() => onUnreadOnlyChange(value)}
              aria-pressed={unreadOnly === value}
              className={`rounded-lg px-2.5 py-1 text-xs font-medium ${
                unreadOnly === value ? 'bg-brand-50 text-brand-700' : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading && !conversations ? (
          <div className="space-y-3 p-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-14 rounded-xl" />
            ))}
          </div>
        ) : conversations?.length === 0 ? (
          <p className="px-4 py-8 text-center text-sm text-gray-500">
            {unreadOnly ? 'No unread conversations.' : query ? 'No conversations match.' : 'No conversations yet.'}
          </p>
        ) : (
          <ul>
            {conversations.map((conversation) => {
              const active = conversation.id === activeId
              const unread = conversation.unread_count > 0
              const other = participantSide === 'company'
                ? conversation.student
                : { name: conversation.company.company_name }
              const lastWasMine = conversation.last_message?.sender_side === participantSide
              return (
                <li key={conversation.id}>
                  <button
                    onClick={() => onSelect(conversation.id)}
                    aria-current={active ? 'true' : undefined}
                    className={`flex w-full items-start gap-3 border-l-2 px-3 py-3 text-left transition-colors ${
                      active ? 'border-brand-600 bg-brand-50/60' : 'border-transparent hover:bg-gray-50'
                    }`}
                  >
                    <Avatar name={other.name} size="sm" />
                    <span className="min-w-0 flex-1">
                      <span className="flex items-baseline justify-between gap-2">
                        <span className={`truncate text-sm ${unread ? 'font-semibold text-gray-900' : 'font-medium text-gray-800'}`}>
                          {other.name}
                        </span>
                        {conversation.last_message && (
                          <span className="shrink-0 text-xs text-gray-400">
                            {formatMessageTime(conversation.last_message.created_at)}
                          </span>
                        )}
                      </span>
                      <span className="flex items-center justify-between gap-2">
                        <span className={`truncate text-xs ${unread ? 'text-gray-800' : 'text-gray-500'}`}>
                          {conversation.last_message
                            ? `${lastWasMine ? 'You: ' : ''}${conversation.last_message.body}`
                            : 'No messages yet'}
                        </span>
                        {unread && (
                          <span className="inline-flex h-5 min-w-5 shrink-0 items-center justify-center rounded-full bg-brand-600 px-1.5 text-xs font-semibold text-white">
                            {conversation.unread_count}
                            <span className="sr-only"> unread</span>
                          </span>
                        )}
                      </span>
                    </span>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
