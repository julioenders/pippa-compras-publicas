import KPICard from '../components/shared/KPICard'
import BrazilMap from '../components/charts/BrazilMap'
import TendenciasChart from '../components/charts/TendenciasChart'
import ComparativoUFsChart from '../components/charts/ComparativoUFsChart'

const kpis = [
  {
    title: 'Contratacoes BR',
    value: '19.083',
    trend: 6,
    subtitle: 'acumulado 2024',
    color: '#2ecc71',
  },
  {
    title: 'Valor Total',
    value: 'R$ 2,1B',
    trend: 14,
    subtitle: 'acumulado 2024',
    color: '#0080FF',
  },
  {
    title: '% MPE Nacional',
    value: '31%',
    trend: -2,
    subtitle: 'participacao em valor',
    color: '#f39c12',
  },
  {
    title: 'Desertos',
    value: '47',
    trend: -8,
    subtitle: 'municipios sem fornecedor',
    color: '#e74c3c',
  },
]

const mockMapData = [
  { uf: 'AC', percentual_mpe: 28.1, total_contratacoes: 4200, valor_total: 980_000_000 },
  { uf: 'AL', percentual_mpe: 26.5, total_contratacoes: 8100, valor_total: 1_800_000_000 },
  { uf: 'AM', percentual_mpe: 25.3, total_contratacoes: 9500, valor_total: 2_500_000_000 },
  { uf: 'AP', percentual_mpe: 22.0, total_contratacoes: 2800, valor_total: 620_000_000 },
  { uf: 'BA', percentual_mpe: 29.4, total_contratacoes: 67000, valor_total: 15_000_000_000 },
  { uf: 'CE', percentual_mpe: 31.2, total_contratacoes: 45000, valor_total: 10_200_000_000 },
  { uf: 'DF', percentual_mpe: 33.8, total_contratacoes: 38000, valor_total: 22_000_000_000 },
  { uf: 'ES', percentual_mpe: 35.5, total_contratacoes: 22000, valor_total: 5_100_000_000 },
  { uf: 'GO', percentual_mpe: 37.1, total_contratacoes: 35000, valor_total: 8_200_000_000 },
  { uf: 'MA', percentual_mpe: 24.8, total_contratacoes: 18000, valor_total: 4_300_000_000 },
  { uf: 'MG', percentual_mpe: 38.5, total_contratacoes: 112000, valor_total: 28_000_000_000 },
  { uf: 'MS', percentual_mpe: 36.0, total_contratacoes: 15000, valor_total: 3_600_000_000 },
  { uf: 'MT', percentual_mpe: 34.2, total_contratacoes: 17000, valor_total: 4_100_000_000 },
  { uf: 'PA', percentual_mpe: 23.9, total_contratacoes: 22000, valor_total: 5_800_000_000 },
  { uf: 'PB', percentual_mpe: 30.1, total_contratacoes: 12000, valor_total: 2_700_000_000 },
  { uf: 'PE', percentual_mpe: 28.7, total_contratacoes: 38000, valor_total: 8_900_000_000 },
  { uf: 'PI', percentual_mpe: 27.3, total_contratacoes: 9800, valor_total: 2_100_000_000 },
  { uf: 'PR', percentual_mpe: 41.0, total_contratacoes: 78000, valor_total: 18_500_000_000 },
  { uf: 'RJ', percentual_mpe: 31.8, total_contratacoes: 98000, valor_total: 31_000_000_000 },
  { uf: 'RN', percentual_mpe: 29.9, total_contratacoes: 11500, valor_total: 2_600_000_000 },
  { uf: 'RO', percentual_mpe: 32.4, total_contratacoes: 7200, valor_total: 1_700_000_000 },
  { uf: 'RR', percentual_mpe: 21.5, total_contratacoes: 2100, valor_total: 480_000_000 },
  { uf: 'RS', percentual_mpe: 40.2, total_contratacoes: 72000, valor_total: 17_000_000_000 },
  { uf: 'SC', percentual_mpe: 42.8, total_contratacoes: 58000, valor_total: 13_500_000_000 },
  { uf: 'SE', percentual_mpe: 27.6, total_contratacoes: 7800, valor_total: 1_750_000_000 },
  { uf: 'SP', percentual_mpe: 36.2, total_contratacoes: 185000, valor_total: 52_000_000_000 },
  { uf: 'TO', percentual_mpe: 30.5, total_contratacoes: 6500, valor_total: 1_500_000_000 },
]

const mockTendencias = [
  { periodo: '2025-10', total_contratos: 97000, percentual_mpe: 33.3 },
  { periodo: '2025-11', total_contratos: 99000, percentual_mpe: 33.6 },
  { periodo: '2025-12', total_contratos: 101000, percentual_mpe: 33.9 },
  { periodo: '2026-01', total_contratos: 103000, percentual_mpe: 34.2 },
  { periodo: '2026-02', total_contratos: 105000, percentual_mpe: 34.5 },
  { periodo: '2026-03', total_contratos: 107000, percentual_mpe: 34.8 },
  { periodo: '2026-04', total_contratos: 109000, percentual_mpe: 35.1 },
  { periodo: '2026-05', total_contratos: 111000, percentual_mpe: 35.4 },
  { periodo: '2026-06', total_contratos: 113000, percentual_mpe: 35.7 },
  { periodo: '2026-07', total_contratos: 115000, percentual_mpe: 36.0 },
  { periodo: '2026-08', total_contratos: 117000, percentual_mpe: 36.3 },
  { periodo: '2026-09', total_contratos: 119000, percentual_mpe: 36.6 },
]

export default function SebraeNacional() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-white">Painel Nacional</h1>

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

      <BrazilMap data={mockMapData} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <TendenciasChart
          title="Tendencias nacionais"
          data={mockTendencias}
        />
        <ComparativoUFsChart
          title="Participacao MPE por UF"
          data={mockMapData}
        />
      </div>
    </div>
  )
}
