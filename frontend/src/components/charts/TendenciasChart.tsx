import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface Props {
  title: string
  data: Array<{ periodo: string; total_contratos: number; percentual_mpe: number }>
}

const tooltipStyle = {
  backgroundColor: '#1a2332',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '8px',
}

const compactFmt = new Intl.NumberFormat('pt-BR', {
  notation: 'compact',
  maximumFractionDigits: 1,
})

export default function TendenciasChart({ title, data }: Props) {
  return (
    <div className="rounded-xl border border-white/5 bg-obs-bg p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-300">{title}</h3>

      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <XAxis
            dataKey="periodo"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
          />
          <YAxis
            yAxisId="left"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
            tickFormatter={(v: number) => compactFmt.format(v)}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
            tickFormatter={(v: number) => `${v}%`}
            domain={[0, 'auto']}
          />

          <Tooltip
            contentStyle={tooltipStyle}
            labelStyle={{ color: '#e5e7eb' }}
            itemStyle={{ color: '#9ca3af' }}
            formatter={(value: number, name: string) => {
              if (name === 'total_contratos') return [compactFmt.format(value), 'Total Contratos']
              return [`${value.toFixed(1)}%`, '% MPE']
            }}
          />

          <Legend
            verticalAlign="bottom"
            wrapperStyle={{ paddingTop: 12, color: '#9ca3af', fontSize: 12 }}
            formatter={(value: string) =>
              value === 'total_contratos' ? 'Total Contratos' : '% MPE'
            }
          />

          <Bar
            yAxisId="left"
            dataKey="total_contratos"
            fill="#0080FF"
            opacity={0.6}
            radius={[4, 4, 0, 0]}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="percentual_mpe"
            stroke="#2ecc71"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
