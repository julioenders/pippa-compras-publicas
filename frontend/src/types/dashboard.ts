import type { SinalOportunidade } from './common'

export interface KPI {
  titulo: string
  valor: number | string
  subtitulo?: string
  tendencia?: number
}

export interface GestorDashboard {
  total_contratacoes: number
  valor_total: number
  percentual_mpe: number
  score_conformidade: number
  top_categorias: Array<{ categoria: string; valor: number; quantidade: number }>
}

export interface NacionalDashboard {
  total_contratacoes_br: number
  valor_total_br: number
  percentual_mpe_nacional: number
  num_desertos: number
  dados_por_uf: Array<{
    uf: string
    percentual_mpe: number
    total_contratacoes: number
    valor_total: number
  }>
}

export interface UFDashboard {
  oportunidades_uf: number
  valor_total_uf: number
  desertos_uf: number
  alertas_ativos: number
}

export interface OportunidadeMPE {
  id: number
  titulo: string
  valor: number
  modalidade: string
  modalidade_simples: string
  prazo: string
  exclusiva_mpe: boolean
  sinal: SinalOportunidade
  orgao_nome: string
  uf: string
  municipio: string
}

export interface Alerta {
  id: number
  tipo: string
  titulo: string
  corpo: string
  uf: string
  cnae_divisao: string
  sinal: SinalOportunidade
  created_at: string
}
