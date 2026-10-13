import { Link, useNavigate, useOutletContext } from 'react-router-dom'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import PageHeader from '../../components/ui/PageHeader'
import FormField, { SelectField, TextAreaField } from '../../components/common/FormField'
import { useForm } from '../../hooks/useForm'
import { usePermissions } from '../../hooks/usePermissions'
import NoAccess from '../../components/common/NoAccess'
import { createJob } from '../../services/jobService'
import { JOB_CATEGORIES } from '../../utils/constants'
import { todayISO } from '../../utils/format'
import { composeValidators, maxLength, minLength, required } from '../../utils/validators'

function Section({ title, children }) {
  return (
    <div className="border-t border-gray-100 px-6 py-5 first:border-t-0">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">{title}</h2>
      {children}
    </div>
  )
}

const nonNegative = (value) => (value !== '' && Number(value) < 0 ? 'Salary cannot be negative' : undefined)

export default function PostJob() {
  const navigate = useNavigate()
  const { reloadCompany } = useOutletContext()
  const { can, loaded, member } = usePermissions()

  const { values, errors, isSubmitting, submitError, handleChange, handleBlur, handleSubmit } = useForm({
    initialValues: {
      title: '',
      description: '',
      category: JOB_CATEGORIES[0].value,
      city: '',
      location: '',
      is_remote: false,
      salary: '',
      skills_required: '',
      posting_date: todayISO(),
      deadline: '',
    },
    validators: {
      title: composeValidators(required('Job title is required'), minLength(2), maxLength(190)),
      city: composeValidators(required('City is required'), maxLength(100)),
      location: maxLength(190),
      salary: nonNegative,
      posting_date: required('Posting date is required'),
      deadline: (value) =>
        !value
          ? 'Deadline is required'
          : value < values.posting_date
            ? 'Deadline must be on or after the posting date'
            : undefined,
    },
    onSubmit: async (vals) => {
      const job = await createJob({ ...vals, salary: vals.salary === '' ? null : Number(vals.salary) })
      reloadCompany()
      navigate(`/company/jobs/${job.id}`)
    },
  })

  const setCheckbox = (name) => (event) => handleChange({ target: { name, value: event.target.checked } })

  if (loaded && !can('jobs:write')) {
    return (
      <div className="mx-auto max-w-2xl space-y-5">
        <PageHeader title="Post a job" backTo="/company/jobs" backLabel="Back to jobs" />
        <NoAccess roleLabel={member.role_label} action="post jobs" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <PageHeader title="Post a job" backTo="/company/jobs" backLabel="Back to jobs" />

      <form onSubmit={handleSubmit} noValidate>
        <Card className="overflow-hidden">
          <Section title="Basic information">
            <FormField
              label="Job title"
              name="title"
              value={values.title}
              onChange={handleChange}
              onBlur={handleBlur}
              error={errors.title}
            />
            <SelectField
              label="Category"
              name="category"
              value={values.category}
              onChange={handleChange}
              options={JOB_CATEGORIES}
            />
          </Section>

          <Section title="Location">
            <div className="grid grid-cols-1 gap-x-4 sm:grid-cols-2">
              <FormField
                label="City"
                name="city"
                value={values.city}
                onChange={handleChange}
                onBlur={handleBlur}
                error={errors.city}
              />
              <FormField
                label="Address or office (optional)"
                name="location"
                value={values.location}
                onChange={handleChange}
                onBlur={handleBlur}
                error={errors.location}
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={values.is_remote}
                onChange={setCheckbox('is_remote')}
                className="h-4 w-4 rounded border-gray-300 text-brand-600"
              />
              This is a remote position
            </label>
          </Section>

          <Section title="Role details">
            <TextAreaField
              label="Description"
              name="description"
              rows={5}
              value={values.description}
              onChange={handleChange}
              hint="Responsibilities, team, and what success looks like."
            />
            <FormField
              label="Required skills (optional)"
              name="skills_required"
              value={values.skills_required}
              onChange={handleChange}
              hint="Comma-separated, e.g. Python, SQL, React"
            />
          </Section>

          <Section title="Compensation & dates">
            <FormField
              label="Salary or hourly rate in USD (optional)"
              name="salary"
              type="number"
              min="0"
              step="0.01"
              value={values.salary}
              onChange={handleChange}
              onBlur={handleBlur}
              error={errors.salary}
            />
            <div className="grid grid-cols-1 gap-x-4 sm:grid-cols-2">
              <FormField
                label="Posting date"
                name="posting_date"
                type="date"
                value={values.posting_date}
                onChange={handleChange}
                onBlur={handleBlur}
                error={errors.posting_date}
              />
              <FormField
                label="Application deadline"
                name="deadline"
                type="date"
                min={values.posting_date}
                value={values.deadline}
                onChange={handleChange}
                onBlur={handleBlur}
                error={errors.deadline}
              />
            </div>
          </Section>

          <div className="flex flex-wrap items-center justify-end gap-3 border-t border-gray-100 bg-gray-50/60 px-6 py-4">
            {submitError && (
              <p className="mr-auto text-sm text-red-600" role="alert">
                {submitError}
              </p>
            )}
            <Button as={Link} to="/company/jobs" variant="outline">
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Posting…' : 'Post job'}
            </Button>
          </div>
        </Card>
      </form>
    </div>
  )
}
