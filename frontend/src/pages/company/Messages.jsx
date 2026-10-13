import { useCallback, useEffect, useState } from 'react'
import { Link, useOutletContext, useSearchParams } from 'react-router-dom'
import { ArrowLeft, MessageSquare, PenSquare } from 'lucide-react'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Avatar from '../../components/ui/Avatar'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import ErrorMessage from '../../components/common/ErrorMessage'
import ConversationList from '../../components/messages/ConversationList'
import MessageThread from '../../components/messages/MessageThread'
import MessageComposer from '../../components/messages/MessageComposer'
import ContactPanel from '../../components/messages/ContactPanel'
import NewConversationModal from '../../components/messages/NewConversationModal'
import { useFetch } from '../../hooks/useFetch'
import { usePermissions } from '../../hooks/usePermissions'
import {
  getConversation,
  getConversations,
  markConversationRead,
  sendMessage,
  startConversation,
} from '../../services/messageService'
import { getMyJobs } from '../../services/jobService'
import { getMyEvents } from '../../services/eventService'
import { isOnOrAfterToday } from '../../utils/format'

const POLL_MS = 10_000

export default function Messages() {
  const { company, reloadCompany } = useOutletContext()
  const { can } = usePermissions()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeId = Number(searchParams.get('c')) || null

  const [query, setQuery] = useState('')
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [composeOpen, setComposeOpen] = useState(false)

  const list = useFetch(() => getConversations({ q: query.trim(), unreadOnly }), [query, unreadOnly])
  const thread = useFetch(() => (activeId ? getConversation(activeId) : Promise.resolve(null)), [activeId])
  const jobs = useFetch(getMyJobs, [])
  const events = useFetch(getMyEvents, [])

  const openJobs = (jobs.data || []).filter((job) => isOnOrAfterToday(job.deadline))
  const upcomingEvents = (events.data || []).filter((event) => isOnOrAfterToday(event.event_date))

  const select = (id) => setSearchParams(id ? { c: String(id) } : {})

  // Silent refresh: patch data in place so polling never flashes skeletons.
  const refreshList = useCallback(() => {
    getConversations({ q: query.trim(), unreadOnly }).then(list.setData).catch(() => {})
  }, [query, unreadOnly]) // eslint-disable-line react-hooks/exhaustive-deps

  const refreshThread = useCallback(() => {
    if (activeId) getConversation(activeId).then(thread.setData).catch(() => {})
  }, [activeId]) // eslint-disable-line react-hooks/exhaustive-deps

  // Whenever the open thread has unread messages from the student, mark
  // them read and refresh the counts (list badges + sidebar badge).
  const unreadInThread = (thread.data?.id === activeId && thread.data.unread_count) || 0
  useEffect(() => {
    if (!activeId || unreadInThread === 0) return
    markConversationRead(activeId)
      .then(() => {
        refreshList()
        refreshThread()
        reloadCompany()
      })
      .catch(() => {})
  }, [activeId, unreadInThread]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const timer = setInterval(() => {
      refreshList()
      refreshThread()
    }, POLL_MS)
    return () => clearInterval(timer)
  }, [refreshList, refreshThread])

  const handleSend = async (message) => {
    const sent = await sendMessage(activeId, message)
    thread.setData((current) => ({ ...current, messages: [...current.messages, sent] }))
    refreshList()
  }

  const handlePick = async (student) => {
    const conversation = await startConversation(student.account_id)
    setComposeOpen(false)
    refreshList()
    select(conversation.id)
  }

  // Ignore the previous thread's data while the newly selected one loads.
  const conversation = thread.data?.id === activeId ? thread.data : null

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Messages</h1>
          <p className="mt-0.5 text-sm text-gray-500">Conversations with students, shared across your team.</p>
        </div>
        {can('messages:write') && (
          <Button icon={PenSquare} onClick={() => setComposeOpen(true)}>
            New message
          </Button>
        )}
      </div>

      <ErrorMessage message={list.error} />

      <Card className="grid h-[calc(100vh-13rem)] min-h-[32rem] grid-cols-1 overflow-hidden md:grid-cols-[18rem_1fr] xl:grid-cols-[18rem_1fr_17rem]">
        <div className={`min-h-0 border-gray-100 md:border-r ${activeId ? 'hidden md:block' : ''}`}>
          <ConversationList
            conversations={list.data}
            loading={list.loading}
            activeId={activeId}
            onSelect={select}
            query={query}
            onQueryChange={setQuery}
            unreadOnly={unreadOnly}
            onUnreadOnlyChange={setUnreadOnly}
          />
        </div>

        <section
          className={`flex min-h-0 min-w-0 flex-col ${activeId ? '' : 'hidden md:flex'}`}
          aria-label="Conversation"
        >
          {!activeId ? (
            <div className="flex flex-1 items-center justify-center p-6">
              <EmptyState
                icon={MessageSquare}
                title={list.data?.length ? 'Select a conversation' : 'No conversations yet'}
                description={
                  list.data?.length
                    ? 'Choose a student on the left to read and reply.'
                    : 'Message a student from their profile, or start a new conversation.'
                }
              />
            </div>
          ) : thread.error ? (
            <div className="p-4">
              <ErrorMessage message={thread.error} />
            </div>
          ) : !conversation ? (
            <div className="space-y-3 p-4">
              <Skeleton className="h-10 w-48" />
              <Skeleton className="h-16 w-2/3" />
              <Skeleton className="ml-auto h-16 w-1/2" />
            </div>
          ) : (
            <>
              <header className="flex items-center gap-3 border-b border-gray-100 px-4 py-3">
                <button
                  onClick={() => select(null)}
                  className="rounded-lg p-1 text-gray-500 hover:bg-gray-100 md:hidden"
                  aria-label="Back to conversations"
                >
                  <ArrowLeft size={18} />
                </button>
                <Avatar name={conversation.student.name} size="sm" />
                <div className="min-w-0">
                  <Link
                    to={`/company/students/${conversation.student.account_id}`}
                    className="block truncate font-medium text-gray-900 hover:text-brand-700"
                  >
                    {conversation.student.name}
                  </Link>
                  <p className="truncate text-xs text-gray-500">{conversation.student.college_name}</p>
                </div>
              </header>
              <MessageThread messages={conversation.messages} />
              <MessageComposer
                key={conversation.id}
                conversation={conversation}
                companyName={company?.company_name}
                jobs={openJobs}
                events={upcomingEvents}
                canWrite={can('messages:write')}
                onSend={handleSend}
              />
            </>
          )}
        </section>

        <div className="hidden min-h-0 border-l border-gray-100 xl:block">
          {conversation && activeId ? <ContactPanel student={conversation.student} /> : null}
        </div>
      </Card>

      <NewConversationModal open={composeOpen} onClose={() => setComposeOpen(false)} onPick={handlePick} />
    </div>
  )
}

