import { Link, useNavigate } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import FormField from '../../components/common/FormField'
import { useForm } from '../../hooks/useForm'
import { signupCompany } from '../../services/authService'
import { composeValidators, isEmail, minLength, required } from '../../utils/validators'

export default function CompanySignup() {
  const navigate = useNavigate()

  const { values, errors, isSubmitting, submitError, handleChange, handleBlur, handleSubmit } = useForm({
    initialValues: { company_name: '', email: '', password: '', location: '' },
    validators: {
      company_name: required('Company name is required'),
      email: composeValidators(required('Email is required'), isEmail()),
      password: composeValidators(required('Password is required'), minLength(8)),
      location: required('Location is required'),
    },
    onSubmit: async (vals) => {
      await signupCompany(vals)
      navigate('/login')
    },
  })

  return (
    <main className="mx-auto mt-16 max-w-md px-4">
      <Link to="/login" className="mb-6 flex items-center justify-center gap-2 rounded-lg">
        <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
          <Sparkles size={20} strokeWidth={2.5} aria-hidden="true" />
        </span>
        <span className="text-xl font-bold tracking-tight">Hirely</span>
      </Link>
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-card">
      <p className="text-sm font-semibold text-brand-600">Company portal</p>
      <h1 className="mt-1 text-2xl font-bold tracking-tight text-gray-900">Create a company account</h1>
      <form className="mt-6" onSubmit={handleSubmit} noValidate>
        <FormField
          label="Company name"
          name="company_name"
          value={values.company_name}
          onChange={handleChange}
          onBlur={handleBlur}
          error={errors.company_name}
        />
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
        <FormField
          label="Location"
          name="location"
          value={values.location}
          onChange={handleChange}
          onBlur={handleBlur}
          error={errors.location}
        />
        {submitError && <p className="mb-4 text-sm text-red-600">{submitError}</p>}
        <button
          type="submit"
          disabled={isSubmitting}
          className="h-10 w-full rounded-xl bg-brand-600 text-sm font-semibold text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? 'Creating account…' : 'Create company account'}
        </button>
      </form>
      <p className="mt-5 text-center text-sm text-gray-600">
        Already have an account?{' '}
        <Link to="/login" className="font-medium text-brand-700 hover:text-brand-800">
          Sign in
        </Link>
      </p>
      </div>
    </main>
  )
}
