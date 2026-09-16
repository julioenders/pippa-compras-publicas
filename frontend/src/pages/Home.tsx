import { Link } from 'react-router-dom'
import { Building2, Globe, MapPin, Store, Database } from 'lucide-react'
import { PERFIS } from '../lib/constants'

const iconMap: Record<string, React.ReactNode> = {
  'building-2': <Building2 size={32} />,
  globe: <Globe size={32} />,
  'map-pin': <MapPin size={32} />,
  store: <Store size={32} />,
}

const perfisArray = [
  PERFIS.gestorPublico,
  PERFIS.sebraeNacional,
  PERFIS.sebraeUF,
  PERFIS.mpe,
]

const fonteDados = [
  'PNCP',
  'DOU Secao 3',
  'Querido Diario',
  'Dados Abertos Compras',
  'Observatorio SEBRAE',
]

export default function Home() {
  return (
    <div className="flex flex-col items-center gap-12 py-10">
      {/* Title Section */}
      <section className="text-center">
        <h1 className="bg-gradient-to-r from-obs-blue to-obs-blue-light bg-clip-text text-4xl font-extrabold text-transparent sm:text-5xl">
          PIPPA Compras Publicas
        </h1>
        <p className="mt-3 text-lg text-gray-400">
          Inteligencia em Compras Governamentais para MPEs
        </p>
      </section>

      {/* Profile Cards Grid */}
      <section className="grid w-full max-w-4xl grid-cols-1 gap-6 sm:grid-cols-2">
        {perfisArray.map((perfil) => (
          <Link
            key={perfil.id}
            to={perfil.rota}
            className="group relative rounded-xl border border-white/5 bg-obs-bg p-6 transition-all duration-300 hover:shadow-lg hover:shadow-obs-blue/10"
            style={{ borderLeftWidth: '4px', borderLeftColor: perfil.cor }}
          >
            {/* Icon */}
            <div
              className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg"
              style={{ backgroundColor: `${perfil.cor}20`, color: perfil.cor }}
            >
              {iconMap[perfil.icone]}
            </div>

            {/* Title */}
            <h2 className="text-lg font-bold text-white group-hover:text-obs-blue-light">
              {perfil.titulo}
            </h2>

            {/* Subtitle */}
            <p
              className="mt-1 text-sm font-medium"
              style={{ color: perfil.cor }}
            >
              {perfil.subtitulo}
            </p>

            {/* Description */}
            <p className="mt-2 text-sm leading-relaxed text-gray-400">
              {perfil.descricao}
            </p>
          </Link>
        ))}
      </section>

      {/* Fontes de Dados */}
      <section className="w-full max-w-4xl">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Database size={16} />
          <span className="font-medium">Fontes de dados:</span>
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          {fonteDados.map((fonte) => (
            <span
              key={fonte}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-gray-400"
            >
              {fonte}
            </span>
          ))}
        </div>
      </section>
    </div>
  )
}
