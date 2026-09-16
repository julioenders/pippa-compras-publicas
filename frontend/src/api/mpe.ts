import { api } from './client'
import type { OportunidadeMPE } from '../types/dashboard'

export async function buscarOportunidades(
  cnae: string,
  uf: string,
  municipio?: string,
  limite = 10,
): Promise<OportunidadeMPE[]> {
  const params: Record<string, string> = { cnae, uf, limite: String(limite) }
  if (municipio) params.municipio_ibge = municipio
  return api.get<OportunidadeMPE[]>('/api/v1/mpe/oportunidades', params)
}

export async function buscarOportunidade(id: number): Promise<OportunidadeMPE> {
  return api.get<OportunidadeMPE>(`/api/v1/mpe/oportunidade/${id}`)
}

export async function buscarReferenciaPrecos(catmat: string) {
  return api.get('/api/v1/mpe/referencia-precos', { catmat })
}

export async function buscarGuia(modalidade: string) {
  return api.get(`/api/v1/mpe/guia/${modalidade}`)
}
