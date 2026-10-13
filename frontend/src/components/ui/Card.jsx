export default function Card({ className = '', children, ...props }) {
  return (
    <div
      className={`relative rounded-2xl border border-gray-200/80 bg-white shadow-card ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-gray-100 px-5 py-4">
      <div>
        <h3 className="font-semibold text-gray-900">{title}</h3>
        {subtitle && <p className="mt-0.5 text-sm text-gray-500">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}
