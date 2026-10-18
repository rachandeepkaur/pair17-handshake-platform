import { Bot, Briefcase, CalendarDays, Info, RotateCcw, Search, Sliders } from 'lucide-react'
import Card, { CardHeader } from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import PageHeader from '../../components/ui/PageHeader'
import ChatWindow, { SUGGESTIONS } from '../../components/assistant/ChatWindow'
import { useAssistantChat } from '../../hooks/useAssistantChat'

const CAPABILITIES = [
  { icon: Sliders, title: 'Uses your profile', text: 'Reads your saved preferences, or your city, major, and skills.' },
  { icon: Search, title: 'Searches jobs', text: 'Filters by title, company, type, city, salary, skills, deadline, or remote.' },
  { icon: Briefcase, title: 'Explains a job', text: 'Gives full details and company info for any job ID.' },
  { icon: CalendarDays, title: 'Finds events', text: 'Searches upcoming events by name, city, date, or major.' },
]

export default function Assistant() {
  const chat = useAssistantChat()
  const hasConversation = chat.conversation.length > 0

  return (
    <div className="space-y-5">
      <PageHeader
        title="Career assistant"
        description="Ask in plain English. Answers come only from jobs and events listed on Hirely."
        actions={
          hasConversation && (
            <Button variant="outline" icon={RotateCcw} onClick={chat.reset} disabled={chat.loading}>
              New chat
            </Button>
          )
        }
      />

      {chat.error && (
        <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {chat.error}
        </p>
      )}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_18rem]">
        <Card className="overflow-hidden">
          <div className="flex items-center gap-3 border-b border-gray-100 px-5 py-3">
            <span className="flex size-9 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
              <Bot size={20} aria-hidden="true" />
            </span>
            <div>
              <p className="font-semibold text-gray-900">Hirely assistant</p>
              <p className="text-xs text-gray-500">Remembers this conversation, so you can ask follow-ups.</p>
            </div>
          </div>
          <ChatWindow chat={chat} heightClass="h-[calc(100vh-17rem)] min-h-[28rem]" />
        </Card>
      </div>
    </div>
  )
}
