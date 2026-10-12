import { MessageSquare } from 'lucide-react'
import ComingSoon from '../../components/common/ComingSoon'

export default function Messages() {
  return (
    <ComingSoon
      icon={MessageSquare}
      title="Messages"
      description="Communicate with candidates in one place."
      features={[
        'Conversation list with unread filters',
        'Message templates and attachments',
        'Candidate context panel',
        'Links to jobs and events',
        '“Invite to apply” and “Invite to event” actions',
        'Candidate profile preview',
      ]}
    />
  )
}
