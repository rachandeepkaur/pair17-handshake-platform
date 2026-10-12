import Card from '../ui/Card'

// Placeholder for portal sections whose backend isn't built yet. Lists the
// planned capabilities so the section reads as intentional, not broken.
export default function ComingSoon({ icon: Icon, title, description, features = [] }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        {description && <p className="mt-0.5 text-sm text-gray-500">{description}</p>}
      </div>

      <Card className="overflow-hidden">
        <div className="flex flex-col items-center bg-gradient-to-br from-brand-50 to-accent-50/40 px-6 py-12 text-center">
          <span className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-brand-600 shadow-card">
            {Icon && <Icon size={26} strokeWidth={2} />}
          </span>
          <span className="mt-4 rounded-full bg-brand-600/10 px-3 py-1 text-xs font-semibold text-brand-700">
            Coming soon
          </span>
          <p className="mt-3 max-w-md text-sm text-gray-600">
            This section is designed and planned. The interface will light up once its backend
            services are connected.
          </p>
        </div>

        {features.length > 0 && (
          <div className="grid grid-cols-1 gap-px bg-gray-100 sm:grid-cols-2">
            {features.map((feature) => (
              <div key={feature} className="bg-white px-5 py-4 text-sm text-gray-700">
                {feature}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
