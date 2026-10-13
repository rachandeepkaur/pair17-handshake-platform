import { useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { KeyRound, UserRound } from 'lucide-react'
import Card, { CardHeader } from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import FormField from '../../components/common/FormField'
import { useForm } from '../../hooks/useForm'
import { usePermissions } from '../../hooks/usePermissions'
import { changePassword } from '../../services/authService'
import { updateMyName } from '../../services/teamService'
import { composeValidators, maxLength, minLength, required } from '../../utils/validators'

function Saved({ children }) {
  return (
    <p role="status" className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
      {children}
    </p>
  )
}

function ProfileForm({ member, onSaved }) {
  const [saved, setSaved] = useState(false)
  const { values, errors, isSubmitting, submitError, handleChange, handleBlur, handleSubmit } = useForm({
    initialValues: { name: member.name },
    validators: { name: composeValidators(required('Name is required'), maxLength(150)) },
    onSubmit: async ({ name }) => {
      setSaved(false)
      await updateMyName(name.trim())
      onSaved()
      setSaved(true)
    },
  })

  return (
    <form onSubmit={handleSubmit} noValidate className="p-5">
      {saved && <Saved>Name updated.</Saved>}
      <FormField
        label="Display name"
        name="name"
        value={values.name}
        onChange={handleChange}
        onBlur={handleBlur}
        error={errors.name}
        hint="Shown to students on messages you send, and to your teammates."
      />
      <FormField label="Login email" name="email" value={member.email} readOnly disabled hint="Contact an admin to change it." />
      <p className="mb-4 text-sm text-gray-600">
        Role: <span className="font-medium text-gray-900">{member.role_label}</span>
      </p>
      {submitError && <p className="mb-3 text-sm text-red-600">{submitError}</p>}
      <div className="flex justify-end">
        <Button type="submit" disabled={isSubmitting || values.name.trim() === member.name}>
          {isSubmitting ? 'Saving…' : 'Save'}
        </Button>
      </div>
    </form>
  )
}

function PasswordForm({ onChanged }) {
  const { values, errors, isSubmitting, submitError, handleChange, handleBlur, handleSubmit } = useForm({
    initialValues: { current: '', next: '', confirm: '' },
    validators: {
      current: required('Enter your current password'),
      next: composeValidators(required('Enter a new password'), minLength(8), maxLength(72)),
      confirm: (value) => (value !== values.next ? 'Passwords don’t match' : undefined),
    },
    onSubmit: async ({ current, next }) => {
      await changePassword(current, next)
      onChanged()
    },
  })

  return (
    <form onSubmit={handleSubmit} noValidate className="p-5">
      <FormField
        label="Current password"
        name="current"
        type="password"
        autoComplete="current-password"
        value={values.current}
        onChange={handleChange}
        onBlur={handleBlur}
        error={errors.current}
      />
      <FormField
        label="New password"
        name="next"
        type="password"
        autoComplete="new-password"
        value={values.next}
        onChange={handleChange}
        onBlur={handleBlur}
        error={errors.next}
        hint="At least 8 characters."
      />
      <FormField
        label="Confirm new password"
        name="confirm"
        type="password"
        autoComplete="new-password"
        value={values.confirm}
        onChange={handleChange}
        onBlur={handleBlur}
        error={errors.confirm}
      />
      {submitError && (
        <p className="mb-3 text-sm text-red-600" role="alert">
          {submitError}
        </p>
      )}
      <div className="flex justify-end">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Updating…' : 'Change password'}
        </Button>
      </div>
    </form>
  )
}

export default function Settings() {
  const { reloadCompany } = useOutletContext()
  const { member } = usePermissions()
  // Remounting the form (new key) clears its fields after a successful change.
  const [passwordChanges, setPasswordChanges] = useState(0)

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader title="Settings" description="Your personal account settings." />

      <Card>
        <CardHeader title="Your profile" action={<UserRound size={18} className="text-gray-400" aria-hidden="true" />} />
        {member ? <ProfileForm member={member} onSaved={reloadCompany} /> : <Skeleton className="m-5 h-40" />}
      </Card>

      <Card>
        <CardHeader title="Password" action={<KeyRound size={18} className="text-gray-400" aria-hidden="true" />} />
        {passwordChanges > 0 && (
          <div className="px-5 pt-5">
            <Saved>Password changed. Use your new password the next time you sign in.</Saved>
          </div>
        )}
        <PasswordForm key={passwordChanges} onChanged={() => setPasswordChanges((count) => count + 1)} />
      </Card>
    </div>
  )
}
