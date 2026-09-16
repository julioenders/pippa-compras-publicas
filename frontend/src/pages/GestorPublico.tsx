import { useState, useEffect } from 'react'
import { Filter } from 'lucide-react'
import KPICard from '../components/shared/KPICard'
import ParticipacaoMPEChart from '../components/charts/ParticipacaoMPEChart'
import TopCategoriasChart from '../components/charts/TopCategoriasChart'
import { api } from '../api/client'
import { UFS } from '../lib/constants'

interface Contratacao {
  id: number
  orgao_nome: string
  objeto_resumo: string
  valor_estimado: number
  modalidade: string
  data_publicacao: string
  uf: string
  exclusiva_mpe: boolean
  esfera: string
}

interface ContratacaoResponse {
  pagina: number
  tamanho: number
  total: number
  itens: Contratacao[]
}

function fmtVal(v: number) {
  if (v >= 1e9) return `R$ ${(v / 1e9).toFixed(1)}B`
  if (v >= 1e6) return `R$ ${(v / 1e6).toFixed(1)}M`
  if (v >= 1e3) return `R$ ${(v / 1e3).toFixed(1)}mil`
  return `R$ ${v.toFixed(0)}`
}

export default function GestorPublico() {
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [data, setData] = useState<ContratacaoResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [uf, setUf] = useState('')
  const [modalidade, setModalidade] = useState('')

  useEffect(() => {
    setLoading(true)
    setError(null)
    const params: Record<string, string> = { tamanho: '500' }
    if (uf) params.uf = uf
    if (modalidade) params.modalidade = modalidade
    api
      .get<ContratacaoResponse>('/api/v1/contratacoes/', params)
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [uf, modalidade])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-gray-400 text-lg">Carregando dados reais do PNCP...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-2">
        <div className="text-red-400">Erro ao carregar dados</div>
        <div className="text-gray-500 text-sm">{error}</div>
        <div className="text-gray-600 text-xs mt-2">A API pode estar acordando (ate 50s no plano gratuito)</div>
      </div>
    )
  }

  const itens = data?.itens || []
  const total = data?.total || 0
  const valorTotal = itens.reduce((s, c) => s + (c.valor_estimado || 0), 0)
  const totalMPE = itens.filter((c) => c.exclusiva_mpe).length
  const pctMPE = itens.length > 0 ? Math.round((totalMPE / itens.length) * 100) : 0
  const conformidade = pctMPE >= 25 ? Math.min(100, 50 + pctMPE) : Math.max(20, pctMPE * 2)

  const byMonth = new Map<string, { total: number; mpe: number }>()
  for (const c of itens) {
    const p = c.data_publicacao?.slice(0, 7) || 'sem-data'
    const e = byMonth.get(p) || { total: 0, mpe: 0 }
    e.total++
    if (c.exclusiva_mpe) e.mpe++
    byMonth.set(p, e)
  }
  const participacaoData = [...byMonth.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([periodo, { total: t, mpe }]) => ({
      periodo,
      percentual_mpe: t > 0 ? Math.round((mpe / t) * 1000) / 10 : 0,
      meta: 25,
    }))

  const byMod = new Map<string, { valor: number; qtd: number }>()
  for (const c of itens) {
    const m = c.modalidade || 'Outros'
    const e = byMod.get(m) || { valor: 0, qtd: 0 }
    e.valor += c.valor_estimado || 0
    e.qtd++
    byMod.set(m, e)
  }
  const categoriasData = [...byMod.entries()]
    .map(([grupo_catmat, { valor, qtd }]) => ({ grupo_catmat, valor_total: valor, qtd_itens: qtd }))
    .sort((a, b) => b.valor_total - a.valor_total)
    .slice(0, 6)

  const kpis = [
    { title: 'Total Contratacoes', value: total.toLocaleString('pt-BR'), trend: 0, subtitle: 'dados reais PNCP', color: '#0080FF' },
    { title: 'Valor Total', value: fmtVal(valorTotal), trend: 0, subtitle: 'valor estimado', color: '#2ecc71' },
    { title: 'Participacao MPE', value: `${pctMPE}%`, trend: 0, subtitle: 'exclusivas para MPE', color: '#f39c12' },
    { title: 'Score Conformidade', value: `${conformidade}%`, trend: 0, subtitle: 'meta: 25% MPE', color: '#40BBFF' },
  ]

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Painel do Gestor Publico</h1>
        <button
          type="button"
          onClick={() => setFiltersOpen(!filtersOpen)}
          className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-gray-300 transition-colors hover:bg-white/10"
        >
          <Filter size={16} />
          Filtros
        </button>
      </div>

      {filtersOpen && (
        <div className="flex flex-wrap gap-3 rounded-xl border border-white/5 bg-obs-bg p-4">
          <select value={uf} onChange={(e) => setUf(e.target.value)}
            className="rounded-lg border border-white/10 bg-obs-bg-dark px-3 py-2 text-sm text-gray-300 outline-none focus:border-obs-blue">
            <option value="">Todas UFs</option>
            {UFS.map((u) => <option key={u} value={u}>{u}</option>)}
          </select>
          <select value={modalidade} onChange={(e) => setModalidade(e.target.value)}
            className="rounded-lg border border-white/10 bg-obs-bg-dark px-3 py-2 text-sm text-gray-300 outline-none focus:border-obs-blue">
            <option value="">Todas Modalidades</option>
            <option value="5">Pregao</option>
            <option value="8">Dispensa</option>
            <option value="6">Concorrencia</option>
            <option value="4">Inexigibilidade</option>
          </select>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi) => <KPICard key={kpi.title} {...kpi} />)}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ParticipacaoMPEChart title="Participacao MPE por periodo" data={participacaoData} />
        <TopCategoriasChart title="Top modalidades por valor" data={categoriasData} />
      </div>
    </div>
  )
}
