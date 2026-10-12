import { Settings as SettingsIcon } from 'lucide-react'
import ComingSoon from '../../components/common/ComingSoon'

export default function Settings() {
  return (
    <ComingSoon
      icon={SettingsIcon}
      title="Settings"
      description="Manage account, notifications, and workspace preferences."
      features={[
        'Account and login settings',
        'Notification preferences',
        'Email and calendar integrations',
        'Branding and workspace defaults',
        'Billing and plan',
        'Data export and privacy',
      ]}
    />
  )
}
