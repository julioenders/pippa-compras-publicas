import type { SinalOportunidade } from '../types/common'

export const SIGNAL_CONFIG: Record<SinalOportunidade, {
  label: string
  cor: string
  emoji: string
  bgClass: string
  textClass: string
}> = {
  oportunidade: {
    label: 'Oportunidade',
    cor: '#2ecc71',
    emoji: '🟢',
    bgClass: 'bg-signal-green/20',
    textClass: 'text-signal-green',
  },
  competitivo: {
    label: 'Competitivo',
    cor: '#f39c12',
    emoji: '🟡',
    bgClass: 'bg-signal-yellow/20',
    textClass: 'text-signal-yellow',
  },
  cautela: {
    label: 'Atenção',
    cor: '#e67e22',
    emoji: '🟠',
    bgClass: 'bg-signal-orange/20',
    textClass: 'text-signal-orange',
  },
  saturado: {
    label: 'Saturado',
    cor: '#e74c3c',
    emoji: '🔴',
    bgClass: 'bg-signal-red/20',
    textClass: 'text-signal-red',
  },
  deserto: {
    label: 'Deserto',
    cor: '#95a5a6',
    emoji: '⚪',
    bgClass: 'bg-signal-gray/20',
    textClass: 'text-signal-gray',
  },
}
