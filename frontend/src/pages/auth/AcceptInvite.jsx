import { useNavigate, useParams } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import FormField from '../../components/common/FormField'
import ErrorMessage from '../../components/common/ErrorMessage'
import { useAuth } from '../../hooks/useAuth'
import { useFetch } from '../../hooks/useFetch'
import { useForm } from '../../hooks/useForm'
import { acceptInvitation, previewInvitation } from '../../services/teamService'
import { formatDate } from '../../utils/format'
import { composeValidators, maxLength, minLength, required } from '../../utils/validators'

function JoinForm({ token, invitation }) {
  const navigate = useNavigate()
  const { startSession } = useAuth()

  const { values, errors, isSubmitting, submitError, handleChange, handleBlur, handleSubmit } = useForm({
    initialValues: { name: invitation.name, password: '', confirm: '' },
    validators: {
      name: composeValidators(required('Name is required'), maxLength(150)),
      password: composeValidators(required('Choose a password'), minLength(8), maxLength(72)),
      confirm: (value) => (value !== values.password ? 'Passwords don’t match' : undefined),
    },
    onSubmit: async ({ name, password }) => {
      startSession(await acceptInvitation(token, { name: name.trim(), password }))
      navigate('/company/dashboard', { replace: true })
    },
  })

  return (
    <form onSubmit={handleSubmit} noValidate>
      <FormField label="Email" name="email" value={invitation.email} readOnly disabled />
      <FormField label="Your name" name="name" value={values.name} onChange={handleChange} onBlur={handleBlur} error={errors.name} />
      <FormField
        label="Password"
        name="password"
        type="password"
        autoComplete="new-password"
        value={values.password}
        onChange={handleChange}
        onBlur={handleBlur}
        error={errors.password}
        hint="At least 8 characters."
      />
      <FormField
        label="Confirm password"
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
      <Button type="submit" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? 'Joining…' : `Join ${invitation.company_name}`}
      </Button>
    </form>
  )
}

export default function AcceptInvite() {
  const { token } = useParams()
  const { data: invitation, loading, error } = useFetch(() => previewInvitation(token), [token])

  return (
    <div className="flex min-h-screen items-start justify-center bg-canvas px-4 py-16">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-center gap-2">
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
            <Sparkles size={20} aria-hidden="true" />
          </span>
          <span className="text-xl font-bold tracking-tight">Hirely</span>
        </div>

        <div className="rounded-2xl border border-gray-200/80 bg-white p-6 shadow-card">
          {loading ? (
            <Skeleton className="h-64" />
          ) : error ? (
            <>
              <h1 className="text-lg font-semibold text-gray-900">Invitation unavailable</h1>
              <div className="mt-3">
                <ErrorMessage message={error} />
              </div>
            </>
          ) : (
            <>
              <h1 className="text-lg font-semibold text-gray-900">Join {invitation.company_name}</h1>
              <p className="mt-1 mb-5 text-sm text-gray-600">
                You’ve been invited as <strong className="font-medium text-gray-900">{invitation.role_label}</strong>.
                This link expires {formatDate(invitation.expires_at)}.
              </p>
              <JoinForm token={token} invitation={invitation} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
