import { useState, useEffect } from 'react'
import KPICard from '../components/shared/KPICard'
import BrazilMap from '../components/charts/BrazilMap'
import TendenciasChart from '../components/charts/TendenciasChart'
import ComparativoUFsChart from '../components/charts/ComparativoUFsChart'
import { api } from '../api/client'

interface DashboardData {
  total_contratacoes: number
  valor_total_estimado: number
  participacao_mpe_nacional: number
  desertos_fornecimento: number
}

interface MapaUF {
  uf: string
  total_contratos: number
  valor_total: number
  percentual_mpe: number
}

interface Tendencia {
  periodo: string
  total_contratos: number
  percentual_mpe: number
}

function fmtVal(v: number) {
  if (v >= 1e9) return `R$ ${(v / 1e9).toFixed(1)}B`
  if (v >= 1e6) return `R$ ${(v / 1e6).toFixed(1)}M`
  if (v >= 1e3) return `R$ ${(v / 1e3).toFixed(1)}mil`
  return `R$ ${v.toFixed(0)}`
}

export default function SebraeNacional() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [mapaData, setMapaData] = useState<MapaUF[]>([])
  const [tendencias, setTendencias] = useState<Tendencia[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.get<DashboardData>('/api/v1/sebrae-nacional/dashboard'),
      api.get<MapaUF[]>('/api/v1/sebrae-nacional/mapa'),
      api.get<Tendencia[]>('/api/v1/sebrae-nacional/tendencias', { periodo_meses: '12' }),
    ])
      .then(([dash, mapa, tend]) => {
        setDashboard(dash)
        setMapaData(mapa)
        setTendencias(tend)
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-gray-400 text-lg">Carregando painel nacional...</div>
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

  const mapForCharts = mapaData.map((m) => ({
    uf: m.uf,
    percentual_mpe: m.percentual_mpe,
    total_contratacoes: m.total_contratos,
    valor_total: m.valor_total,
  }))

  const kpis = [
    { title: 'Contratacoes BR', value: (dashboard?.total_contratacoes || 0).toLocaleString('pt-BR'), trend: 0, subtitle: 'dados DOU Secao 3', color: '#2ecc71' },
    { title: 'Valor Total', value: fmtVal(dashboard?.valor_total_estimado || 0), trend: 0, subtitle: 'valor estimado', color: '#0080FF' },
    { title: '% MPE Nacional', value: `${dashboard?.participacao_mpe_nacional || 0}%`, trend: 0, subtitle: 'participacao em valor', color: '#f39c12' },
    { title: 'Desertos', value: String(dashboard?.desertos_fornecimento || 0), trend: 0, subtitle: 'regioes sem fornecedor', color: '#e74c3c' },
  ]

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-white">Painel Nacional</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi) => <KPICard key={kpi.title} {...kpi} />)}
      </div>

      <BrazilMap data={mapForCharts} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <TendenciasChart title="Tendencias nacionais" data={tendencias} />
        <ComparativoUFsChart title="Participacao MPE por UF" data={mapForCharts} />
      </div>
    </div>
  )
}
