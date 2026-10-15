import { Link, useNavigate } from 'react-router-dom'
import FormField from '../../components/common/FormField'
import { useForm } from '../../hooks/useForm'
import { signupStudent } from '../../services/studentAuthService'
import { composeValidators, isEmail, minLength, required } from '../../utils/validators'

export default function StudentSignup() {
  const navigate = useNavigate()
  const { values, errors, isSubmitting, submitError, handleChange, handleBlur, handleSubmit } = useForm({
    initialValues: { name: '', email: '', password: '', college_name: '' },
    validators: {
      name: required('Name is required'),
      email: composeValidators(required('Email is required'), isEmail()),
      password: composeValidators(required('Password is required'), minLength(8)),
      college_name: required('College name is required'),
    },
    onSubmit: async (valuesToSubmit) => {
      await signupStudent(valuesToSubmit)
      navigate('/student/login', { replace: true })
    },
  })

  return (
    <main className="mx-auto mt-16 max-w-md rounded-2xl border border-gray-200 bg-white p-6 shadow-card">
      <p className="text-sm font-semibold text-brand-600">Student portal</p>
      <h1 className="mt-1 text-2xl font-bold tracking-tight text-gray-900">Create your account</h1>
      <p className="mt-2 text-sm text-gray-600">Start discovering jobs, events, and campus opportunities.</p>

      <form className="mt-6" onSubmit={handleSubmit} noValidate>
        <FormField label="Full name" name="name" value={values.name} onChange={handleChange} onBlur={handleBlur} error={errors.name} />
        <FormField label="Email" name="email" type="email" value={values.email} onChange={handleChange} onBlur={handleBlur} error={errors.email} />
        <FormField label="Password" name="password" type="password" value={values.password} onChange={handleChange} onBlur={handleBlur} error={errors.password} hint="Use at least 8 characters." />
        <FormField label="College name" name="college_name" value={values.college_name} onChange={handleChange} onBlur={handleBlur} error={errors.college_name} />
        {submitError && <p className="mb-4 text-sm text-red-600">{submitError}</p>}
        <button type="submit" disabled={isSubmitting} className="h-10 w-full rounded-xl bg-brand-600 text-sm font-semibold text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50">
          {isSubmitting ? 'Creating account…' : 'Create student account'}
        </button>
      </form>

      <p className="mt-5 text-center text-sm text-gray-600">
        Already have a student account?{' '}
        <Link to="/student/login" className="font-medium text-brand-700 hover:text-brand-800">Sign in</Link>
      </p>
    </main>
  )
}
