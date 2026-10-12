export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-gray-300 bg-gray-50/50 px-6 py-10 text-center">
      {Icon && (
        <span className="mb-3 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
          <Icon size={22} strokeWidth={2} />
        </span>
      )}
      <p className="font-medium text-gray-900">{title}</p>
      {description && <p className="mt-1 max-w-sm text-sm text-gray-500">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
