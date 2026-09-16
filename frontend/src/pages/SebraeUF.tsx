import { useParams, useNavigate } from 'react-router-dom'
import KPICard from '../components/shared/KPICard'
import CruzamentoScatter from '../components/charts/CruzamentoScatter'
import { UFS } from '../lib/constants'

const kpis = [
  {
    title: 'Oportunidades',
    value: '342',
    trend: 18,
    subtitle: 'abertas agora',
    color: '#2ecc71',
  },
  {
    title: 'Valor Total UF',
    value: 'R$ 180M',
    trend: 9,
    subtitle: 'ultimos 12 meses',
    color: '#0080FF',
  },
  {
    title: 'Desertos UF',
    value: '12',
    trend: -4,
    subtitle: 'municipios sem fornecedor',
    color: '#e74c3c',
  },
  {
    title: 'Alertas',
    value: '8',
    subtitle: 'novas oportunidades hoje',
    color: '#f39c12',
  },
]

const mockRadar = [
  { cnae_divisao: '62', cnae_descricao: 'Servicos de TI', demanda: 85, valor_medio: 45000, qtd_mpes: 12, sinal: 'oportunidade' as const },
  { cnae_divisao: '43', cnae_descricao: 'Construcao', demanda: 42, valor_medio: 120000, qtd_mpes: 8, sinal: 'oportunidade' as const },
  { cnae_divisao: '10', cnae_descricao: 'Alimenticios', demanda: 67, valor_medio: 22000, qtd_mpes: 35, sinal: 'competitivo' as const },
  { cnae_divisao: '47', cnae_descricao: 'Comercio varejista', demanda: 95, valor_medio: 18000, qtd_mpes: 60, sinal: 'competitivo' as const },
  { cnae_divisao: '26', cnae_descricao: 'Equip. informatica', demanda: 15, valor_medio: 85000, qtd_mpes: 2, sinal: 'deserto' as const },
  { cnae_divisao: '33', cnae_descricao: 'Manutencao', demanda: 28, valor_medio: 55000, qtd_mpes: 3, sinal: 'cautela' as const },
]

const SINAL_COLORS: Record<string, string> = {
  oportunidade: '#2ecc71',
  competitivo: '#f39c12',
  cautela: '#e67e22',
  saturado: '#e74c3c',
  deserto: '#95a5a6',
}

const SINAL_LABELS: Record<string, string> = {
  oportunidade: 'Oportunidade',
  competitivo: 'Competitivo',
  cautela: 'Atencao',
  saturado: 'Saturado',
  deserto: 'Deserto',
}

const mockScatter = mockRadar.map((r) => ({
  cnae_divisao: r.cnae_divisao,
  cnae_descricao: r.cnae_descricao,
  qtd_contratacoes: r.demanda,
  qtd_mpes_regiao: r.qtd_mpes,
  sinal: r.sinal,
}))

export default function SebraeUF() {
  const { uf } = useParams<{ uf: string }>()
  const navigate = useNavigate()
  const currentUF = uf?.toUpperCase() || 'SP'

  function handleUFChange(e: React.ChangeEvent<HTMLSelectElement>) {
    navigate(`/sebrae-uf/${e.target.value}`)
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold text-white">
          Radar de Oportunidades —{' '}
          <span className="text-obs-blue-light">{currentUF}</span>
        </h1>
        <select
          value={currentUF}
          onChange={handleUFChange}
          className="w-full rounded-lg border border-white/10 bg-obs-bg px-4 py-2 text-sm text-gray-300 outline-none focus:border-obs-blue sm:w-auto"
        >
          {UFS.map((sigla) => (
            <option key={sigla} value={sigla}>
              {sigla}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi) => (
          <KPICard
            key={kpi.title}
            title={kpi.title}
            value={kpi.value}
            trend={kpi.trend}
            subtitle={kpi.subtitle}
            color={kpi.color}
          />
        ))}
      </div>

      <div className="rounded-xl border border-white/5 bg-obs-bg p-4">
        <h3 className="mb-3 text-sm font-medium text-gray-400">
          Oportunidades por CNAE em {currentUF}
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-white/10 text-xs uppercase text-gray-500">
                <th className="px-3 py-2">CNAE</th>
                <th className="px-3 py-2">Descricao</th>
                <th className="px-3 py-2 text-right">Demanda/mes</th>
                <th className="px-3 py-2 text-right">MPEs ativas</th>
                <th className="px-3 py-2 text-center">Sinal</th>
              </tr>
            </thead>
            <tbody>
              {mockRadar.map((row) => (
                <tr
                  key={row.cnae_divisao}
                  className="border-b border-white/5 transition-colors hover:bg-white/5"
                >
                  <td className="px-3 py-3 font-mono text-gray-300">
                    {row.cnae_divisao}
                  </td>
                  <td className="px-3 py-3 text-gray-300">
                    {row.cnae_descricao}
                  </td>
                  <td className="px-3 py-3 text-right text-gray-300">
                    {row.demanda}
                  </td>
                  <td className="px-3 py-3 text-right text-gray-300">
                    {row.qtd_mpes}
                  </td>
                  <td className="px-3 py-3 text-center">
                    <span
                      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium"
                      style={{
                        backgroundColor: `${SINAL_COLORS[row.sinal]}18`,
                        color: SINAL_COLORS[row.sinal],
                      }}
                    >
                      <span
                        className="inline-block h-2 w-2 rounded-full"
                        style={{ backgroundColor: SINAL_COLORS[row.sinal] }}
                      />
                      {SINAL_LABELS[row.sinal]}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <CruzamentoScatter
        title={`Cruzamento oferta x demanda — ${currentUF}`}
        data={mockScatter}
      />
    </div>
  )
}
