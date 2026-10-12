const PALETTE = [
  'bg-brand-100 text-brand-700',
  'bg-accent-100 text-accent-700',
  'bg-amber-100 text-amber-700',
  'bg-violet-100 text-violet-700',
  'bg-cyan-100 text-cyan-700',
  'bg-rose-100 text-rose-700',
]

function initials(name = '') {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

const SIZES = { sm: 'h-8 w-8 text-xs', md: 'h-10 w-10 text-sm', lg: 'h-12 w-12 text-base' }

export default function Avatar({ name = '', size = 'md', className = '' }) {
  const color = PALETTE[(name.charCodeAt(0) || 0) % PALETTE.length]
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-full font-semibold ${color} ${SIZES[size]} ${className}`}
      title={name}
    >
      {initials(name) || '?'}
    </span>
  )
}
