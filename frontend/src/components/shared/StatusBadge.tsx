import { SINAIS } from '../../lib/constants'

type Sinal = keyof typeof SINAIS

interface StatusBadgeProps {
  sinal: Sinal
}

const classMap: Record<Sinal, string> = {
  oportunidade: 'signal-oportunidade',
  competitivo: 'signal-competitivo',
  cautela: 'signal-cautela',
  saturado: 'signal-saturado',
  deserto: 'signal-deserto',
}

export default function StatusBadge({ sinal }: StatusBadgeProps) {
  const info = SINAIS[sinal]

  return (
    <span className={`signal-badge ${classMap[sinal]}`}>
      <span>{info.emoji}</span>
      <span>{info.label}</span>
    </span>
  )
}
