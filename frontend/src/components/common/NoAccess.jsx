import { Lock } from 'lucide-react'
import EmptyState from '../ui/EmptyState'

export default function NoAccess({ roleLabel, action }) {
  return (
    <EmptyState
      icon={Lock}
      title="You don’t have access to this"
      description={`Your role${roleLabel ? ` (${roleLabel})` : ''} can’t ${action}. Ask an Owner or Admin to change your role.`}
    />
  )
}
