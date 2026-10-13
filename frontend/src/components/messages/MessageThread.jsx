import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Briefcase, CalendarDays } from 'lucide-react'
import { formatDate, formatDateTime } from '../../utils/format'

function Attachment({ to, icon: Icon, label, title, mine }) {
  return (
    <Link
      to={to}
      className={`mt-2 flex items-center gap-2 rounded-xl border px-3 py-2 text-left text-sm ${
        mine ? 'border-white/25 bg-white/10 hover:bg-white/20' : 'border-gray-200 bg-gray-50 hover:bg-gray-100'
      }`}
    >
      <Icon size={16} aria-hidden="true" className="shrink-0" />
      <span className="min-w-0">
        <span className={`block text-xs ${mine ? 'text-brand-100' : 'text-gray-500'}`}>{label}</span>
        <span className="block truncate font-medium">{title}</span>
      </span>
    </Link>
  )
}

export default function MessageThread({ messages }) {
  const endRef = useRef(null)
  const lastId = messages.at(-1)?.id

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end' })
  }, [lastId])

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center p-6 text-center text-sm text-gray-500">
        No messages yet. Say hello, or use a template below.
      </div>
    )
  }

  return (
    <ol className="flex-1 space-y-3 overflow-y-auto p-4" aria-label="Messages">
      {messages.map((message, index) => {
        const mine = message.sender_side === 'company'
        const previous = messages[index - 1]
        const showSender = !previous || previous.sender_name !== message.sender_name
        return (
          <li key={message.id} className={`flex flex-col ${mine ? 'items-end' : 'items-start'}`}>
            {showSender && <span className="mb-1 px-1 text-xs text-gray-500">{message.sender_name}</span>}
            <div
              className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm sm:max-w-[70%] ${
                mine ? 'rounded-br-md bg-brand-600 text-white' : 'rounded-bl-md border border-gray-200 bg-white text-gray-800'
              }`}
            >
              <p className="whitespace-pre-line break-words">{message.body}</p>
              {message.job && (
                <Attachment
                  to={`/company/jobs/${message.job.id}`}
                  icon={Briefcase}
                  label="Invitation to apply"
                  title={message.job.title}
                  mine={mine}
                />
              )}
              {message.event && (
                <Attachment
                  to={`/company/events/${message.event.id}`}
                  icon={CalendarDays}
                  label={`Event · ${formatDate(message.event.event_date)}`}
                  title={message.event.name}
                  mine={mine}
                />
              )}
            </div>
            <span className="mt-1 px-1 text-[11px] text-gray-400">
              {formatDateTime(message.created_at)}
              {mine && message.read_at && ' · Read'}
            </span>
          </li>
        )
      })}
      <li ref={endRef} aria-hidden="true" />
    </ol>
  )
}
