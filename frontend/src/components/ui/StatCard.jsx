import Card from './Card'

const TONES = {
  brand: 'bg-brand-50 text-brand-600',
  accent: 'bg-accent-50 text-accent-600',
  amber: 'bg-amber-50 text-amber-600',
  violet: 'bg-violet-50 text-violet-600',
  cyan: 'bg-cyan-50 text-cyan-600',
  rose: 'bg-rose-50 text-rose-600',
}

export default function StatCard({ icon: Icon, label, value, delta, tone = 'brand' }) {
  return (
    <Card className="p-5 transition-shadow hover:shadow-card-hover">
      <div className="flex items-center justify-between">
        <span className={`inline-flex h-9 w-9 items-center justify-center rounded-xl ${TONES[tone]}`}>
          {Icon && <Icon size={18} strokeWidth={2} />}
        </span>
        {delta != null && (
          <span
            className={`text-xs font-medium ${delta >= 0 ? 'text-emerald-600' : 'text-red-600'}`}
          >
            {delta >= 0 ? '+' : ''}
            {delta}%
          </span>
        )}
      </div>
      <p className="mt-4 text-2xl font-semibold text-gray-900">{value}</p>
      <p className="mt-1 text-sm text-gray-500">{label}</p>
    </Card>
  )
}
