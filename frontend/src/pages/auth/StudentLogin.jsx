import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import FormField from '../../components/common/FormField'
import { useAuth } from '../../hooks/useAuth'
import { useForm } from '../../hooks/useForm'
import { login as signIn } from '../../services/authService'
import { composeValidators, isEmail, required } from '../../utils/validators'

export default function StudentLogin() {
  const navigate = useNavigate()
  const { startSession } = useAuth()
  const [roleError, setRoleError] = useState('')
  const { values, errors, isSubmitting, submitError, handleChange, handleBlur, handleSubmit } = useForm({
    initialValues: { email: '', password: '' },
    validators: {
      email: composeValidators(required('Email is required'), isEmail()),
      password: required('Password is required'),
    },
    onSubmit: async (credentials) => {
      setRoleError('')
      const session = await signIn(credentials)
      if (session.role !== 'student') {
        setRoleError('This sign-in page is for student accounts. Please use the company sign-in page.')
        return
      }
      startSession(session)
      navigate('/student/dashboard', { replace: true })
    },
  })

  return (
    <main className="mx-auto mt-16 max-w-md rounded-2xl border border-gray-200 bg-white p-6 shadow-card">
      <p className="text-sm font-semibold text-brand-600">Student portal</p>
      <h1 className="mt-1 text-2xl font-bold tracking-tight text-gray-900">Welcome back</h1>
      <form className="mt-6" onSubmit={handleSubmit} noValidate>
        <FormField label="Email" name="email" type="email" value={values.email} onChange={handleChange} onBlur={handleBlur} error={errors.email} />
        <FormField label="Password" name="password" type="password" value={values.password} onChange={handleChange} onBlur={handleBlur} error={errors.password} />
        {(submitError || roleError) && <p className="mb-4 text-sm text-red-600">{submitError || roleError}</p>}
        <button type="submit" disabled={isSubmitting} className="h-10 w-full rounded-xl bg-brand-600 text-sm font-semibold text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50">
          {isSubmitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
      <p className="mt-5 text-center text-sm text-gray-600">
        New student?{' '}
        <Link to="/signup/student" className="font-medium text-brand-700 hover:text-brand-800">Create an account</Link>
      </p>
    </main>
  )
}
