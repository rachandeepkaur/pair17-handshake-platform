// Quick-insert templates for the company inbox. Placeholders are filled from
// the open conversation so recruiters only tweak, never retype.
const firstName = (name = '') => name.split(' ')[0] || 'there'

export const MESSAGE_TEMPLATES = [
  {
    id: 'thanks',
    label: 'Thanks for applying',
    build: ({ student, company }) =>
      `Hi ${firstName(student.name)}, thanks for applying to ${company}! We're reviewing your application and will follow up soon.`,
  },
  {
    id: 'chat',
    label: 'Schedule a chat',
    build: ({ student }) =>
      `Hi ${firstName(student.name)}, we'd love to set up a quick call to learn more about you. What times work for you this week?`,
  },
  {
    id: 'documents',
    label: 'Request documents',
    build: ({ student }) =>
      `Hi ${firstName(student.name)}, could you send us an updated resume and any portfolio or project links? Thank you!`,
  },
  {
    id: 'update',
    label: 'Application update',
    build: ({ student, company }) =>
      `Hi ${firstName(student.name)}, thank you for your interest in ${company}. We wanted to give you a quick update on your application.`,
  },
]

export const inviteToApplyText = ({ student, job }) =>
  `Hi ${firstName(student.name)}, we think you'd be a great fit for our ${job.title} role. We'd love for you to apply!`

export const inviteToEventText = ({ student, event, date }) =>
  `Hi ${firstName(student.name)}, we're hosting ${event.name} on ${date} and would love to see you there.`
