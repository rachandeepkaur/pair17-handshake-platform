import { useNavigate } from 'react-router-dom'
import FormField from '../../components/common/FormField'
import { useForm } from '../../hooks/useForm'
import { createJob } from '../../services/jobService'
import { JOB_CATEGORIES } from '../../utils/constants'
import { required } from '../../utils/validators'

export default function PostJob() {
  const navigate = useNavigate()

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
      deadline: '',
    },
    validators: {
      title: required('Title is required'),
      city: required('City is required'),
      deadline: required('Deadline is required'),
    },
    onSubmit: async (vals) => {
      await createJob({
        ...vals,
        salary: vals.salary === '' ? null : Number(vals.salary),
      })
      navigate('/company/jobs')
    },
  })

  const setCheckbox = (name) => (event) =>
    handleChange({ target: { name, value: event.target.checked } })

  return (
    <div className="mx-auto mt-10 max-w-xl rounded-lg border p-6 shadow-sm">
      <h1 className="mb-6 text-xl font-semibold">Post a job</h1>
      <form onSubmit={handleSubmit} noValidate>
        <FormField
          label="Title"
          name="title"
          value={values.title}
          onChange={handleChange}
          onBlur={handleBlur}
          error={errors.title}
        />

        <div className="mb-4">
          <label htmlFor="category" className="mb-1 block text-sm font-medium text-gray-700">
            Category
          </label>
          <select
            id="category"
            name="category"
            value={values.category}
            onChange={handleChange}
            onBlur={handleBlur}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {JOB_CATEGORIES.map((category) => (
              <option key={category.value} value={category.value}>
                {category.label}
              </option>
            ))}
          </select>
        </div>

        <FormField
          label="City"
          name="city"
          value={values.city}
          onChange={handleChange}
          onBlur={handleBlur}
          error={errors.city}
        />
        <FormField
          label="Location (optional)"
          name="location"
          value={values.location}
          onChange={handleChange}
          onBlur={handleBlur}
          error={errors.location}
        />

        <div className="mb-4 flex items-center gap-2">
          <input
            id="is_remote"
            type="checkbox"
            checked={values.is_remote}
            onChange={setCheckbox('is_remote')}
          />
          <label htmlFor="is_remote" className="text-sm text-gray-700">
            This is a remote position
          </label>
        </div>

        <FormField
          label="Salary (optional)"
          name="salary"
          type="number"
          value={values.salary}
          onChange={handleChange}
          onBlur={handleBlur}
          error={errors.salary}
        />
        <FormField
          label="Deadline"
          name="deadline"
          type="date"
          value={values.deadline}
          onChange={handleChange}
          onBlur={handleBlur}
          error={errors.deadline}
        />

        <div className="mb-4">
          <label htmlFor="description" className="mb-1 block text-sm font-medium text-gray-700">
            Description (optional)
          </label>
          <textarea
            id="description"
            name="description"
            rows={4}
            value={values.description}
            onChange={handleChange}
            onBlur={handleBlur}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <FormField
          label="Skills, comma-separated (optional)"
          name="skills_required"
          value={values.skills_required}
          onChange={handleChange}
          onBlur={handleBlur}
          error={errors.skills_required}
        />

        {submitError && <p className="mb-4 text-sm text-red-600">{submitError}</p>}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-md bg-blue-600 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {isSubmitting ? 'Posting...' : 'Post job'}
        </button>
      </form>
    </div>
  )
}
