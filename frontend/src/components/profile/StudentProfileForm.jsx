import FormField, { TextAreaField } from '../common/FormField'
import Button from '../ui/Button'
import { useForm } from '../../hooks/useForm'
import { composeValidators, isEmail, maxLength, minLength, required } from '../../utils/validators'

const optionalMax = (length) => maxLength(length)

export default function StudentProfileForm({ profile, onSave, onCancel }) {
  const { values, errors, isSubmitting, submitError, handleChange, handleBlur, handleSubmit } = useForm({
    initialValues: {
      name: profile.name || '',
      email: profile.email || '',
      college_name: profile.college_name || '',
      date_of_birth: profile.date_of_birth || '',
      city: profile.city || '',
      state: profile.state || '',
      country: profile.country || '',
      career_objective: profile.career_objective || '',
      degree: profile.degree || '',
      major: profile.major || '',
      graduation_year: profile.graduation_year ?? '',
      cgpa: profile.cgpa ?? '',
      experience: profile.experience || '',
      phone: profile.phone || '',
      skills: profile.skills || '',
    },
    validators: {
      name: composeValidators(required('Name is required'), maxLength(150)),
      email: composeValidators(required('Email is required'), isEmail()),
      college_name: composeValidators(required('College name is required'), maxLength(190)),
      city: optionalMax(100),
      state: optionalMax(100),
      country: optionalMax(100),
      career_objective: optionalMax(3000),
      degree: optionalMax(100),
      major: optionalMax(100),
      graduation_year: (value) => value && (!/^\d{4}$/.test(value) || Number(value) < 1900) ? 'Enter a four-digit year' : undefined,
      cgpa: (value) => value && (Number(value) < 0 || Number(value) > 9.99) ? 'Enter a value from 0 to 9.99' : undefined,
      experience: optionalMax(10000),
      phone: optionalMax(30),
      skills: optionalMax(2000),
    },
    onSubmit: (values) => onSave({
      ...values,
      date_of_birth: values.date_of_birth || null,
      graduation_year: values.graduation_year ? Number(values.graduation_year) : null,
      cgpa: values.cgpa === '' ? null : Number(values.cgpa),
    }),
  })

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="grid grid-cols-1 gap-x-4 sm:grid-cols-2">
        <FormField label="Full name" name="name" value={values.name} onChange={handleChange} onBlur={handleBlur} error={errors.name} />
        <FormField label="Email" name="email" type="email" value={values.email} onChange={handleChange} onBlur={handleBlur} error={errors.email} />
        <FormField label="College name" name="college_name" value={values.college_name} onChange={handleChange} onBlur={handleBlur} error={errors.college_name} />
        <FormField label="Date of birth" name="date_of_birth" type="date" value={values.date_of_birth} onChange={handleChange} onBlur={handleBlur} error={errors.date_of_birth} />
        <FormField label="City" name="city" value={values.city} onChange={handleChange} onBlur={handleBlur} error={errors.city} />
        <FormField label="State" name="state" value={values.state} onChange={handleChange} onBlur={handleBlur} error={errors.state} />
        <FormField label="Country" name="country" value={values.country} onChange={handleChange} onBlur={handleBlur} error={errors.country} />
        <FormField label="Phone" name="phone" type="tel" value={values.phone} onChange={handleChange} onBlur={handleBlur} error={errors.phone} />
      </div>

      <div className="grid grid-cols-1 gap-x-4 sm:grid-cols-2">
        <FormField label="Degree" name="degree" value={values.degree} onChange={handleChange} onBlur={handleBlur} error={errors.degree} />
        <FormField label="Major" name="major" value={values.major} onChange={handleChange} onBlur={handleBlur} error={errors.major} />
        <FormField label="Graduation year" name="graduation_year" type="number" min="1900" max="9999" value={values.graduation_year} onChange={handleChange} onBlur={handleBlur} error={errors.graduation_year} />
        <FormField label="CGPA" name="cgpa" type="number" min="0" max="9.99" step="0.01" value={values.cgpa} onChange={handleChange} onBlur={handleBlur} error={errors.cgpa} />
      </div>

      <TextAreaField label="Career objective" name="career_objective" rows={3} value={values.career_objective} onChange={handleChange} onBlur={handleBlur} error={errors.career_objective} />
      <TextAreaField label="Experience" name="experience" rows={4} value={values.experience} onChange={handleChange} onBlur={handleBlur} error={errors.experience} />
      <TextAreaField label="Skills" name="skills" rows={3} value={values.skills} onChange={handleChange} onBlur={handleBlur} error={errors.skills} hint="Separate skills with commas." />

      {submitError && <p className="mb-3 text-sm text-red-600">{submitError}</p>}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>Cancel</Button>
        <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Saving…' : 'Save changes'}</Button>
      </div>
    </form>
  )
}
