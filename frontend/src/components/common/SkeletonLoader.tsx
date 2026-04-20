import clsx from 'clsx'

function Shimmer({ className }: { className?: string }) {
  return <div className={clsx('shimmer rounded', className)} />
}

export function StatSkeleton() {
  return (
    <div className="card p-6 space-y-2.5">
      <Shimmer className="w-20 h-3" />
      <Shimmer className="w-28 h-7" />
      <Shimmer className="w-16 h-3" />
    </div>
  )
}

export function CardSkeleton({ className }: { className?: string }) {
  return (
    <div className={clsx('card p-6 space-y-3', className)}>
      <div className="flex items-center justify-between">
        <Shimmer className="w-32 h-4" />
        <Shimmer className="w-16 h-4" />
      </div>
      <Shimmer className="w-full h-3" />
      <Shimmer className="w-5/6 h-3" />
      <Shimmer className="w-4/6 h-3" />
    </div>
  )
}

export function ChartSkeleton() {
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-5">
        <Shimmer className="w-40 h-5" />
        <div className="flex gap-1">
          {[0, 1, 2, 3, 4].map(i => <Shimmer key={i} className="w-10 h-6" />)}
        </div>
      </div>
      <Shimmer className="w-full h-56" />
    </div>
  )
}

export function ScoreSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-x-10 gap-y-8">
      <div className="md:col-span-4 space-y-3">
        <Shimmer className="w-28 h-3" />
        <Shimmer className="w-32 h-20" />
        <Shimmer className="w-24 h-4" />
      </div>
      <div className="md:col-span-8 space-y-2">
        {[0, 1, 2, 3, 4, 5].map(i => (
          <div key={i} className="space-y-2 py-2 border-b border-border-subtle">
            <div className="flex justify-between">
              <Shimmer className="w-28 h-3" />
              <Shimmer className="w-10 h-3" />
            </div>
            <Shimmer className="w-full h-[2px]" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function DashboardSkeleton() {
  return (
    <div className="pt-8 space-y-10">
      <div className="space-y-6 pb-6 border-b border-border-subtle">
        <div className="space-y-3">
          <Shimmer className="w-40 h-3" />
          <Shimmer className="w-72 h-10" />
        </div>
        <div className="flex items-end gap-4">
          <Shimmer className="w-52 h-12" />
          <Shimmer className="w-32 h-5" />
        </div>
      </div>
      <ScoreSkeleton />
      <ChartSkeleton />
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {[0, 1, 2, 3, 4].map(i => <CardSkeleton key={i} />)}
      </div>
    </div>
  )
}

export default function SkeletonLoader({ className }: { className?: string }) {
  return (
    <div className={clsx('space-y-2', className)}>
      {[0, 1, 2].map(i => (
        <Shimmer key={i} className={clsx('h-4', i === 2 ? 'w-3/4' : 'w-full')} />
      ))}
    </div>
  )
}
