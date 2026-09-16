import { useState, useEffect } from 'react'
import {
  Search,
  Clock,
  ExternalLink,
  Share2,
  Shield,
  ChevronRight,
} from 'lucide-react'
import { SINAIS, UFS } from '../lib/constants'
import { formatCurrency, daysUntil } from '../lib/formatters'
import type { SinalOportunidade } from '../types/common'

interface SavedProfile {
  cnae: string
  uf: string
}

interface MockOportunidade {
  id: number
  titulo: string
  valor: number
  prazo: string
  sinal: SinalOportunidade
  exclusiva_mpe: boolean
  orgao: string
  modalidade: string
  municipio: string
}

const mockOportunidades: MockOportunidade[] = [
  {
    id: 1,
    titulo: 'Aquisicao de material de escritorio e papelaria',
    valor: 45000,
    prazo: '2026-10-01',
    sinal: 'oportunidade',
    exclusiva_mpe: true,
    orgao: 'Prefeitura Municipal',
    modalidade: 'Dispensa (mais simples!)',
    municipio: 'Campinas/SP',
  },
  {
    id: 2,
    titulo: 'Servicos de manutencao predial preventiva',
    valor: 180000,
    prazo: '2026-09-28',
    sinal: 'competitivo',
    exclusiva_mpe: false,
    orgao: 'Secretaria de Educacao',
    modalidade: 'Pregao Eletronico',
    municipio: 'Sorocaba/SP',
  },
  {
    id: 3,
    titulo: 'Fornecimento de refeicoes prontas - merenda escolar',
    valor: 320000,
    prazo: '2026-10-05',
    sinal: 'oportunidade',
    exclusiva_mpe: true,
    orgao: 'FNDE',
    modalidade: 'Pregao Eletronico',
    municipio: 'Sao Paulo/SP',
  },
]

function SignalDot({ sinal }: { sinal: SinalOportunidade }) {
  const info = SINAIS[sinal]
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={{
        backgroundColor: `${info.cor}18`,
        color: info.cor,
      }}
    >
      <span
        className="inline-block h-2 w-2 rounded-full"
        style={{ backgroundColor: info.cor }}
      />
      {info.label}
    </span>
  )
}

function OnboardingCard({
  onSave,
}: {
  onSave: (profile: SavedProfile) => void
}) {
  const [cnae, setCnae] = useState('')
  const [uf, setUf] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (cnae && uf) {
      onSave({ cnae, uf })
    }
  }

  return (
    <div className="mx-auto max-w-md rounded-2xl bg-white p-8 shadow-lg">
      <h2 className="text-xl font-bold text-gray-900">
        Vamos comecar!
      </h2>
      <p className="mt-2 text-sm text-gray-600">
        Informe seu CNAE e estado para encontrarmos oportunidades compativeis
        com seu negocio.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        <div>
          <label
            htmlFor="cnae"
            className="block text-sm font-medium text-gray-700"
          >
            CNAE principal
          </label>
          <input
            id="cnae"
            type="text"
            placeholder="Ex: 47.61-0 (Comercio de livros)"
            value={cnae}
            onChange={(e) => setCnae(e.target.value)}
            className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-3 text-sm text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          />
        </div>

        <div>
          <label
            htmlFor="uf"
            className="block text-sm font-medium text-gray-700"
          >
            Estado
          </label>
          <select
            id="uf"
            value={uf}
            onChange={(e) => setUf(e.target.value)}
            className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-3 text-sm text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          >
            <option value="">Selecione o estado</option>
            {UFS.map((sigla) => (
              <option key={sigla} value={sigla}>
                {sigla}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={!cnae || !uf}
          className="mt-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Buscar oportunidades
        </button>
      </form>
    </div>
  )
}

function OpportunityCard({ op }: { op: MockOportunidade }) {
  const dias = daysUntil(op.prazo)

  function handleShare() {
    const text = encodeURIComponent(
      `Oportunidade de licitacao: ${op.titulo} - ${formatCurrency(op.valor)} - Prazo: ${dias} dias`,
    )
    window.open(`https://wa.me/?text=${text}`, '_blank')
  }

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-base font-semibold leading-snug text-gray-900">
          {op.titulo}
        </h3>
        <SignalDot sinal={op.sinal} />
      </div>

      {/* Tags */}
      <div className="mt-3 flex flex-wrap gap-2">
        {op.exclusiva_mpe && (
          <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
            <Shield size={12} />
            Exclusivo para pequenas empresas
          </span>
        )}
        <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-600">
          {op.modalidade}
        </span>
      </div>

      {/* Details */}
      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-600">
        <span className="font-semibold text-gray-900">
          {formatCurrency(op.valor)}
        </span>
        <span className="flex items-center gap-1">
          <Clock size={14} />
          {dias > 0 ? `${dias} dias restantes` : 'Encerrado'}
        </span>
        <span>{op.municipio}</span>
      </div>

      <p className="mt-1 text-xs text-gray-500">{op.orgao}</p>

      {/* Actions */}
      <div className="mt-4 flex gap-3">
        <button
          type="button"
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700 active:bg-blue-800"
        >
          Ver detalhes
          <ChevronRight size={16} />
        </button>
        <button
          type="button"
          onClick={handleShare}
          className="flex items-center justify-center gap-2 rounded-xl border border-gray-300 px-4 py-3 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 active:bg-gray-100"
          aria-label="Compartilhar no WhatsApp"
        >
          <Share2 size={16} />
          Compartilhar
        </button>
      </div>
    </div>
  )
}

export default function MPE() {
  const [profile, setProfile] = useState<SavedProfile | null>(null)

  useEffect(() => {
    const saved = localStorage.getItem('pippa_mpe_profile')
    if (saved) {
      try {
        setProfile(JSON.parse(saved))
      } catch {
        // Invalid data in localStorage, ignore
      }
    }
  }, [])

  function handleSaveProfile(newProfile: SavedProfile) {
    localStorage.setItem('pippa_mpe_profile', JSON.stringify(newProfile))
    setProfile(newProfile)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-lg px-4 py-6">
        {/* Header */}
        <h1 className="text-2xl font-bold text-gray-900">
          Suas Oportunidades
        </h1>

        {!profile ? (
          /* Onboarding */
          <div className="mt-8">
            <OnboardingCard onSave={handleSaveProfile} />
          </div>
        ) : (
          <>
            {/* Profile info */}
            <div className="mt-4 flex items-center justify-between rounded-xl bg-white p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <Search size={18} className="text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    CNAE: {profile.cnae}
                  </p>
                  <p className="text-xs text-gray-500">Estado: {profile.uf}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  localStorage.removeItem('pippa_mpe_profile')
                  setProfile(null)
                }}
                className="text-xs text-blue-600 hover:underline"
              >
                Alterar
              </button>
            </div>

            {/* Results count */}
            <p className="mt-6 text-sm text-gray-500">
              <span className="font-semibold text-gray-900">
                {mockOportunidades.length} oportunidades
              </span>{' '}
              encontradas para seu perfil
            </p>

            {/* Opportunity Cards */}
            <div className="mt-4 flex flex-col gap-4">
              {mockOportunidades.map((op) => (
                <OpportunityCard key={op.id} op={op} />
              ))}
            </div>

            {/* Load more (placeholder) */}
            <button
              type="button"
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl border border-gray-300 bg-white py-3 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              <ExternalLink size={16} />
              Carregar mais oportunidades
            </button>
          </>
        )}
      </div>
    </div>
  )
}
