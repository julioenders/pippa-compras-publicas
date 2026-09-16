import { useState } from 'react'
import { Filter } from 'lucide-react'
import KPICard from '../components/shared/KPICard'
import ParticipacaoMPEChart from '../components/charts/ParticipacaoMPEChart'
import TopCategoriasChart from '../components/charts/TopCategoriasChart'

const kpis = [
  {
    title: 'Total Contratacoes',
    value: '156',
    trend: 12,
    subtitle: 'ultimos 30 dias',
    color: '#0080FF',
  },
  {
    title: 'Valor Total',
    value: 'R$ 12,4M',
    trend: 8,
    subtitle: 'ultimos 30 dias',
    color: '#2ecc71',
  },
  {
    title: 'Participacao MPE',
    value: '32%',
    trend: -3,
    subtitle: 'do total licitado',
    color: '#f39c12',
  },
  {
    title: 'Score Conformidade',
    value: '78%',
    trend: 5,
    subtitle: 'meta: 80%',
    color: '#40BBFF',
  },
]

const mockParticipacao = [
  { periodo: '2025-10', percentual_mpe: 28.5, meta: 25 },
  { periodo: '2025-11', percentual_mpe: 30.2, meta: 25 },
  { periodo: '2025-12', percentual_mpe: 27.8, meta: 25 },
  { periodo: '2026-01', percentual_mpe: 31.0, meta: 25 },
  { periodo: '2026-02', percentual_mpe: 29.5, meta: 25 },
  { periodo: '2026-03', percentual_mpe: 33.1, meta: 25 },
  { periodo: '2026-04', percentual_mpe: 32.4, meta: 25 },
  { periodo: '2026-05', percentual_mpe: 35.0, meta: 25 },
  { periodo: '2026-06', percentual_mpe: 34.2, meta: 25 },
  { periodo: '2026-07', percentual_mpe: 36.1, meta: 25 },
  { periodo: '2026-08', percentual_mpe: 33.8, meta: 25 },
  { periodo: '2026-09', percentual_mpe: 32.0, meta: 25 },
]

const mockCategorias = [
  { grupo_catmat: 'Servicos de TI', valor_total: 2_300_000, qtd_itens: 42 },
  { grupo_catmat: 'Material Escritorio', valor_total: 1_200_000, qtd_itens: 85 },
  { grupo_catmat: 'Alimentacao', valor_total: 950_000, qtd_itens: 67 },
  { grupo_catmat: 'Manutencao Predial', valor_total: 780_000, qtd_itens: 31 },
  { grupo_catmat: 'Combustivel', valor_total: 620_000, qtd_itens: 28 },
  { grupo_catmat: 'Equipamentos', valor_total: 450_000, qtd_itens: 15 },
]

export default function GestorPublico() {
  const [filtersOpen, setFiltersOpen] = useState(false)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">
          Painel do Gestor Publico
        </h1>
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
          <select className="rounded-lg border border-white/10 bg-obs-bg-dark px-3 py-2 text-sm text-gray-300 outline-none focus:border-obs-blue">
            <option value="">UF</option>
            <option value="SP">SP</option>
            <option value="RJ">RJ</option>
            <option value="MG">MG</option>
          </select>
          <select className="rounded-lg border border-white/10 bg-obs-bg-dark px-3 py-2 text-sm text-gray-300 outline-none focus:border-obs-blue">
            <option value="">Modalidade</option>
            <option value="pregao">Pregao</option>
            <option value="dispensa">Dispensa</option>
            <option value="concorrencia">Concorrencia</option>
          </select>
          <input
            type="date"
            className="rounded-lg border border-white/10 bg-obs-bg-dark px-3 py-2 text-sm text-gray-300 outline-none focus:border-obs-blue"
          />
          <input
            type="date"
            className="rounded-lg border border-white/10 bg-obs-bg-dark px-3 py-2 text-sm text-gray-300 outline-none focus:border-obs-blue"
          />
        </div>
      )}

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

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ParticipacaoMPEChart
          title="Evolucao da participacao MPE (%)"
          data={mockParticipacao}
        />
        <TopCategoriasChart
          title="Top categorias por valor"
          data={mockCategorias}
        />
      </div>
    </div>
  )
}
