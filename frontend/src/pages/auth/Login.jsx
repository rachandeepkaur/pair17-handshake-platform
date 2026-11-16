import { Link, useNavigate } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import FormField from '../../components/common/FormField'
import { useAuth } from '../../hooks/useAuth'
import { useForm } from '../../hooks/useForm'
import { composeValidators, isEmail, required } from '../../utils/validators'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()

  const { values, errors, isSubmitting, submitError, handleChange, handleBlur, handleSubmit } = useForm({
    initialValues: { email: '', password: '' },
    validators: {
      email: composeValidators(required('Email is required'), isEmail()),
      password: required('Password is required'),
    },
    onSubmit: async (vals) => {
      const { role } = await login(vals)
      navigate(role === 'company' ? '/company/dashboard' : '/student/dashboard')
    },
  })

  return (
    <div className="mx-auto mt-16 max-w-md px-4">
      <Link to="/login" className="mb-6 flex items-center justify-center gap-2 rounded-lg">
        <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
          <Sparkles size={20} strokeWidth={2.5} aria-hidden="true" />
        </span>
        <span className="text-xl font-bold tracking-tight">Hirely</span>
      </Link>

      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-card">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Sign in</h1>
        <form className="mt-6" onSubmit={handleSubmit} noValidate>
          <FormField
            label="Email"
            name="email"
            type="email"
            value={values.email}
            onChange={handleChange}
            onBlur={handleBlur}
            error={errors.email}
          />
          <FormField
            label="Password"
            name="password"
            type="password"
            value={values.password}
            onChange={handleChange}
            onBlur={handleBlur}
            error={errors.password}
          />
          {submitError && <p className="mb-4 text-sm text-red-600">{submitError}</p>}
          <button
            type="submit"
            disabled={isSubmitting}
            className="h-10 w-full rounded-xl bg-brand-600 text-sm font-semibold text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="mt-5 text-center text-sm text-gray-600">
          New here? Create a{' '}
          <Link to="/signup/student" className="font-medium text-brand-700 hover:text-brand-800">
            student
          </Link>{' '}
          or{' '}
          <Link to="/signup/company" className="font-medium text-brand-700 hover:text-brand-800">
            company
          </Link>{' '}
          account
        </p>
      </div>
    </div>
  )
}
