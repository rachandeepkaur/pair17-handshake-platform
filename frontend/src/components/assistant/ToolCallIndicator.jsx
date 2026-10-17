export default function ToolCallIndicator({ count }) {
  if (!count) return null

  return <p className="mt-2 text-xs text-gray-500">Used {count} {count === 1 ? 'tool call' : 'tool calls'}.</p>
}
