import { Bookmark, Check, X } from 'lucide-react'
import Button from '../ui/Button'

// Shown when the assistant wants to change data (save a job or event). Nothing
// is saved until the student approves; declining tells the assistant to stop.
export default function ConfirmActionDialog({ action, onDecide, busy }) {
  return (
    <div
      role="alertdialog"
      aria-labelledby="confirm-action-title"
      aria-describedby="confirm-action-summary"
      className="rounded-2xl border border-amber-200 bg-amber-50 p-4"
    >
      <div className="flex items-start gap-3">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-700">
          <Bookmark size={18} aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <p id="confirm-action-title" className="text-sm font-semibold text-gray-900">
            The assistant wants to make a change
          </p>
          <p id="confirm-action-summary" className="mt-0.5 text-sm text-gray-700">
            {action.summary}. Nothing is saved unless you approve.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button autoFocus size="sm" icon={Check} onClick={() => onDecide(true)} disabled={busy}>
              Approve
            </Button>
            <Button size="sm" variant="outline" icon={X} onClick={() => onDecide(false)} disabled={busy}>
              Decline
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
