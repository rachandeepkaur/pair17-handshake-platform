import { Shield } from 'lucide-react'
import ComingSoon from '../../components/common/ComingSoon'

export default function Team() {
  return (
    <ComingSoon
      icon={Shield}
      title="Team & Permissions"
      description="Manage who can access your recruiting workspace."
      features={[
        'Invite teammates by email',
        'Roles: Owner, Admin, Recruiter, Hiring Manager, Viewer',
        'Permission matrix for jobs, applicants, and events',
        'Pending invitations',
        'Last active timestamps',
        'Remove or change a teammate’s access',
      ]}
    />
  )
}
