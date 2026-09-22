import { Outlet } from 'react-router-dom'
import Header from './Header'

export default function AppShell() {
  return (
    <div className="flex min-h-screen flex-col bg-obs-bg-dark text-white">
      <Header />

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-white/10 bg-obs-bg-dark py-4">
        <p className="text-center text-xs text-gray-500">
          Dados: DOU - Diario Oficial da Uniao, Secao 3
        </p>
      </footer>
    </div>
  )
}
