import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface DataPoint {
  cnae_divisao: string
  cnae_descricao?: string | null
  qtd_contratacoes: number
  qtd_mpes_regiao: number
  sinal: string
}

interface Props {
  title: string
  data: DataPoint[]
}

const tooltipStyle = {
  backgroundColor: '#1a2332',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '8px',
}

const sinalColors: Record<string, string> = {
  oportunidade: '#2ecc71',
  competitivo: '#f39c12',
  cautela: '#e67e22',
  saturado: '#e74c3c',
  deserto: '#95a5a6',
}

const sinalLabels: Record<string, string> = {
  oportunidade: 'Oportunidade',
  competitivo: 'Competitivo',
  cautela: 'Cautela',
  saturado: 'Saturado',
  deserto: 'Deserto',
}

const compactFmt = new Intl.NumberFormat('pt-BR', {
  notation: 'compact',
  maximumFractionDigits: 1,
})

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: DataPoint }> }) {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload
  if (!d) return null
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs"
      style={{
        backgroundColor: '#1a2332',
        border: '1px solid rgba(255,255,255,0.1)',
      }}
    >
      <p className="mb-1 font-medium text-gray-200">
        {d.cnae_descricao ?? d.cnae_divisao}
      </p>
      <p className="text-gray-400">
        Demanda: {compactFmt.format(d.qtd_contratacoes)}
      </p>
      <p className="text-gray-400">
        Oferta MPE: {compactFmt.format(d.qtd_mpes_regiao)}
      </p>
      <p style={{ color: sinalColors[d.sinal] ?? '#9ca3af' }}>
        {sinalLabels[d.sinal] ?? d.sinal}
      </p>
    </div>
  )
}

export default function CruzamentoScatter({ title, data }: Props) {
  const sinais = [...new Set(data.map((d) => d.sinal))]

  return (
    <div className="rounded-xl border border-white/5 bg-obs-bg p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-300">{title}</h3>

      <ResponsiveContainer width="100%" height={320}>
        <ScatterChart margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <XAxis
            type="number"
            dataKey="qtd_contratacoes"
            name="Demanda"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
            tickFormatter={(v: number) => compactFmt.format(v)}
            label={{
              value: 'Demanda',
              position: 'insideBottom',
              offset: -2,
              fill: '#6b7280',
              fontSize: 11,
            }}
          />
          <YAxis
            type="number"
            dataKey="qtd_mpes_regiao"
            name="Oferta MPE"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
            tickFormatter={(v: number) => compactFmt.format(v)}
            label={{
              value: 'Oferta MPE',
              angle: -90,
              position: 'insideLeft',
              offset: 10,
              fill: '#6b7280',
              fontSize: 11,
            }}
          />

          <Tooltip
            content={<CustomTooltip />}
            contentStyle={tooltipStyle}
            cursor={{ strokeDasharray: '3 3', stroke: '#374151' }}
          />

          <Scatter data={data}>
            {data.map((entry, idx) => (
              <Cell
                key={idx}
                fill={sinalColors[entry.sinal] ?? '#9ca3af'}
                fillOpacity={0.85}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      <div className="mt-2 flex flex-wrap gap-3">
        {sinais.map((s) => (
          <span key={s} className="flex items-center gap-1.5 text-xs text-gray-400">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: sinalColors[s] ?? '#9ca3af' }}
            />
            {sinalLabels[s] ?? s}
          </span>
        ))}
      </div>
    </div>
  )
}
