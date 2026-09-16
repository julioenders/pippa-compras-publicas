import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { PERFIS } from '../../lib/constants'

const navItems = [
  { label: PERFIS.gestorPublico.titulo, to: PERFIS.gestorPublico.rota },
  { label: PERFIS.sebraeNacional.titulo, to: PERFIS.sebraeNacional.rota },
  { label: PERFIS.sebraeUF.titulo, to: '/sebrae-uf/SP' },
  { label: PERFIS.mpe.titulo, to: PERFIS.mpe.rota },
]

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-obs-bg-dark/95 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        {/* Logo */}
        <NavLink to="/" className="flex items-baseline gap-2">
          <span className="bg-gradient-to-r from-obs-blue to-obs-blue-light bg-clip-text text-xl font-bold text-transparent">
            PIPPA
          </span>
          <span className="text-sm font-medium text-gray-400">
            Compras Publicas
          </span>
        </NavLink>

        {/* Desktop Nav */}
        <nav className="hidden items-center gap-1 md:flex">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `relative px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'text-obs-blue-light'
                    : 'text-gray-400 hover:text-white'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {item.label}
                  {isActive && (
                    <span className="absolute bottom-0 left-3 right-3 h-0.5 rounded-full bg-obs-blue-light" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Mobile Menu Button */}
        <button
          type="button"
          className="rounded-md p-2 text-gray-400 hover:text-white md:hidden"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label={menuOpen ? 'Fechar menu' : 'Abrir menu'}
        >
          {menuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile Nav */}
      {menuOpen && (
        <nav className="border-t border-white/5 bg-obs-bg-dark px-4 pb-3 pt-2 md:hidden">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) =>
                `block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-obs-blue/10 text-obs-blue-light'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      )}
    </header>
  )
}
