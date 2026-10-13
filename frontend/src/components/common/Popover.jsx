import { useEffect, useRef, useState } from 'react'

// A button that toggles a small floating panel; closes on outside click or
// Escape. `children` is a render function receiving `close`.
export default function Popover({ label, icon: Icon, disabled, align = 'left', placement = 'top', children }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const onClick = (event) => ref.current && !ref.current.contains(event.target) && setOpen(false)
    const onKey = (event) => event.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-haspopup="menu"
        className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {Icon && <Icon size={16} aria-hidden="true" />}
        {label}
      </button>
      {open && (
        <div
          role="menu"
          className={`absolute z-30 w-72 animate-fade-in rounded-xl border border-gray-200 bg-white p-1.5 shadow-pop ${
            placement === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'
          } ${align === 'right' ? 'right-0' : 'left-0'}`}
        >
          {children(() => setOpen(false))}
        </div>
      )}
    </div>
  )
}

export function PopoverItem({ onClick, title, subtitle }) {
  return (
    <button
      type="button"
      role="menuitem"
      onClick={onClick}
      className="block w-full rounded-lg px-3 py-2 text-left hover:bg-gray-50"
    >
      <span className="block truncate text-sm font-medium text-gray-900">{title}</span>
      {subtitle && <span className="block truncate text-xs text-gray-500">{subtitle}</span>}
    </button>
  )
}
