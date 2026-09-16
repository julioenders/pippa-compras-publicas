import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'

interface Props {
  title?: string
  data: Array<{
    uf: string
    percentual_mpe: number
    total_contratacoes: number
    valor_total: number
  }>
}

const TOOLTIP_STYLE = {
  backgroundColor: '#1a2332',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '8px',
}

function formatCompact(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    notation: 'compact',
    compactDisplay: 'short',
    maximumFractionDigits: 1,
  }).format(value)
}

export default function ComparativoUFsChart({ title, data }: Props) {
  const sorted = [...data]
    .sort((a, b) => b.percentual_mpe - a.percentual_mpe)
    .slice(0, 15)

  return (
    <div className="rounded-xl border border-white/5 bg-obs-bg p-4">
      {title && (
        <h3 className="mb-3 text-sm font-medium text-gray-400">{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={sorted} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
          <XAxis
            dataKey="uf"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
            tickFormatter={(v: number) => `${v}%`}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            labelStyle={{ color: '#e5e7eb' }}
            formatter={(value: number, name: string) => {
              if (name === 'percentual_mpe') return [`${value.toFixed(1)}%`, '% MPE']
              return [formatCompact(value), name]
            }}
          />
          <ReferenceLine
            y={25}
            stroke="#e74c3c"
            strokeDasharray="4 4"
            label={{ value: 'Meta 25%', fill: '#e74c3c', fontSize: 10, position: 'right' }}
          />
          <Bar
            dataKey="percentual_mpe"
            fill="#0080FF"
            radius={[4, 4, 0, 0]}
            maxBarSize={30}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
