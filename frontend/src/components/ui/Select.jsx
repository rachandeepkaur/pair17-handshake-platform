import { Check, ChevronDown } from 'lucide-react'
import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

const SIZES = {
  sm: 'h-9 text-sm',
  md: 'h-10 text-sm',
}
const MENU_MAX_HEIGHT = 288 // px, about 8 options

/**
 * A styled replacement for <select>: a button that opens a listbox.
 *
 * onChange receives an event-like object, { target: { name, value } }, so it
 * plugs into the same handlers a native select used (useForm, setters).
 * The menu is portalled to <body> with fixed positioning, so tables, cards
 * with overflow-hidden, and modals never clip it; it flips above the button
 * when there is no room below.
 */
export default function Select({
  value,
  onChange,
  options,
  name,
  id,
  size = 'md',
  disabled = false,
  invalid = false,
  className = '',
  menuClassName = '',
  'aria-label': ariaLabel,
  'aria-describedby': ariaDescribedBy,
  onBlur,
}) {
  const autoId = useId()
  const buttonId = id || name || `select-${autoId}`
  const listId = `${buttonId}-listbox`
  const buttonRef = useRef(null)
  const listRef = useRef(null)
  const typeahead = useRef({ text: '', at: 0 })
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const [position, setPosition] = useState(null)

  const selectedIndex = options.findIndex((option) => String(option.value) === String(value ?? ''))
  const selected = options[selectedIndex]

  const place = useCallback(() => {
    const rect = buttonRef.current?.getBoundingClientRect()
    if (!rect) return
    const below = window.innerHeight - rect.bottom - 8
    const above = rect.top - 8
    const flip = below < Math.min(MENU_MAX_HEIGHT, 160) && above > below
    setPosition({
      left: rect.left,
      minWidth: rect.width,
      maxWidth: Math.max(rect.width, Math.min(360, window.innerWidth - rect.left - 8)),
      maxHeight: Math.min(MENU_MAX_HEIGHT, flip ? above : below),
      ...(flip ? { bottom: window.innerHeight - rect.top + 4 } : { top: rect.bottom + 4 }),
    })
  }, [])

  const openMenu = (index = selectedIndex) => {
    if (disabled) return
    place()
    setActive(index >= 0 ? index : 0)
    setOpen(true)
  }

  const close = (refocus = true) => {
    setOpen(false)
    if (refocus) buttonRef.current?.focus()
  }

  const choose = (index) => {
    const option = options[index]
    if (!option || option.disabled) return
    close()
    if (String(option.value) !== String(value ?? '')) onChange?.({ target: { name, value: option.value } })
  }

  // Keep the menu attached to the button while the page scrolls or resizes.
  useLayoutEffect(() => {
    if (!open) return undefined
    place()
    window.addEventListener('resize', place)
    window.addEventListener('scroll', place, true)
    return () => {
      window.removeEventListener('resize', place)
      window.removeEventListener('scroll', place, true)
    }
  }, [open, place])

  // Close on a click anywhere outside the button and the menu.
  useEffect(() => {
    if (!open) return undefined
    const onPointerDown = (event) => {
      if (buttonRef.current?.contains(event.target) || listRef.current?.contains(event.target)) return
      close(false)
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [open])

  // Keep the highlighted option in view inside the menu (not the page).
  useEffect(() => {
    if (!open || active < 0) return
    const list = listRef.current
    const item = list?.children[active]
    if (!list || !item) return
    if (item.offsetTop < list.scrollTop) list.scrollTop = item.offsetTop
    else if (item.offsetTop + item.offsetHeight > list.scrollTop + list.clientHeight)
      list.scrollTop = item.offsetTop + item.offsetHeight - list.clientHeight
  }, [open, active])

  const move = (from, step) => {
    for (let i = 1; i <= options.length; i += 1) {
      const next = (from + step * i + options.length) % options.length
      if (!options[next].disabled) return next
    }
    return from
  }

  const handleKeyDown = (event) => {
    const { key } = event
    if (!open) {
      if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(key)) {
        event.preventDefault()
        openMenu(key === 'ArrowUp' ? move(selectedIndex, -1) : selectedIndex)
      }
      return
    }
    if (key === 'Escape') {
      event.preventDefault()
      event.stopPropagation() // don't also close a surrounding modal
      close()
    } else if (key === 'Tab') {
      close(false)
    } else if (key === 'ArrowDown' || key === 'ArrowUp') {
      event.preventDefault()
      setActive((current) => move(current, key === 'ArrowDown' ? 1 : -1))
    } else if (key === 'Home' || key === 'End') {
      event.preventDefault()
      setActive(key === 'Home' ? move(-1, 1) : move(options.length, -1))
    } else if (key === 'Enter' || key === ' ') {
      event.preventDefault()
      choose(active)
    } else if (key.length === 1 && !event.metaKey && !event.ctrlKey && !event.altKey) {
      // Type-ahead: jump to the first option starting with the typed letters.
      const now = Date.now()
      const text = (now - typeahead.current.at < 700 ? typeahead.current.text : '') + key.toLowerCase()
      typeahead.current = { text, at: now }
      const match = options.findIndex((option) => !option.disabled && String(option.label).toLowerCase().startsWith(text))
      if (match >= 0) setActive(match)
    }
  }

  return (
    <>
      <button
        ref={buttonRef}
        id={buttonId}
        name={name}
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listId : undefined}
        aria-activedescendant={open && active >= 0 ? `${listId}-${active}` : undefined}
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        aria-invalid={invalid || undefined}
        disabled={disabled}
        onClick={() => (open ? close() : openMenu())}
        onKeyDown={handleKeyDown}
        onBlur={onBlur ? () => !open && onBlur({ target: { name, value } }) : undefined}
        className={`inline-flex w-full items-center justify-between gap-2 rounded-xl border bg-white pl-3 pr-2.5 text-left text-gray-900 transition-colors hover:border-gray-400 focus:outline-none focus-visible:border-brand-400 focus-visible:ring-2 focus-visible:ring-brand-100 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:border-gray-300 ${
          open ? 'border-brand-400 ring-2 ring-brand-100' : invalid ? 'border-red-400' : 'border-gray-300'
        } ${SIZES[size] || SIZES.md} ${className}`}
      >
        <span className={`truncate ${selected ? '' : 'text-gray-400'}`}>{selected ? selected.label : 'Select…'}</span>
        <ChevronDown
          size={16}
          aria-hidden="true"
          className={`shrink-0 text-gray-400 transition-transform duration-150 ${open ? 'rotate-180 text-brand-600' : ''}`}
        />
      </button>

      {open &&
        position &&
        createPortal(
          <ul
            ref={listRef}
            id={listId}
            role="listbox"
            aria-labelledby={ariaLabel ? undefined : buttonId}
            aria-label={ariaLabel}
            style={position}
            className={`fixed z-[60] animate-fade-in overflow-y-auto rounded-xl border border-gray-200 bg-white p-1 text-sm shadow-pop ${menuClassName}`}
          >
            {options.map((option, index) => {
              const isSelected = index === selectedIndex
              return (
                <li
                  key={String(option.value)}
                  id={`${listId}-${index}`}
                  role="option"
                  aria-selected={isSelected}
                  aria-disabled={option.disabled || undefined}
                  onPointerMove={() => !option.disabled && active !== index && setActive(index)}
                  onClick={() => choose(index)}
                  className={`flex cursor-pointer items-center gap-2 rounded-lg px-2.5 py-2 ${
                    option.disabled
                      ? 'cursor-not-allowed text-gray-300'
                      : index === active
                        ? 'bg-brand-50 text-brand-800'
                        : 'text-gray-700'
                  }`}
                >
                  <span className="min-w-0 flex-1">
                    <span className={`block truncate ${isSelected ? 'font-semibold' : ''}`}>{option.label}</span>
                    {option.description && <span className="block truncate text-xs text-gray-500">{option.description}</span>}
                  </span>
                  <Check
                    size={15}
                    aria-hidden="true"
                    className={`shrink-0 text-brand-600 ${isSelected ? 'visible' : 'invisible'}`}
                  />
                </li>
              )
            })}
          </ul>,
          document.body,
        )}
    </>
  )
}
