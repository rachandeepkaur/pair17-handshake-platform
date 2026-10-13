import { useOutletContext } from 'react-router-dom'

// Reads the signed-in member's permissions from the company layout. The API
// enforces the same rules; this only hides actions that would be rejected.
// While the summary is still loading nothing is allowed, so write buttons
// never flash in and back out for read-only roles.
export function usePermissions() {
  const { company } = useOutletContext()
  const member = company?.member
  const permissions = new Set(member?.permissions || [])
  return {
    member,
    loaded: Boolean(member),
    can: (permission) => permissions.has(permission),
  }
}
