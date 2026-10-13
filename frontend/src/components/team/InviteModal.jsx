import { useState } from 'react'
import Modal from '../common/Modal'
import Button from '../ui/Button'
import FormField, { SelectField } from '../common/FormField'
import InviteLinkPanel from './InviteLinkPanel'
import { useForm } from '../../hooks/useForm'
import { createInvitation } from '../../services/teamService'
import { composeValidators, isEmail, maxLength, required } from '../../utils/validators'

export default function InviteModal({ open, onClose, roles, onInvited }) {
  const [created, setCreated] = useState(null)
  const invitable = roles.filter((role) => role.key !== 'owner')

  const { values, errors, isSubmitting, submitError, handleChange, handleBlur, handleSubmit } = useForm({
    initialValues: { name: '', email: '', role: 'recruiter' },
    validators: {
      name: composeValidators(required('Name is required'), maxLength(150)),
      email: composeValidators(required('Email is required'), isEmail(), maxLength(190)),
    },
    onSubmit: async (vals) => {
      const invitation = await createInvitation(vals)
      setCreated(invitation)
      onInvited()
    },
  })

  const close = () => {
    setCreated(null)
    onClose()
  }

  const selected = invitable.find((role) => role.key === values.role)

  return (
    <Modal
      open={open}
      onClose={close}
      title={created ? 'Invitation created' : 'Invite a teammate'}
      footer={
        created ? (
          <Button onClick={close}>Done</Button>
        ) : (
          <>
            <Button variant="outline" onClick={close} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" form="invite-form" disabled={isSubmitting}>
              {isSubmitting ? 'Creating…' : 'Create invite link'}
            </Button>
          </>
        )
      }
    >
      {created ? (
        <InviteLinkPanel invitation={created} />
      ) : (
        <form id="invite-form" onSubmit={handleSubmit} noValidate className="mt-2">
          <FormField label="Name" name="name" value={values.name} onChange={handleChange} onBlur={handleBlur} error={errors.name} />
          <FormField
            label="Work email"
            name="email"
            type="email"
            value={values.email}
            onChange={handleChange}
            onBlur={handleBlur}
            error={errors.email}
          />
          <SelectField
            label="Role"
            name="role"
            value={values.role}
            onChange={handleChange}
            options={invitable.map((role) => ({ value: role.key, label: role.label }))}
            hint={selected?.description}
          />
          {submitError && (
            <p className="text-sm text-red-600" role="alert">
              {submitError}
            </p>
          )}
        </form>
      )}
    </Modal>
  )
}
