import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import KPICard from '../components/shared/KPICard'
import CruzamentoScatter from '../components/charts/CruzamentoScatter'
import { UFS } from '../lib/constants'
import { api } from '../api/client'

interface UFDash {
  uf: string
  oportunidades_abertas: number
  valor_total_estimado: number
  desertos_fornecimento: number
  alertas_nao_lidos: number
  participacao_mpe_percentual: number
}

interface RadarItem {
  id: number
  orgao: string
  objeto: string
  valor_estimado: number
  exclusiva_mpe: boolean
  data_encerramento: string | null
  modalidade: string
  sinal: string
  sinal_descricao: string
  score: number
  cnae_divisao: string
  cnae_descricao: string
  qtd_mpes_regiao: number
}

interface CruzamentoItem {
  cnae_divisao: string
  cnae_descricao: string
  qtd_contratacoes: number
  valor_total_demanda: number
  qtd_mpes_regiao: number
  sinal: string
  sinal_descricao: string
}

const SINAL_COLORS: Record<string, string> = {
  oportunidade: 'bg-green-500',
  competitivo: 'bg-yellow-500',
  cautela: 'bg-orange-500',
  saturado: 'bg-red-500',
  deserto: 'bg-gray-500',
}

const SINAL_LABELS: Record<string, string> = {
  oportunidade: 'Oportunidade',
  competitivo: 'Competitivo',
  cautela: 'Cautela',
  saturado: 'Saturado',
  deserto: 'Deserto',
}

function fmtVal(v: number) {
  if (v >= 1e9) return `R$ ${(v / 1e9).toFixed(1)}B`
  if (v >= 1e6) return `R$ ${(v / 1e6).toFixed(1)}M`
  if (v >= 1e3) return `R$ ${(v / 1e3).toFixed(1)}mil`
  return `R$ ${v.toFixed(0)}`
}

export default function SebraeUF() {
  const { uf } = useParams<{ uf: string }>()
  const navigate = useNavigate()
  const currentUF = uf?.toUpperCase() || 'AM'

  const [dash, setDash] = useState<UFDash | null>(null)
  const [radar, setRadar] = useState<RadarItem[]>([])
  const [cruzamento, setCruzamento] = useState<CruzamentoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([
      api.get<UFDash>(`/api/v1/sebrae-uf/${currentUF}/dashboard`),
      api.get<RadarItem[]>(`/api/v1/sebrae-uf/${currentUF}/radar`),
      api.get<CruzamentoItem[]>(`/api/v1/sebrae-uf/${currentUF}/cruzamento`),
    ])
      .then(([d, r, c]) => { setDash(d); setRadar(r); setCruzamento(c) })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [currentUF])

  function handleUFChange(e: React.ChangeEvent<HTMLSelectElement>) {
    navigate(`/sebrae-uf/${e.target.value}`)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-gray-400 text-lg">Carregando dados de {currentUF}...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-2">
        <div className="text-red-400">Erro ao carregar dados</div>
        <div className="text-gray-500 text-sm">{error}</div>
      </div>
    )
  }

  const kpis = [
    { title: 'Oportunidades', value: String(dash?.oportunidades_abertas || 0), trend: 0, subtitle: `abertas em ${currentUF}`, color: '#2ecc71' },
    { title: 'Valor Total', value: fmtVal(dash?.valor_total_estimado || 0), trend: 0, subtitle: 'em licitacoes', color: '#0080FF' },
    { title: 'Desertos', value: String(dash?.desertos_fornecimento || 0), trend: 0, subtitle: 'sem fornecedor local', color: '#e74c3c' },
    { title: '% MPE', value: `${dash?.participacao_mpe_percentual || 0}%`, trend: 0, subtitle: 'participacao MPE', color: '#f39c12' },
  ]

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold text-white">Painel SEBRAE</h1>
        <select
          value={currentUF}
          onChange={handleUFChange}
          className="rounded-lg border border-white/10 bg-obs-bg-dark px-3 py-2 text-sm font-semibold text-obs-blue outline-none focus:border-obs-blue"
        >
          {UFS.map((u) => <option key={u} value={u}>{u}</option>)}
        </select>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi) => <KPICard key={kpi.title} {...kpi} />)}
      </div>

      {radar.length > 0 && (
        <div className="rounded-xl border border-white/5 bg-obs-bg p-4">
          <h2 className="mb-4 text-lg font-semibold text-white">Radar de Oportunidades</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-gray-300">
              <thead className="text-xs uppercase text-gray-500 border-b border-white/10">
                <tr>
                  <th className="px-3 py-2">CNAE</th>
                  <th className="px-3 py-2">Orgao</th>
                  <th className="px-3 py-2">Valor</th>
                  <th className="px-3 py-2">Sinal</th>
                  <th className="px-3 py-2">MPEs</th>
                </tr>
              </thead>
              <tbody>
                {radar.slice(0, 15).map((r) => (
                  <tr key={r.id} className="border-b border-white/5 hover:bg-white/5">
                    <td className="px-3 py-2 text-xs">{r.cnae_descricao || r.cnae_divisao}</td>
                    <td className="px-3 py-2 text-xs max-w-[200px] truncate">{r.orgao}</td>
                    <td className="px-3 py-2 text-xs">{fmtVal(r.valor_estimado || 0)}</td>
                    <td className="px-3 py-2">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium text-white ${SINAL_COLORS[r.sinal] || 'bg-gray-600'}`}>
                        {SINAL_LABELS[r.sinal] || r.sinal}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-xs text-center">{r.qtd_mpes_regiao}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {cruzamento.length > 0 && (
        <CruzamentoScatter title={`Cruzamento oferta x demanda — ${currentUF}`} data={cruzamento} />
      )}

      {radar.length === 0 && cruzamento.length === 0 && (
        <div className="rounded-xl border border-white/5 bg-obs-bg p-8 text-center text-gray-500">
          Nenhuma oportunidade encontrada para {currentUF} no periodo atual.
          Os dados sao atualizados diariamente via DOU Secao 3.
        </div>
      )}
    </div>
  )
}
