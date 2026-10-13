import { useState } from 'react'
import { Briefcase, CalendarDays, FileText, Lock, Send, X } from 'lucide-react'
import Button from '../ui/Button'
import Popover, { PopoverItem } from '../common/Popover'
import { errorMessage } from '../../services/api'
import { formatDate } from '../../utils/format'
import { MESSAGE_TEMPLATES, inviteToApplyText, inviteToEventText } from '../../utils/messageTemplates'

export default function MessageComposer({ conversation, companyName, jobs, events, canWrite, onSend }) {
  const [body, setBody] = useState('')
  const [attachment, setAttachment] = useState(null)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')

  if (!canWrite) {
    return (
      <div className="flex items-center gap-2 border-t border-gray-100 bg-gray-50 px-4 py-3 text-sm text-gray-500">
        <Lock size={16} aria-hidden="true" /> Your role can read messages but not send them.
      </div>
    )
  }

  const student = conversation.student
  const fill = (text) => setBody((current) => (current.trim() ? `${current}\n\n${text}` : text))

  const submit = async () => {
    const text = body.trim()
    if (!text || sending) return
    setSending(true)
    setError('')
    try {
      await onSend({
        body: text,
        jobId: attachment?.type === 'job' ? attachment.id : null,
        eventId: attachment?.type === 'event' ? attachment.id : null,
      })
      setBody('')
      setAttachment(null)
    } catch (err) {
      setError(errorMessage(err, 'Message could not be sent'))
    } finally {
      setSending(false)
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <div className="border-t border-gray-100 p-3">
      {attachment && (
        <div className="mb-2 inline-flex max-w-full items-center gap-2 rounded-lg bg-brand-50 px-2.5 py-1.5 text-sm text-brand-800">
          {attachment.type === 'job' ? <Briefcase size={14} aria-hidden="true" /> : <CalendarDays size={14} aria-hidden="true" />}
          <span className="truncate">
            {attachment.type === 'job' ? 'Invite to apply: ' : 'Invite to event: '}
            <strong className="font-medium">{attachment.title}</strong>
          </span>
          <button
            onClick={() => setAttachment(null)}
            className="rounded p-0.5 hover:bg-brand-100"
            aria-label="Remove attachment"
          >
            <X size={14} />
          </button>
        </div>
      )}

      <label htmlFor="message-body" className="sr-only">
        Message to {student.name}
      </label>
      <textarea
        id="message-body"
        rows={3}
        value={body}
        onChange={(event) => setBody(event.target.value)}
        onKeyDown={handleKeyDown}
        maxLength={5000}
        placeholder={`Message ${student.name}…`}
        className="w-full resize-none rounded-xl border border-gray-300 px-3 py-2 text-sm focus:border-brand-400"
      />
      {error && (
        <p className="mt-1 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

      <div className="mt-2 flex flex-wrap items-center gap-1">
        <Popover label="Templates" icon={FileText}>
          {(close) =>
            MESSAGE_TEMPLATES.map((template) => (
              <PopoverItem
                key={template.id}
                title={template.label}
                onClick={() => {
                  fill(template.build({ student, company: companyName }))
                  close()
                }}
              />
            ))
          }
        </Popover>

        <Popover label="Invite to apply" icon={Briefcase}>
          {(close) =>
            jobs.length === 0 ? (
              <p className="px-3 py-2 text-sm text-gray-500">No open jobs to invite to.</p>
            ) : (
              jobs.map((job) => (
                <PopoverItem
                  key={job.id}
                  title={job.title}
                  subtitle={`${job.city} · Apply by ${formatDate(job.deadline)}`}
                  onClick={() => {
                    setAttachment({ type: 'job', id: job.id, title: job.title })
                    if (!body.trim()) setBody(inviteToApplyText({ student, job }))
                    close()
                  }}
                />
              ))
            )
          }
        </Popover>

        <Popover label="Invite to event" icon={CalendarDays}>
          {(close) =>
            events.length === 0 ? (
              <p className="px-3 py-2 text-sm text-gray-500">No upcoming events to invite to.</p>
            ) : (
              events.map((event) => (
                <PopoverItem
                  key={event.id}
                  title={event.name}
                  subtitle={formatDate(event.event_date)}
                  onClick={() => {
                    setAttachment({ type: 'event', id: event.id, title: event.name })
                    if (!body.trim()) setBody(inviteToEventText({ student, event, date: formatDate(event.event_date) }))
                    close()
                  }}
                />
              ))
            )
          }
        </Popover>

        <span className="ml-auto hidden text-xs text-gray-400 sm:inline">Enter to send · Shift+Enter for a new line</span>
        <Button size="sm" icon={Send} onClick={submit} disabled={!body.trim() || sending} className="ml-2">
          {sending ? 'Sending…' : 'Send'}
        </Button>
      </div>
    </div>
  )
}
