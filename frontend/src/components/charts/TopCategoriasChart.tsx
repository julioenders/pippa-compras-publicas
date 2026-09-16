import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface Props {
  title: string
  data: Array<{ grupo_catmat: string; valor_total: number; qtd_itens: number }>
}

const tooltipStyle = {
  backgroundColor: '#1a2332',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '8px',
}

const currencyFmt = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  notation: 'compact',
  maximumFractionDigits: 1,
})

const currencyFmtFull = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
})

const numberFmt = new Intl.NumberFormat('pt-BR')

function truncate(text: string, max: number) {
  return text.length > max ? `${text.slice(0, max)}...` : text
}

export default function TopCategoriasChart({ title, data }: Props) {
  const chartHeight = Math.max(200, data.length * 40)

  return (
    <div className="rounded-xl border border-white/5 bg-obs-bg p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-300">{title}</h3>

      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 0, right: 16, bottom: 0, left: 8 }}
        >
          <XAxis
            type="number"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
            tickFormatter={(v: number) => currencyFmt.format(v)}
          />
          <YAxis
            type="category"
            dataKey="grupo_catmat"
            width={140}
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
            tickFormatter={(v: string) => truncate(v, 22)}
          />

          <Tooltip
            contentStyle={tooltipStyle}
            labelStyle={{ color: '#e5e7eb' }}
            itemStyle={{ color: '#9ca3af' }}
            formatter={(_: unknown, __: unknown, entry: { payload?: Props['data'][number] }) => {
              const d = entry.payload
              if (!d) return [String(_), 'Valor']
              return [
                `${currencyFmtFull.format(d.valor_total)} | ${numberFmt.format(d.qtd_itens)} itens`,
                'Valor',
              ]
            }}
          />

          <Bar dataKey="valor_total" fill="#0080FF" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
