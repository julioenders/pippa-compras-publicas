import { api } from './client'
import type { GestorDashboard } from '../types/dashboard'

export async function buscarDashboard(
  orgaoCnpj: string,
  periodoInicio?: string,
  periodoFim?: string,
): Promise<GestorDashboard> {
  const params: Record<string, string> = { orgao_cnpj: orgaoCnpj }
  if (periodoInicio) params.periodo_inicio = periodoInicio
  if (periodoFim) params.periodo_fim = periodoFim
  return api.get<GestorDashboard>('/api/v1/gestor-publico/dashboard', params)
}

export async function buscarParticipacaoMPE(orgaoCnpj: string, periodoMeses = 12) {
  return api.get('/api/v1/gestor-publico/participacao-mpe', {
    orgao_cnpj: orgaoCnpj,
    periodo_meses: String(periodoMeses),
  })
}

export async function buscarBenchmarkPrecos(catmat: string, uf?: string) {
  const params: Record<string, string> = { catmat }
  if (uf) params.uf = uf
  return api.get('/api/v1/gestor-publico/benchmark-precos', params)
}
