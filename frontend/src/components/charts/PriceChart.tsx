import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine
} from 'recharts'
import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import type { HistoryPoint } from '@/types'
import { formatCurrency, formatDate } from '@/utils/formatters'
import clsx from 'clsx'

const PERIODS = [
  { label: '1W', value: '1wk' },
  { label: '1M', value: '1mo' },
  { label: '3M', value: '3mo' },
  { label: '6M', value: '6mo' },
  { label: '1Y', value: '1y' },
]

interface Props {
  history: HistoryPoint[]
  period: string
  loading: boolean
  onPeriodChange: (period: string) => void
  currentPrice: number
}

function useTokens() {
  const [tokens, setTokens] = useState({ tick: '#888', border: '#222', surface: '#000', text: '#fff' })
  useEffect(() => {
    const update = () => {
      const css = getComputedStyle(document.documentElement)
      const t3 = css.getPropertyValue('--text-3').trim()
      const border = css.getPropertyValue('--border').trim()
      const surface = css.getPropertyValue('--surface').trim()
      const text = css.getPropertyValue('--text').trim()
      const toRgb = (v: string) => `rgb(${v.split(' ').join(',')})`
      setTokens({ tick: toRgb(t3), border: toRgb(border), surface: toRgb(surface), text: toRgb(text) })
    }
    update()
    const observer = new MutationObserver(update)
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    return () => observer.disconnect()
  }, [])
  return tokens
}

function CustomTooltip({ active, payload, label, tokens }: { active?: boolean; payload?: { value: number }[]; label?: string; tokens: ReturnType<typeof useTokens> }) {
  if (!active || !payload?.length) return null
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs"
      style={{ backgroundColor: tokens.surface, border: `1px solid ${tokens.border}`, color: tokens.text }}
    >
      <p className="text-[10px] opacity-60 mb-0.5 font-mono">{label}</p>
      <p className="font-mono tabular-nums">
        {formatCurrency(payload[0]?.value)}
      </p>
    </div>
  )
}

export default function PriceChart({ history, period, loading, onPeriodChange, currentPrice }: Props) {
  const tokens = useTokens()
  if (!history.length && !loading) return null

  const first = history[0]?.close ?? 0
  const isPositive = currentPrice >= first
  const lineColor = isPositive ? 'rgb(var(--green))' : 'rgb(var(--red))'
  const fillColor = isPositive ? 'rgb(var(--green) / 0.14)' : 'rgb(var(--red) / 0.14)'

  const minY = history.length ? Math.min(...history.map(h => h.low)) * 0.998 : 0
  const maxY = history.length ? Math.max(...history.map(h => h.high)) * 1.002 : 100

  const formatXAxis = (dateStr: string) => {
    const d = new Date(dateStr)
    if (period === '1wk') return d.toLocaleDateString('en-IN', { weekday: 'short' })
    if (period === '1mo' || period === '3mo') return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
    return d.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' })
  }

  return (
    <div className="card p-6">
      <div className="flex items-baseline justify-between mb-6">
        <div>
          <h3 className="section-title">Price history</h3>
          {history.length > 0 && (
            <p className="text-[11px] text-text-tertiary font-mono mt-1">
              {formatDate(history[0]?.date)} – {formatDate(history[history.length - 1]?.date)}
            </p>
          )}
        </div>
        <div className="flex items-center border border-border-subtle rounded-full overflow-hidden">
          {PERIODS.map(p => (
            <button
              key={p.value}
              onClick={() => onPeriodChange(p.value)}
              disabled={loading}
              className={clsx(
                'px-3 py-1.5 text-[11px] font-mono transition-colors',
                period === p.value
                  ? 'bg-text-primary text-bg-primary'
                  : 'text-text-tertiary hover:text-text-primary'
              )}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-bg-primary/60 backdrop-blur-sm z-10">
            <div className="w-4 h-4 border-2 border-text-tertiary border-t-transparent rounded-full animate-spin" />
          </div>
        )}
        <motion.div
          key={period}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={history} margin={{ top: 4, right: 4, left: -12, bottom: 0 }}>
              <defs>
                <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={lineColor} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="2 4" stroke={tokens.border} vertical={false} />
              <XAxis
                dataKey="date"
                tickFormatter={formatXAxis}
                tick={{ fontSize: 10, fill: tokens.tick, fontFamily: 'JetBrains Mono, monospace' }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[minY, maxY]}
                tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`}
                tick={{ fontSize: 10, fill: tokens.tick, fontFamily: 'JetBrains Mono, monospace' }}
                axisLine={false}
                tickLine={false}
                width={48}
              />
              <Tooltip content={<CustomTooltip tokens={tokens} />} />
              {first > 0 && (
                <ReferenceLine y={first} stroke={tokens.border} strokeDasharray="3 3" strokeWidth={1} />
              )}
              <Area
                type="monotone"
                dataKey="close"
                stroke={lineColor}
                strokeWidth={1.6}
                fill="url(#priceGradient)"
                dot={false}
                activeDot={{ r: 3.5, fill: lineColor, strokeWidth: 0 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
      </div>
    </div>
  )
}
