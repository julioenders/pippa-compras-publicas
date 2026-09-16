interface LoadingSkeletonProps {
  lines?: number
}

export default function LoadingSkeleton({ lines = 3 }: LoadingSkeletonProps) {
  return (
    <div className="space-y-3" role="status" aria-label="Carregando">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 animate-pulse rounded bg-white/10"
          style={{ width: `${85 - i * 10}%` }}
        />
      ))}
      <span className="sr-only">Carregando...</span>
    </div>
  )
}
