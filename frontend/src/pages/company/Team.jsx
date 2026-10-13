import { useState } from 'react'
import { Link2, Trash2, UserPlus } from 'lucide-react'
import Card, { CardHeader } from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Avatar from '../../components/ui/Avatar'
import PageHeader from '../../components/ui/PageHeader'
import { RowSkeleton } from '../../components/ui/Skeleton'
import ErrorMessage from '../../components/common/ErrorMessage'
import Modal, { ConfirmDialog } from '../../components/common/Modal'
import InviteModal from '../../components/team/InviteModal'
import InviteLinkPanel from '../../components/team/InviteLinkPanel'
import PermissionMatrix from '../../components/team/PermissionMatrix'
import { useFetch } from '../../hooks/useFetch'
import { usePermissions } from '../../hooks/usePermissions'
import { errorMessage } from '../../services/api'
import {
  getInvitations,
  getMembers,
  getPermissionMatrix,
  regenerateInvitation,
  removeMember,
  revokeInvitation,
  updateMemberRole,
} from '../../services/teamService'
import { formatDate, formatRelative } from '../../utils/format'

const ROLE_STYLES = {
  owner: 'bg-brand-50 text-brand-700',
  admin: 'bg-violet-50 text-violet-700',
  recruiter: 'bg-accent-50 text-accent-700',
  hiring_manager: 'bg-amber-50 text-amber-800',
  viewer: 'bg-gray-100 text-gray-600',
}

function RoleBadge({ role, label }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${ROLE_STYLES[role]}`}>{label}</span>
  )
}

function MemberRow({ member, roles, canManage, onChanged, onRemove }) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const editable = canManage && member.role !== 'owner' && !member.is_you

  const changeRole = async (event) => {
    setSaving(true)
    setError('')
    try {
      onChanged(await updateMemberRole(member.id, event.target.value))
    } catch (err) {
      setError(errorMessage(err, 'Could not change role'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <tr className="hover:bg-gray-50/60">
      <td className="px-5 py-3">
        <div className="flex items-center gap-3">
          <Avatar name={member.name} size="sm" />
          <div className="min-w-0">
            <p className="truncate font-medium text-gray-900">
              {member.name}
              {member.is_you && <span className="ml-1.5 text-xs font-normal text-gray-500">(you)</span>}
            </p>
            <p className="truncate text-xs text-gray-500">{member.email}</p>
          </div>
        </div>
      </td>
      <td className="px-5 py-3">
        {editable ? (
          <>
            <select
              value={member.role}
              onChange={changeRole}
              disabled={saving}
              aria-label={`Role for ${member.name}`}
              className="h-9 rounded-xl border border-gray-300 bg-white px-3 text-sm focus:border-brand-400 disabled:opacity-60"
            >
              {roles
                .filter((role) => role.key !== 'owner')
                .map((role) => (
                  <option key={role.key} value={role.key}>
                    {role.label}
                  </option>
                ))}
            </select>
            {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
          </>
        ) : (
          <RoleBadge role={member.role} label={member.role_label} />
        )}
      </td>
      <td className="whitespace-nowrap px-5 py-3 text-gray-600" title={member.last_active_at || undefined}>
        {formatRelative(member.last_active_at)}
      </td>
      <td className="px-5 py-3 text-right">
        {editable && (
          <Button variant="ghost" size="sm" icon={Trash2} onClick={() => onRemove(member)} aria-label={`Remove ${member.name}`}>
            <span className="hidden sm:inline">Remove</span>
          </Button>
        )}
      </td>
    </tr>
  )
}

export default function Team() {
  const { can, loaded } = usePermissions()
  const canManage = can('team:manage')

  const matrix = useFetch(getPermissionMatrix, [])
  const members = useFetch(getMembers, [])
  // Only managers may list invitations; don't fire a request that would 403.
  const invitations = useFetch(() => (canManage ? getInvitations() : Promise.resolve([])), [canManage])

  const [inviteOpen, setInviteOpen] = useState(false)
  const [newLink, setNewLink] = useState(null)
  const [confirm, setConfirm] = useState(null)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState('')

  const patchMember = (updated) =>
    members.setData((list) => list.map((member) => (member.id === updated.id ? updated : member)))

  const runConfirmed = async () => {
    setBusy(true)
    setActionError('')
    try {
      if (confirm.type === 'member') {
        await removeMember(confirm.item.id)
        members.setData((list) => list.filter((member) => member.id !== confirm.item.id))
      } else {
        await revokeInvitation(confirm.item.id)
        invitations.setData((list) => list.filter((invitation) => invitation.id !== confirm.item.id))
      }
      setConfirm(null)
    } catch (err) {
      setActionError(errorMessage(err))
      setConfirm(null)
    } finally {
      setBusy(false)
    }
  }

  const issueNewLink = async (invitation) => {
    setActionError('')
    try {
      const updated = await regenerateInvitation(invitation.id)
      invitations.setData((list) => list.map((item) => (item.id === updated.id ? updated : item)))
      setNewLink(updated)
    } catch (err) {
      setActionError(errorMessage(err))
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Team & Permissions"
        description="Manage who can access your recruiting workspace and what they can do."
        actions={
          canManage && (
            <Button icon={UserPlus} onClick={() => setInviteOpen(true)} disabled={!matrix.data}>
              Invite Teammate
            </Button>
          )
        }
      />

      <ErrorMessage message={members.error || matrix.error || invitations.error || actionError} />
      {loaded && !canManage && (
        <p className="rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-600">
          Only Owners and Admins can invite or manage teammates.
        </p>
      )}

      <Card className="overflow-hidden">
        <CardHeader title="Members" subtitle={members.data && `${members.data.length} teammate${members.data.length === 1 ? '' : 's'}`} />
        {members.loading || !matrix.data ? (
          <div className="px-5">
            <RowSkeleton />
            <RowSkeleton />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px] text-left text-sm">
              <thead className="border-b border-gray-100 bg-gray-50/60 text-xs uppercase tracking-wide text-gray-500">
                <tr>
                  <th className="px-5 py-3 font-medium">Member</th>
                  <th className="px-5 py-3 font-medium">Role</th>
                  <th className="px-5 py-3 font-medium">Last active</th>
                  <th className="px-5 py-3">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {members.data.map((member) => (
                  <MemberRow
                    key={member.id}
                    member={member}
                    roles={matrix.data.roles}
                    canManage={canManage}
                    onChanged={patchMember}
                    onRemove={(item) => setConfirm({ type: 'member', item })}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {canManage && (
        <Card className="overflow-hidden">
          <CardHeader title="Pending invitations" subtitle="Links are single-use and expire after 7 days." />
          {invitations.loading ? (
            <div className="px-5">
              <RowSkeleton />
            </div>
          ) : invitations.data?.length === 0 ? (
            <p className="px-5 py-6 text-sm text-gray-500">No pending invitations.</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {invitations.data.map((invitation) => (
                <li key={invitation.id} className="flex flex-wrap items-center gap-3 px-5 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-gray-900">
                      {invitation.name} <span className="font-normal text-gray-500">· {invitation.email}</span>
                    </p>
                    <p className={`text-xs ${invitation.expired ? 'font-medium text-red-600' : 'text-gray-500'}`}>
                      {invitation.role_label} · {invitation.expired ? 'Expired' : `Expires ${formatDate(invitation.expires_at)}`}
                    </p>
                  </div>
                  <Button variant="outline" size="sm" icon={Link2} onClick={() => issueNewLink(invitation)}>
                    New link
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setConfirm({ type: 'invitation', item: invitation })}>
                    Revoke
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {matrix.data && <PermissionMatrix matrix={matrix.data} />}

      {inviteOpen && matrix.data && (
        <InviteModal
          open
          roles={matrix.data.roles}
          onClose={() => setInviteOpen(false)}
          onInvited={invitations.reload}
        />
      )}

      <Modal open={Boolean(newLink)} title="New invitation link" onClose={() => setNewLink(null)} footer={<Button onClick={() => setNewLink(null)}>Done</Button>}>
        {newLink && <InviteLinkPanel invitation={newLink} />}
      </Modal>

      <ConfirmDialog
        open={Boolean(confirm)}
        busy={busy}
        title={confirm?.type === 'member' ? `Remove ${confirm.item.name}?` : 'Revoke this invitation?'}
        message={
          confirm?.type === 'member'
            ? 'Their login will be deleted and they’ll lose access immediately. Messages and jobs they created stay with the company.'
            : `The link sent to ${confirm?.item.email} will stop working.`
        }
        confirmLabel={confirm?.type === 'member' ? 'Remove' : 'Revoke'}
        onConfirm={runConfirmed}
        onCancel={() => setConfirm(null)}
      />
    </div>
  )
}
