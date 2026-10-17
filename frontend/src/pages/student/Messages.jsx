import { useCallback, useEffect, useState } from 'react'
import { useOutletContext, useSearchParams } from 'react-router-dom'
import { ArrowLeft, MessageSquare } from 'lucide-react'
import Card from '../../components/ui/Card'
import Avatar from '../../components/ui/Avatar'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import ErrorMessage from '../../components/common/ErrorMessage'
import ConversationList from '../../components/messages/ConversationList'
import MessageThread from '../../components/messages/MessageThread'
import MessageComposer from '../../components/messages/MessageComposer'
import { useFetch } from '../../hooks/useFetch'
import { getConversation, getConversations, markConversationRead, sendMessage } from '../../services/messageService'

const POLL_MS = 10_000

export default function StudentMessages() {
  const { reloadInbox } = useOutletContext()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeId = Number(searchParams.get('c')) || null
  const [query, setQuery] = useState('')
  const [unreadOnly, setUnreadOnly] = useState(false)
  const list = useFetch(() => getConversations({ q: query.trim(), unreadOnly }), [query, unreadOnly])
  const thread = useFetch(() => (activeId ? getConversation(activeId) : Promise.resolve(null)), [activeId])
  const select = (id) => setSearchParams(id ? { c: String(id) } : {})

  const refreshList = useCallback(() => {
    getConversations({ q: query.trim(), unreadOnly }).then(list.setData).catch(() => {})
  }, [query, unreadOnly]) // eslint-disable-line react-hooks/exhaustive-deps
  const refreshThread = useCallback(() => {
    if (activeId) getConversation(activeId).then(thread.setData).catch(() => {})
  }, [activeId]) // eslint-disable-line react-hooks/exhaustive-deps

  const unreadInThread = (thread.data?.id === activeId && thread.data.unread_count) || 0
  useEffect(() => {
    if (!activeId || unreadInThread === 0) return
    markConversationRead(activeId).then(() => {
      refreshList()
      refreshThread()
      reloadInbox()
    }).catch(() => {})
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
  const conversation = thread.data?.id === activeId ? thread.data : null

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Inbox</h1>
        <p className="mt-0.5 text-sm text-gray-500">Conversations with employers.</p>
      </div>
      <ErrorMessage message={list.error} />
      <Card className="grid h-[calc(100vh-13rem)] min-h-[32rem] grid-cols-1 overflow-hidden md:grid-cols-[18rem_1fr]">
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
            participantSide="student"
          />
        </div>
        <section className={`flex min-h-0 min-w-0 flex-col ${activeId ? '' : 'hidden md:flex'}`} aria-label="Conversation">
          {!activeId ? (
            <div className="flex flex-1 items-center justify-center p-6">
              <EmptyState icon={MessageSquare} title={list.data?.length ? 'Select a conversation' : 'No conversations yet'} description={list.data?.length ? 'Choose an employer on the left to read and reply.' : 'Employers can start a conversation with you.'} />
            </div>
          ) : thread.error ? (
            <div className="p-4"><ErrorMessage message={thread.error} /></div>
          ) : !conversation ? (
            <div className="space-y-3 p-4"><Skeleton className="h-10 w-48" /><Skeleton className="h-16 w-2/3" /><Skeleton className="ml-auto h-16 w-1/2" /></div>
          ) : (
            <>
              <header className="flex items-center gap-3 border-b border-gray-100 px-4 py-3">
                <button onClick={() => select(null)} className="rounded-lg p-1 text-gray-500 hover:bg-gray-100 md:hidden" aria-label="Back to conversations"><ArrowLeft size={18} /></button>
                <Avatar name={conversation.company.company_name} size="sm" />
                <div className="min-w-0"><p className="truncate font-medium text-gray-900">{conversation.company.company_name}</p><p className="truncate text-xs text-gray-500">Employer</p></div>
              </header>
              <MessageThread messages={conversation.messages} participantSide="student" attachmentBasePath="/student" />
              <MessageComposer key={conversation.id} conversation={conversation} recipientName={conversation.company.company_name} showCompanyTools={false} onSend={handleSend} />
            </>
          )}
        </section>
      </Card>
    </div>
  )
}
