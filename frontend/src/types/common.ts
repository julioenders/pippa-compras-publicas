export type Esfera = 'F' | 'E' | 'M'

export type SinalOportunidade =
  | 'oportunidade'
  | 'competitivo'
  | 'cautela'
  | 'saturado'
  | 'deserto'

export type Perfil = 'gestor_publico' | 'sebrae_nacional' | 'sebrae_uf' | 'mpe'

export interface Paginacao {
  total_registros: number
  total_paginas: number
  pagina_atual: number
  paginas_restantes: number
}

export interface Filtros {
  uf?: string
  cnae?: string
  data_inicio?: string
  data_fim?: string
  modalidade?: string
  esfera?: Esfera
}
