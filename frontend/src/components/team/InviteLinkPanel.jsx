import { useRef, useState } from 'react'
import { Check, Copy } from 'lucide-react'
import Button from '../ui/Button'
import { inviteLink } from '../../services/teamService'

export default function InviteLinkPanel({ invitation }) {
  const inputRef = useRef(null)
  const [copied, setCopied] = useState(false)
  const link = inviteLink(invitation.token)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(link)
    } catch {
      // Clipboard API can be blocked (e.g. non-secure origin); fall back to
      // selecting the text so the user can copy it manually.
      inputRef.current?.select()
      document.execCommand?.('copy')
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-3">
      <p>
        Send this link to <strong className="font-medium text-gray-900">{invitation.email}</strong>. It signs them up
        as <strong className="font-medium text-gray-900">{invitation.role_label}</strong>, works once, and expires in 7
        days.
      </p>
      <div className="flex gap-2">
        <input
          ref={inputRef}
          readOnly
          value={link}
          aria-label="Invitation link"
          onFocus={(event) => event.target.select()}
          className="h-10 min-w-0 flex-1 rounded-xl border border-gray-300 bg-gray-50 px-3 text-sm text-gray-800"
        />
        <Button type="button" variant="outline" icon={copied ? Check : Copy} onClick={copy}>
          {copied ? 'Copied' : 'Copy'}
        </Button>
      </div>
      <p className="text-xs text-gray-500">
        This link is shown only now. If it’s lost, use “New link” on the pending invitation.
      </p>
    </div>
  )
}
