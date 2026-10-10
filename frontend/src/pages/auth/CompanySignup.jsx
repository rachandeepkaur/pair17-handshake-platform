import { Link, useNavigate } from 'react-router-dom'
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
    <div className="max-w-md mx-auto mt-16 p-6 border rounded-lg shadow-sm">
      <h1 className="text-xl font-semibold mb-6">Create a company account</h1>
      <form onSubmit={handleSubmit} noValidate>
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
          className="w-full rounded-md bg-blue-600 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {isSubmitting ? 'Creating account...' : 'Sign up'}
        </button>
      </form>
      <p className="mt-4 text-sm text-gray-600">
        Already have an account?{' '}
        <Link to="/login" className="text-blue-600">
          Sign in
        </Link>
      </p>
    </div>
  )
}
