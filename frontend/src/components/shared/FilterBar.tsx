import { useCallback } from 'react'
import { Search } from 'lucide-react'
import { UFS } from '../../lib/constants'

export interface Filters {
  uf?: string
  cnae?: string
  dataInicio?: string
  dataFim?: string
}

interface FilterBarProps {
  onFilterChange: (filters: Filters) => void
  showUF?: boolean
  showCNAE?: boolean
  showDateRange?: boolean
}

export default function FilterBar({
  onFilterChange,
  showUF = true,
  showCNAE = false,
  showDateRange = false,
}: FilterBarProps) {
  const handleChange = useCallback(
    (field: keyof Filters, value: string) => {
      onFilterChange({ [field]: value || undefined })
    },
    [onFilterChange],
  )

  const selectClasses =
    'rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none transition focus:border-obs-blue focus:ring-1 focus:ring-obs-blue'
  const inputClasses =
    'rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none transition placeholder:text-gray-500 focus:border-obs-blue focus:ring-1 focus:ring-obs-blue'

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-white/5 bg-white/[0.02] p-3">
      {showUF && (
        <select
          className={selectClasses}
          defaultValue=""
          onChange={(e) => handleChange('uf', e.target.value)}
          aria-label="Filtrar por UF"
        >
          <option value="">Todas UFs</option>
          {UFS.map((uf) => (
            <option key={uf} value={uf}>
              {uf}
            </option>
          ))}
        </select>
      )}

      {showCNAE && (
        <div className="relative">
          <Search
            size={14}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
          />
          <input
            type="text"
            placeholder="CNAE ou palavra-chave"
            className={`${inputClasses} pl-8`}
            onChange={(e) => handleChange('cnae', e.target.value)}
            aria-label="Filtrar por CNAE"
          />
        </div>
      )}

      {showDateRange && (
        <>
          <input
            type="date"
            className={inputClasses}
            onChange={(e) => handleChange('dataInicio', e.target.value)}
            aria-label="Data inicio"
          />
          <span className="text-xs text-gray-500">ate</span>
          <input
            type="date"
            className={inputClasses}
            onChange={(e) => handleChange('dataFim', e.target.value)}
            aria-label="Data fim"
          />
        </>
      )}
    </div>
  )
}
