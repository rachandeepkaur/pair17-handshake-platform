export const required = (message = 'This field is required') => (value) =>
  value === undefined || value === null || String(value).trim() === '' ? message : undefined

export const isEmail = (message = 'Enter a valid email address') => (value) =>
  value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? message : undefined

export const minLength = (length, message) => (value) =>
  value && value.length < length ? message || `Must be at least ${length} characters` : undefined

export const composeValidators =
  (...validators) =>
  (value) =>
    validators.reduce((error, validator) => error || validator(value), undefined)

export const maxLength = (length, message) => (value) =>
  value && String(value).length > length ? message || `Must be ${length} characters or fewer` : undefined
