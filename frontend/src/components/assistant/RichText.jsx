// Renders the small Markdown subset the model uses (paragraphs, numbered and
// bulleted lists, **bold**) as React elements, never as raw HTML.
function inline(text, keyPrefix) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) =>
    part.startsWith('**') && part.endsWith('**') && part.length > 4 ? (
      <strong key={`${keyPrefix}-${index}`} className="font-semibold">
        {part.slice(2, -2)}
      </strong>
    ) : (
      part
    ),
  )
}

export default function RichText({ text }) {
  const blocks = []
  let list = null

  text.split('\n').forEach((rawLine, index) => {
    const line = rawLine.trim()
    const numbered = line.match(/^(\d+)[.)]\s+(.*)$/)
    const bullet = line.match(/^[-*•]\s+(.*)$/)

    if (numbered || bullet) {
      const kind = numbered ? 'ol' : 'ul'
      if (!list || list.kind !== kind) {
        list = { kind, items: [] }
        blocks.push(list)
      }
      list.items.push(inline(numbered ? numbered[2] : bullet[1], `li-${index}`))
    } else if (line) {
      list = null
      blocks.push({ kind: 'p', content: inline(line, `p-${index}`) })
    } else {
      list = null
    }
  })

  return (
    <div className="space-y-2">
      {blocks.map((block, index) => {
        if (block.kind === 'p') return <p key={index}>{block.content}</p>
        const List = block.kind
        return (
          <List key={index} className={`space-y-1 pl-5 ${block.kind === 'ol' ? 'list-decimal' : 'list-disc'}`}>
            {block.items.map((item, itemIndex) => (
              <li key={itemIndex}>{item}</li>
            ))}
          </List>
        )
      })}
    </div>
  )
}
