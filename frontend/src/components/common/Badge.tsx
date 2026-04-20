import clsx from 'clsx'

interface Props {
  children: React.ReactNode
  variant?: 'green' | 'red' | 'blue' | 'amber' | 'muted'
  size?: 'xs' | 'sm' | 'md'
  dot?: boolean
  className?: string
}

const textClass = {
  green: 'text-green',
  red: 'text-red',
  amber: 'text-yellow',
  blue: 'text-text-secondary',
  muted: 'text-text-tertiary',
} as const

const dotClass = {
  green: 'bg-accent-green',
  red: 'bg-accent-red',
  amber: 'bg-accent-amber',
  blue: 'bg-text-secondary',
  muted: 'bg-text-tertiary',
} as const

export default function Badge({ children, variant = 'muted', size = 'sm', dot, className }: Props) {
  return (
    <span className={clsx(
      'inline-flex items-center gap-1.5 rounded-full border border-border-subtle whitespace-nowrap',
      size === 'xs' ? 'text-[10px] px-2 py-0.5' : size === 'sm' ? 'text-[11px] px-2 py-0.5' : 'text-xs px-2.5 py-1',
      textClass[variant],
      className
    )}>
      {dot && <span className={clsx('w-1 h-1 rounded-full shrink-0', dotClass[variant])} />}
      {children}
    </span>
  )
}
