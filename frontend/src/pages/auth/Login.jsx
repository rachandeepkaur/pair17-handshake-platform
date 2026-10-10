import { Link, useNavigate } from 'react-router-dom'
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
    <div className="max-w-md mx-auto mt-16 p-6 border rounded-lg shadow-sm">
      <h1 className="text-xl font-semibold mb-6">Sign in</h1>
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
      <p className="mt-4 text-sm text-gray-600">
        New company?{' '}
        <Link to="/signup/company" className="text-blue-600">
          Create a company account
        </Link>
      </p>
    </div>
  )
}
