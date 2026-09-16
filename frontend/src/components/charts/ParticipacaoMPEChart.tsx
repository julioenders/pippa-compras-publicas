import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'

interface Props {
  title: string
  data: Array<{ periodo: string; percentual_mpe: number; meta?: number }>
}

const tooltipStyle = {
  backgroundColor: '#1a2332',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '8px',
}

export default function ParticipacaoMPEChart({ title, data }: Props) {
  return (
    <div className="rounded-xl border border-white/5 bg-obs-bg p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-300">{title}</h3>

      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="gradientMPE" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0080FF" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#0080FF" stopOpacity={0.05} />
            </linearGradient>
          </defs>

          <XAxis
            dataKey="periodo"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
          />
          <YAxis
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
            formatter={(value: number) => [`${value.toFixed(1)}%`, '% MPE']}
          />

          <ReferenceLine
            y={25}
            stroke="#e74c3c"
            strokeDasharray="6 4"
            label={{
              value: 'Meta 25%',
              fill: '#e74c3c',
              fontSize: 11,
              position: 'insideTopRight',
            }}
          />

          <Area
            type="monotone"
            dataKey="percentual_mpe"
            stroke="#0080FF"
            strokeWidth={2}
            fill="url(#gradientMPE)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
