import { Inbox, Search, AlertCircle } from 'lucide-react'
import type { ReactNode } from 'react'

interface EmptyStateProps {
  message: string
  icon?: 'inbox' | 'search' | 'alert'
}

const iconMap: Record<string, ReactNode> = {
  inbox: <Inbox size={48} strokeWidth={1.2} />,
  search: <Search size={48} strokeWidth={1.2} />,
  alert: <AlertCircle size={48} strokeWidth={1.2} />,
}

export default function EmptyState({
  message,
  icon = 'inbox',
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-gray-500">
      <span className="mb-4 text-gray-600">{iconMap[icon]}</span>
      <p className="max-w-xs text-center text-sm">{message}</p>
    </div>
  )
}
