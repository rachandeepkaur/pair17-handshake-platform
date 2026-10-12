import { splitSkills } from '../../utils/format'

export default function SkillTags({ skills, max }) {
  const all = splitSkills(skills)
  if (all.length === 0) return <span className="text-sm text-gray-400">No skills listed</span>

  const shown = max ? all.slice(0, max) : all
  return (
    <div className="flex flex-wrap gap-1.5">
      {shown.map((skill) => (
        <span key={skill} className="rounded-lg bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">
          {skill}
        </span>
      ))}
      {all.length > shown.length && (
        <span className="px-1 py-0.5 text-xs text-gray-500">+{all.length - shown.length} more</span>
      )}
    </div>
  )
}
