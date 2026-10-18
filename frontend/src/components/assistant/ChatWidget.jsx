import { Link } from 'react-router-dom'
import { Maximize2 } from 'lucide-react'
import Card, { CardHeader } from '../ui/Card'
import ChatWindow from './ChatWindow'
import { useAssistantChat } from '../../hooks/useAssistantChat'

export default function ChatWidget() {
  const chat = useAssistantChat()

  return (
    <Card>
      <CardHeader
        title="Career assistant"
        subtitle="Search jobs and upcoming events using your Hirely data."
        action={
          <Link
            to="/student/assistant"
            className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-sm font-medium text-brand-600 hover:bg-brand-50"
          >
            <Maximize2 size={15} aria-hidden="true" /> Open full page
          </Link>
        }
      />
      {chat.error && (
        <p className="mx-5 mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {chat.error}
        </p>
      )}
      <ChatWindow chat={chat} />
    </Card>
  )
}
