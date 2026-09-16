export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const PERFIS = {
  gestorPublico: {
    id: 'gestor-publico',
    titulo: 'Gestor Público',
    subtitulo: 'Painel de compras e conformidade',
    descricao: 'Indicadores de conformidade MPE, benchmark de preços e planejamento PCA.',
    cor: '#0080FF',
    icone: 'building-2',
    rota: '/gestor-publico',
  },
  sebraeNacional: {
    id: 'sebrae-nacional',
    titulo: 'SEBRAE Nacional',
    subtitulo: 'Visão macro e advocacy',
    descricao: 'Panorama nacional, tendências, desertos de fornecimento e dados para políticas públicas.',
    cor: '#2ecc71',
    icone: 'globe',
    rota: '/sebrae-nacional',
  },
  sebraeUF: {
    id: 'sebrae-uf',
    titulo: 'SEBRAE UF',
    subtitulo: 'Radar de oportunidades',
    descricao: 'Oportunidades no estado, cruzamento oferta × demanda e alertas por CNAE.',
    cor: '#f39c12',
    icone: 'map-pin',
    rota: '/sebrae-uf/SP',
  },
  mpe: {
    id: 'mpe',
    titulo: 'MPE',
    subtitulo: 'Suas oportunidades',
    descricao: 'Oportunidades de venda ao governo compatíveis com seu negócio, em linguagem simples.',
    cor: '#e74c3c',
    icone: 'store',
    rota: '/mpe',
  },
} as const

export const SINAIS = {
  oportunidade: { label: 'Oportunidade', cor: '#2ecc71', emoji: '🟢' },
  competitivo: { label: 'Competitivo', cor: '#f39c12', emoji: '🟡' },
  cautela: { label: 'Atenção', cor: '#e67e22', emoji: '🟠' },
  saturado: { label: 'Saturado', cor: '#e74c3c', emoji: '🔴' },
  deserto: { label: 'Deserto', cor: '#95a5a6', emoji: '⚪' },
} as const

export const UFS = [
  'AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT',
  'PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO',
] as const
