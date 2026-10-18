import { Bot } from 'lucide-react'
import RichText from './RichText'

export default function MessageBubble({ role, content, children }) {
  const isUser = role === 'user'

  return (
    <div className={`flex gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <span className="mt-1 flex size-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700">
          <Bot size={15} aria-hidden="true" />
        </span>
      )}
      <div
        className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-6 ${
          isUser ? 'rounded-br-md bg-brand-600 text-white' : 'rounded-bl-md bg-gray-100 text-gray-800'
        }`}
      >
        {isUser ? <p className="whitespace-pre-wrap">{content}</p> : <RichText text={content} />}
        {children}
      </div>
    </div>
  )
}
