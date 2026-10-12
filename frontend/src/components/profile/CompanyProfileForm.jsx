import FormField, { TextAreaField } from '../common/FormField'
import Button from '../ui/Button'
import { useForm } from '../../hooks/useForm'
import { composeValidators, maxLength, minLength, required } from '../../utils/validators'

export default function CompanyProfileForm({ profile, onSave, onCancel }) {
  const { values, errors, isSubmitting, submitError, handleChange, handleBlur, handleSubmit } = useForm({
    initialValues: {
      company_name: profile.company_name,
      location: profile.location,
      description: profile.description || '',
      contact_info: profile.contact_info || '',
    },
    validators: {
      company_name: composeValidators(required('Company name is required'), minLength(2), maxLength(190)),
      location: composeValidators(required('Location is required'), minLength(2), maxLength(190)),
      description: maxLength(5000),
      contact_info: maxLength(255),
    },
    onSubmit: onSave,
  })

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="grid grid-cols-1 gap-x-4 sm:grid-cols-2">
        <FormField
          label="Company name"
          name="company_name"
          value={values.company_name}
          onChange={handleChange}
          onBlur={handleBlur}
          error={errors.company_name}
        />
        <FormField
          label="Location"
          name="location"
          value={values.location}
          onChange={handleChange}
          onBlur={handleBlur}
          error={errors.location}
        />
      </div>
      <FormField
        label="Contact information"
        name="contact_info"
        value={values.contact_info}
        onChange={handleChange}
        onBlur={handleBlur}
        error={errors.contact_info}
        hint="Recruiting email, phone, or website shown to students."
      />
      <TextAreaField
        label="Description"
        name="description"
        rows={6}
        value={values.description}
        onChange={handleChange}
        onBlur={handleBlur}
        error={errors.description}
        hint="What you do, your culture, and why students should join."
      />

      {submitError && <p className="mb-3 text-sm text-red-600">{submitError}</p>}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : 'Save changes'}
        </Button>
      </div>
    </form>
  )
}
