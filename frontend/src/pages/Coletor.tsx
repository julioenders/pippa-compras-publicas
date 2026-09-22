import { useState } from 'react'
import { Play, Loader2, CheckCircle2, AlertCircle, Calendar } from 'lucide-react'
import { api } from '../api/client'

interface ColetaResult {
  status: string
  job: string
  result: {
    data: string
    publicacoes_brutas: number
    relevantes: number
    contratacoes_criadas: number
    contratacoes_atualizadas: number
    itens_criados: number
    eventos_criados: number
    alertas_criados: number
    duplicadas: number
    erros: number
    erro?: string
  }
}

export default function Coletor() {
  const [data, setData] = useState(() => {
    const ontem = new Date()
    ontem.setDate(ontem.getDate() - 1)
    return ontem.toISOString().slice(0, 10)
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ColetaResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleRun() {
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const res = await api.post<ColetaResult>('/admin/collect/dou', { data })
      setResult(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl py-10 px-4">
      <h1 className="text-2xl font-bold text-white">Coletor DOU Secao 3</h1>
      <p className="mt-2 text-sm text-gray-400">
        Escolha uma data e execute a coleta de publicacoes do Diario Oficial da Uniao.
      </p>

      <div className="mt-8 rounded-xl border border-white/10 bg-obs-bg p-6">
        <label className="block text-sm font-medium text-gray-300">
          Data da publicacao
        </label>
        <div className="mt-2 flex items-center gap-4">
          <div className="relative flex-1">
            <Calendar size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="date"
              value={data}
              onChange={(e) => setData(e.target.value)}
              disabled={loading}
              className="w-full rounded-lg border border-white/10 bg-white/5 py-2.5 pl-10 pr-3 text-sm text-white outline-none focus:border-obs-blue-light focus:ring-1 focus:ring-obs-blue-light disabled:opacity-50"
            />
          </div>
          <button
            type="button"
            onClick={handleRun}
            disabled={loading || !data}
            className="flex items-center gap-2 rounded-lg bg-obs-blue px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-obs-blue-light disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Coletando...
              </>
            ) : (
              <>
                <Play size={16} />
                Executar
              </>
            )}
          </button>
        </div>
      </div>

      {loading && (
        <div className="mt-6 rounded-xl border border-obs-blue/20 bg-obs-blue/5 p-6 text-center">
          <Loader2 size={32} className="mx-auto animate-spin text-obs-blue-light" />
          <p className="mt-3 text-sm text-gray-300">
            Coletando publicacoes do DOU para {data}...
          </p>
          <p className="mt-1 text-xs text-gray-500">
            Isso pode levar alguns minutos.
          </p>
        </div>
      )}

      {error && (
        <div className="mt-6 rounded-xl border border-red-500/20 bg-red-500/5 p-6">
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle size={20} />
            <span className="font-semibold">Erro na coleta</span>
          </div>
          <p className="mt-2 text-sm text-red-300">{error}</p>
        </div>
      )}

      {result && (
        <div className="mt-6 rounded-xl border border-green-500/20 bg-green-500/5 p-6">
          <div className="flex items-center gap-2 text-green-400">
            <CheckCircle2 size={20} />
            <span className="font-semibold">Coleta finalizada</span>
          </div>

          {result.result.erro ? (
            <p className="mt-3 text-sm text-red-300">{result.result.erro}</p>
          ) : (
            <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Stat label="Data" value={result.result.data} />
              <Stat label="Publicacoes brutas" value={result.result.publicacoes_brutas} />
              <Stat label="Relevantes" value={result.result.relevantes} />
              <Stat label="Contratacoes criadas" value={result.result.contratacoes_criadas} />
              <Stat label="Atualizadas" value={result.result.contratacoes_atualizadas} />
              <Stat label="Itens criados" value={result.result.itens_criados} />
              <Stat label="Alertas" value={result.result.alertas_criados} />
              <Stat label="Erros" value={result.result.erros} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="mt-0.5 text-lg font-bold text-white">{String(value)}</p>
    </div>
  )
}
