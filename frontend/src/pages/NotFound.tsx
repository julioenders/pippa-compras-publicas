import { Link } from 'react-router-dom'
import { Home } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <p className="text-6xl font-extrabold text-obs-blue">404</p>

      <h1 className="mt-4 text-xl font-bold text-white">
        Pagina nao encontrada
      </h1>

      <p className="mt-2 text-sm text-gray-400">
        A pagina que voce procura nao existe ou foi movida.
      </p>

      <Link
        to="/"
        className="mt-8 inline-flex items-center gap-2 rounded-lg bg-obs-blue px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-obs-blue-light"
      >
        <Home size={18} />
        Voltar ao inicio
      </Link>
    </div>
  )
}
