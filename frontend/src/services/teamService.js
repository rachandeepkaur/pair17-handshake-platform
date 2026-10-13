import api from './api'

export const getMyMembership = () => api.get('/team/me').then((res) => res.data)
export const updateMyName = (name) => api.patch('/team/me', { name }).then((res) => res.data)
export const getPermissionMatrix = () => api.get('/team/permissions').then((res) => res.data)

export const getMembers = () => api.get('/team/members').then((res) => res.data)
export const updateMemberRole = (memberId, role) =>
  api.patch(`/team/members/${memberId}`, { role }).then((res) => res.data)
export const removeMember = (memberId) => api.delete(`/team/members/${memberId}`)

export const getInvitations = () => api.get('/team/invitations').then((res) => res.data)
export const createInvitation = (data) => api.post('/team/invitations', data).then((res) => res.data)
export const regenerateInvitation = (invitationId) =>
  api.post(`/team/invitations/${invitationId}/regenerate`).then((res) => res.data)
export const revokeInvitation = (invitationId) => api.delete(`/team/invitations/${invitationId}`)

// Public — the invitee isn't signed in yet.
export const previewInvitation = (token) =>
  api.get(`/team/invitations/token/${encodeURIComponent(token)}`).then((res) => res.data)
export const acceptInvitation = (token, data) =>
  api.post(`/team/invitations/token/${encodeURIComponent(token)}/accept`, data).then((res) => res.data)

// The API never returns a usable link (it only knows the token), and only
// right after creating or regenerating an invite.
export const inviteLink = (token) => `${window.location.origin}/invite/${token}`
