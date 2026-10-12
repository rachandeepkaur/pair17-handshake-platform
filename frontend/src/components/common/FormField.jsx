const inputClass = (error) =>
  `w-full rounded-xl border px-3 text-sm transition-colors focus:border-brand-400 ${
    error ? 'border-red-400' : 'border-gray-300'
  }`

function FieldShell({ label, name, error, hint, children }) {
  return (
    <div className="mb-4">
      <label htmlFor={name} className="mb-1 block text-sm font-medium text-gray-700">
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${name}-error`} className="mt-1 text-sm text-red-600">
          {error}
        </p>
      ) : (
        hint && <p className="mt-1 text-xs text-gray-500">{hint}</p>
      )}
    </div>
  )
}

export default function FormField({ label, name, type = 'text', value, onChange, onBlur, error, hint, ...rest }) {
  return (
    <FieldShell label={label} name={name} error={error} hint={hint}>
      <input
        id={name}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${name}-error` : undefined}
        className={`h-10 ${inputClass(error)}`}
        {...rest}
      />
    </FieldShell>
  )
}

export function TextAreaField({ label, name, value, onChange, onBlur, error, hint, rows = 4, ...rest }) {
  return (
    <FieldShell label={label} name={name} error={error} hint={hint}>
      <textarea
        id={name}
        name={name}
        rows={rows}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${name}-error` : undefined}
        className={`py-2 ${inputClass(error)}`}
        {...rest}
      />
    </FieldShell>
  )
}

export function SelectField({ label, name, value, onChange, onBlur, error, hint, options, ...rest }) {
  return (
    <FieldShell label={label} name={name} error={error} hint={hint}>
      <select
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        className={`h-10 bg-white ${inputClass(error)}`}
        {...rest}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </FieldShell>
  )
}
