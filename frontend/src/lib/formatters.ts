export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('pt-BR').format(value)
}

export function formatDate(date: string): string {
  return new Intl.DateTimeFormat('pt-BR').format(new Date(date))
}

export function formatCNPJ(cnpj: string): string {
  const digits = cnpj.replace(/\D/g, '')
  return digits.replace(
    /^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/,
    '$1.$2.$3/$4-$5',
  )
}

export function daysUntil(dateStr: string): number {
  const target = new Date(dateStr)
  const today = new Date()
  const diff = target.getTime() - today.getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

export function modalidadeSimples(modalidade: string): string {
  const map: Record<string, string> = {
    pregao: 'Pregão Eletrônico',
    dispensa: 'Dispensa (mais simples!)',
    concorrencia: 'Concorrência',
    inexigibilidade: 'Contratação Direta',
    leilao: 'Leilão',
    credenciamento: 'Credenciamento',
  }
  return map[modalidade] || modalidade
}
