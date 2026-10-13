import { useState } from 'react'

// Generic form-state hook shared by every auth/profile form (company signup
// today, student signup and profile edits next) so field wiring and
// validation timing only has to be written once.
export function useForm({ initialValues, validators = {}, onSubmit }) {
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  const validateField = (name, value) => {
    const validate = validators[name]
    return validate ? validate(value) : undefined
  }

  const validateAll = () => {
    const nextErrors = {}
    Object.keys(validators).forEach((name) => {
      const error = validateField(name, values[name])
      if (error) nextErrors[name] = error
    })
    setErrors(nextErrors)
    return nextErrors
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setValues((prev) => ({ ...prev, [name]: value }))
    // Once a field shows an error, re-check it as the user types so the
    // error clears while they fix it. Otherwise it would only clear on blur;
    // blurring by clicking Submit removes the message, shifts the layout,
    // and the click lands where the button used to be.
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: validateField(name, value) }))
    }
  }

  const handleBlur = (event) => {
    const { name, value } = event.target
    setErrors((prev) => ({ ...prev, [name]: validateField(name, value) }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSubmitError('')

    const nextErrors = validateAll()
    if (Object.values(nextErrors).some(Boolean)) return

    setIsSubmitting(true)
    try {
      await onSubmit(values)
    } catch (error) {
      setSubmitError(error?.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return { values, errors, isSubmitting, submitError, handleChange, handleBlur, handleSubmit }
}
