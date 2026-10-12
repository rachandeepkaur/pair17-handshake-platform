import { ChevronLeft, ChevronRight } from 'lucide-react'
import Button from '../ui/Button'

export default function Pagination({ total, limit, offset, onChange }) {
  if (total <= limit) return null

  const page = Math.floor(offset / limit) + 1
  const pages = Math.ceil(total / limit)

  return (
    <nav className="flex items-center justify-between gap-3" aria-label="Pagination">
      <p className="text-sm text-gray-500">
        Showing {offset + 1}–{Math.min(offset + limit, total)} of {total}
      </p>
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          icon={ChevronLeft}
          disabled={page <= 1}
          onClick={() => onChange(offset - limit)}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= pages}
          onClick={() => onChange(offset + limit)}
        >
          Next <ChevronRight size={16} />
        </Button>
      </div>
    </nav>
  )
}
