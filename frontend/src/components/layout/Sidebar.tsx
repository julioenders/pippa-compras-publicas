import { Building2, Globe, MapPin, Store } from 'lucide-react'
import type { ReactNode } from 'react'

interface SidebarProps {
  profileId?: string
  profileTitle?: string
  profileSubtitle?: string
  children?: ReactNode
}

const iconMap: Record<string, ReactNode> = {
  'gestor-publico': <Building2 size={20} />,
  'sebrae-nacional': <Globe size={20} />,
  'sebrae-uf': <MapPin size={20} />,
  mpe: <Store size={20} />,
}

export default function Sidebar({
  profileId,
  profileTitle,
  profileSubtitle,
  children,
}: SidebarProps) {
  return (
    <aside className="hidden w-64 shrink-0 border-r border-white/10 bg-obs-bg-dark p-4 lg:block">
      {profileId && (
        <div className="mb-6 flex items-center gap-3 rounded-lg bg-white/5 p-3">
          <span className="text-obs-blue-light">
            {iconMap[profileId] ?? <Building2 size={20} />}
          </span>
          <div>
            <p className="text-sm font-semibold text-white">{profileTitle}</p>
            {profileSubtitle && (
              <p className="text-xs text-gray-400">{profileSubtitle}</p>
            )}
          </div>
        </div>
      )}

      {children}
    </aside>
  )
}
