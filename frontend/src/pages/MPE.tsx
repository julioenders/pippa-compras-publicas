import { useState, useEffect } from 'react'
import {
  Search,
  Clock,
  Share2,
  Shield,
  ChevronRight,
} from 'lucide-react'
import { SINAIS, UFS } from '../lib/constants'
import { formatCurrency, daysUntil } from '../lib/formatters'
import type { SinalOportunidade } from '../types/common'
import { api } from '../api/client'

interface SavedProfile {
  cnae: string
  uf: string
}

interface Oportunidade {
  id: number
  orgao?: string
  orgao_nome?: string
  objeto?: string
  titulo?: string
  valor_estimado?: number
  valor?: string
  prazo?: string
  data_encerramento?: string
  data_encerramento_proposta?: string
  sinal?: SinalOportunidade
  exclusiva_mpe?: boolean
  modalidade?: string
  uf?: string
  municipio?: string
  municipio_ibge?: string
  score?: number
  fonte?: string
}

function SignalDot({ sinal }: { sinal?: SinalOportunidade }) {
  const s = sinal || 'competitivo'
  const info = SINAIS[s]
  if (!info) return null
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={{ backgroundColor: `${info.cor}18`, color: info.cor }}
    >
      <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: info.cor }} />
      {info.label}
    </span>
  )
}

function OnboardingCard({ onSave }: { onSave: (p: SavedProfile) => void }) {
  const [cnae, setCnae] = useState('')
  const [uf, setUf] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (cnae && uf) onSave({ cnae, uf })
  }

  return (
    <div className="mx-auto max-w-md rounded-2xl bg-white p-8 shadow-lg">
      <h2 className="text-xl font-bold text-gray-900">Vamos comecar!</h2>
      <p className="mt-2 text-sm text-gray-600">
        Informe seu CNAE e estado para encontrarmos oportunidades compativeis com seu negocio.
      </p>
      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        <div>
          <label htmlFor="cnae" className="block text-sm font-medium text-gray-700">CNAE principal</label>
          <input id="cnae" type="text" placeholder="Ex: 4761 (Comercio de livros)"
            value={cnae} onChange={(e) => setCnae(e.target.value)}
            className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-3 text-sm text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20" />
        </div>
        <div>
          <label htmlFor="uf" className="block text-sm font-medium text-gray-700">Estado</label>
          <select id="uf" value={uf} onChange={(e) => setUf(e.target.value)}
            className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-3 text-sm text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20">
            <option value="">Selecione o estado</option>
            {UFS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <button type="submit" disabled={!cnae || !uf}
          className="mt-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40">
          Buscar oportunidades
        </button>
      </form>
    </div>
  )
}

function OpportunityCard({ op }: { op: Oportunidade }) {
  const titulo = op.titulo || op.objeto || 'Oportunidade de licitacao'
  const valor = op.valor_estimado || 0
  const prazoStr = op.prazo || op.data_encerramento || op.data_encerramento_proposta || ''
  const dias = prazoStr ? daysUntil(prazoStr) : -1
  const orgao = op.orgao || op.orgao_nome || ''
  const municipio = op.municipio || op.uf || ''

  function handleShare() {
    const text = encodeURIComponent(
      `Oportunidade de licitacao: ${titulo} - ${formatCurrency(valor)} - ${orgao}`,
    )
    window.open(`https://wa.me/?text=${text}`, '_blank')
  }

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-base font-semibold leading-snug text-gray-900 line-clamp-2">{titulo}</h3>
        <SignalDot sinal={op.sinal} />
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {op.exclusiva_mpe && (
          <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
            <Shield size={12} /> Exclusivo para pequenas empresas
          </span>
        )}
        {op.modalidade && (
          <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-600">{op.modalidade}</span>
        )}
        {op.fonte && (
          <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs text-blue-600">Fonte: {op.fonte}</span>
        )}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-600">
        <span className="font-semibold text-gray-900">{valor > 0 ? formatCurrency(valor) : op.valor || 'Valor nao informado'}</span>
        {dias > 0 && (
          <span className="flex items-center gap-1"><Clock size={14} />{dias} dias restantes</span>
        )}
        {municipio && <span>{municipio}</span>}
      </div>

      {orgao && <p className="mt-1 text-xs text-gray-500">{orgao}</p>}

      <div className="mt-4 flex gap-3">
        <button type="button"
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700 active:bg-blue-800">
          Ver detalhes <ChevronRight size={16} />
        </button>
        <button type="button" onClick={handleShare}
          className="flex items-center justify-center gap-2 rounded-xl border border-gray-300 px-4 py-3 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 active:bg-gray-100"
          aria-label="Compartilhar no WhatsApp">
          <Share2 size={16} /> Compartilhar
        </button>
      </div>
    </div>
  )
}

export default function MPE() {
  const [profile, setProfile] = useState<SavedProfile | null>(null)
  const [oportunidades, setOportunidades] = useState<Oportunidade[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const saved = localStorage.getItem('pippa_mpe_profile')
    if (saved) {
      try { setProfile(JSON.parse(saved)) } catch { /* ignore */ }
    }
  }, [])

  useEffect(() => {
    if (!profile) return
    setLoading(true)
    setError(null)
    api
      .get<Oportunidade[]>('/api/v1/mpe/oportunidades', {
        cnae: profile.cnae,
        uf: profile.uf,
        limite: '20',
      })
      .then(setOportunidades)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [profile])

  function handleSaveProfile(newProfile: SavedProfile) {
    localStorage.setItem('pippa_mpe_profile', JSON.stringify(newProfile))
    setProfile(newProfile)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-lg px-4 py-6">
        <h1 className="text-2xl font-bold text-gray-900">Suas Oportunidades</h1>

        {!profile ? (
          <div className="mt-8">
            <OnboardingCard onSave={handleSaveProfile} />
          </div>
        ) : (
          <>
            <div className="mt-4 flex items-center justify-between rounded-xl bg-white p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <Search size={18} className="text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-gray-900">CNAE: {profile.cnae}</p>
                  <p className="text-xs text-gray-500">Estado: {profile.uf}</p>
                </div>
              </div>
              <button type="button" onClick={() => { localStorage.removeItem('pippa_mpe_profile'); setProfile(null) }}
                className="text-xs text-blue-600 hover:underline">Alterar</button>
            </div>

            {loading && (
              <div className="mt-8 text-center">
                <div className="animate-pulse text-gray-500">Buscando oportunidades reais do PNCP...</div>
                <div className="mt-2 text-xs text-gray-400">Pode levar ate 50s na primeira vez (API acordando)</div>
              </div>
            )}

            {error && (
              <div className="mt-8 rounded-xl bg-red-50 p-4 text-center">
                <div className="text-red-600 text-sm">Erro ao buscar oportunidades</div>
                <div className="text-red-400 text-xs mt-1">{error}</div>
              </div>
            )}

            {!loading && !error && (
              <>
                <p className="mt-6 text-sm text-gray-500">
                  <span className="font-semibold text-gray-900">{oportunidades.length} oportunidades</span>{' '}
                  encontradas para seu perfil
                </p>

                <div className="mt-4 flex flex-col gap-4">
                  {oportunidades.map((op) => <OpportunityCard key={op.id} op={op} />)}
                </div>

                {oportunidades.length === 0 && (
                  <div className="mt-4 rounded-xl bg-white p-6 text-center text-gray-500 shadow-sm">
                    Nenhuma oportunidade encontrada para CNAE {profile.cnae} em {profile.uf}.
                    Tente um CNAE mais generico (ex: 47 ao inves de 4761).
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}
