import { Bot } from 'lucide-react'

export default function MessageBubble({ role, content, children }) {
  const isUser = role === 'user'

  return (
    <div className={`flex gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && <span className="mt-1 flex size-6 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700"><Bot size={14} aria-hidden="true" /></span>}
      <div className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm leading-6 ${isUser ? 'bg-brand-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
        <p className="whitespace-pre-wrap">{content}</p>
        {children}
      </div>
    </div>
  )
}
