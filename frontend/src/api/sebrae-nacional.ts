import { api } from './client'
import type { NacionalDashboard } from '../types/dashboard'

export async function buscarDashboard(
  periodoInicio?: string,
  periodoFim?: string,
): Promise<NacionalDashboard> {
  const params: Record<string, string> = {}
  if (periodoInicio) params.periodo_inicio = periodoInicio
  if (periodoFim) params.periodo_fim = periodoFim
  return api.get<NacionalDashboard>('/api/v1/sebrae-nacional/dashboard', params)
}

export async function buscarMapa() {
  return api.get('/api/v1/sebrae-nacional/mapa')
}

export async function buscarDesertos() {
  return api.get('/api/v1/sebrae-nacional/desertos')
}

export async function buscarTendencias(periodoMeses = 12) {
  return api.get('/api/v1/sebrae-nacional/tendencias', {
    periodo_meses: String(periodoMeses),
  })
}
