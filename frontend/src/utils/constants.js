export const JOB_CATEGORIES = [
  { value: 'full_time', label: 'Full-time' },
  { value: 'part_time', label: 'Part-time' },
  { value: 'on_campus', label: 'On-campus' },
  { value: 'internship', label: 'Internship' },
]

export function jobCategoryLabel(value) {
  return JOB_CATEGORIES.find((category) => category.value === value)?.label || value
}

export const APPLICATION_STATUSES = ['Pending', 'Reviewed', 'Declined']
