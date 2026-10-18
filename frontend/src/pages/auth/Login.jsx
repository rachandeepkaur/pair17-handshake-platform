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

      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <h1 className="mb-6 text-xl font-semibold">Sign in</h1>
        <form onSubmit={handleSubmit} noValidate>
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
            className="w-full rounded-md bg-blue-600 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {isSubmitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <div className="mt-4 text-sm text-gray-600">
          <p>New here? Create a new account:</p>
          <div className="mt-2 flex gap-4">
            <Link to="/signup/student" className="text-blue-600">
              Student
            </Link>
            <Link to="/signup/company" className="text-blue-600">
              Company
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
