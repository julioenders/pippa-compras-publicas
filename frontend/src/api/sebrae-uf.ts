import { api } from './client'
import type { UFDashboard, Alerta } from '../types/dashboard'

export async function buscarDashboard(uf: string): Promise<UFDashboard> {
  return api.get<UFDashboard>(`/api/v1/sebrae-uf/${uf}/dashboard`)
}

export async function buscarRadar(uf: string) {
  return api.get(`/api/v1/sebrae-uf/${uf}/radar`)
}

export async function buscarCruzamento(uf: string) {
  return api.get(`/api/v1/sebrae-uf/${uf}/cruzamento`)
}

export async function buscarAlertas(uf: string): Promise<Alerta[]> {
  return api.get<Alerta[]>(`/api/v1/sebrae-uf/${uf}/alertas`)
}
