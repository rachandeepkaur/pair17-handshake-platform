import { Link, useNavigate, useOutletContext } from 'react-router-dom'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import PageHeader from '../../components/ui/PageHeader'
import FormField, { TextAreaField } from '../../components/common/FormField'
import { useForm } from '../../hooks/useForm'
import { usePermissions } from '../../hooks/usePermissions'
import NoAccess from '../../components/common/NoAccess'
import { createEvent } from '../../services/eventService'
import { todayISO } from '../../utils/format'
import { composeValidators, maxLength, minLength, required } from '../../utils/validators'

export default function CreateEvent() {
  const navigate = useNavigate()
  const { reloadCompany } = useOutletContext()
  const { can, loaded, member } = usePermissions()
  const today = todayISO()

  const { values, errors, isSubmitting, submitError, handleChange, handleBlur, handleSubmit } = useForm({
    initialValues: { name: '', description: '', event_date: '', event_time: '', location: '', eligibility: '' },
    validators: {
      name: composeValidators(required('Event name is required'), minLength(2), maxLength(190)),
      event_date: (value) =>
        !value ? 'Event date is required' : value < today ? 'Event date cannot be in the past' : undefined,
      location: maxLength(190),
      eligibility: maxLength(255),
      description: maxLength(5000),
    },
    onSubmit: async (vals) => {
      const event = await createEvent({ ...vals, event_time: vals.event_time || null })
      reloadCompany()
      navigate(`/company/events/${event.id}`)
    },
  })

  if (loaded && !can('events:write')) {
    return (
      <div className="mx-auto max-w-2xl space-y-5">
        <PageHeader title="Create an event" backTo="/company/events" backLabel="Back to events" />
        <NoAccess roleLabel={member.role_label} action="create events" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <PageHeader title="Create an event" backTo="/company/events" backLabel="Back to events" />

      <form onSubmit={handleSubmit} noValidate>
        <Card className="p-6">
          <FormField
            label="Event name"
            name="name"
            value={values.name}
            onChange={handleChange}
            onBlur={handleBlur}
            error={errors.name}
          />
          <TextAreaField
            label="Description (optional)"
            name="description"
            value={values.description}
            onChange={handleChange}
            onBlur={handleBlur}
            error={errors.description}
            hint="Agenda, speakers, and what students will get out of it."
          />
          <div className="grid grid-cols-1 gap-x-4 sm:grid-cols-2">
            <FormField
              label="Date"
              name="event_date"
              type="date"
              min={today}
              value={values.event_date}
              onChange={handleChange}
              onBlur={handleBlur}
              error={errors.event_date}
            />
            <FormField
              label="Time (optional)"
              name="event_time"
              type="time"
              value={values.event_time}
              onChange={handleChange}
            />
          </div>
          <FormField
            label="Location (optional)"
            name="location"
            value={values.location}
            onChange={handleChange}
            onBlur={handleBlur}
            error={errors.location}
            hint="A venue, or “Virtual” with the meeting platform."
          />
          <FormField
            label="Eligibility (optional)"
            name="eligibility"
            value={values.eligibility}
            onChange={handleChange}
            onBlur={handleBlur}
            error={errors.eligibility}
            hint="Who can register, e.g. “Computer Science, Data Science” or “All majors”."
          />

          <div className="flex flex-wrap items-center justify-end gap-3 border-t border-gray-100 pt-4">
            {submitError && (
              <p className="mr-auto text-sm text-red-600" role="alert">
                {submitError}
              </p>
            )}
            <Button as={Link} to="/company/events" variant="outline">
              Cancel
            </Button>
            <Button type="submit" variant="secondary" disabled={isSubmitting}>
              {isSubmitting ? 'Creating…' : 'Create event'}
            </Button>
          </div>
        </Card>
      </form>
    </div>
  )
}
