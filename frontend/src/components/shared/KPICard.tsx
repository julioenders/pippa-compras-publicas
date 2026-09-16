import { TrendingUp, TrendingDown } from 'lucide-react'

interface KPICardProps {
  title: string
  value: string | number
  subtitle?: string
  trend?: number
  color?: string
}

export default function KPICard({
  title,
  value,
  subtitle,
  trend,
  color,
}: KPICardProps) {
  return (
    <div
      className="rounded-xl border border-white/5 p-5"
      style={{ backgroundColor: '#1a2332' }}
    >
      <p className="text-xs font-medium uppercase tracking-wider text-gray-400">
        {title}
      </p>

      <p
        className="mt-2 text-2xl font-bold"
        style={{ color: color ?? '#ffffff' }}
      >
        {value}
      </p>

      <div className="mt-2 flex items-center gap-2">
        {trend !== undefined && trend !== 0 && (
          <span
            className={`inline-flex items-center gap-0.5 text-xs font-medium ${
              trend > 0 ? 'text-signal-green' : 'text-signal-red'
            }`}
          >
            {trend > 0 ? (
              <TrendingUp size={14} />
            ) : (
              <TrendingDown size={14} />
            )}
            {Math.abs(trend)}%
          </span>
        )}

        {subtitle && (
          <span className="text-xs text-gray-500">{subtitle}</span>
        )}
      </div>
    </div>
  )
}
