import { motion } from 'framer-motion'
import { ArrowUp, ArrowDown } from 'lucide-react'
import type { ScoreData } from '@/types'
import { formatCurrency, formatPercent } from '@/utils/formatters'
import clsx from 'clsx'

interface Props {
  score: ScoreData
  currentPrice: number
}

function RatingBar({ label, pct, colorVar, count }: { label: string; pct: number; colorVar: string; count: number }) {
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="text-[12px] text-text-secondary w-10">{label}</span>
      <div className="flex-1 h-[2px] rounded-full bg-bg-card-3 overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: `rgb(var(${colorVar}))` }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.3 }}
        />
      </div>
      <span className="text-[11px] font-mono text-text-tertiary w-10 text-right tabular-nums">{pct.toFixed(0)}%</span>
      <span className="text-[11px] font-mono text-text-secondary w-6 text-right tabular-nums">{count}</span>
    </div>
  )
}

function Tier({ label, price, currentPrice, tone, delay }: { label: string; price: number; currentPrice: number; tone: 'green' | 'yellow' | 'red'; delay: number }) {
  const pct = currentPrice > 0 ? ((price - currentPrice) / currentPrice) * 100 : 0
  const isUp = pct >= 0
  const toneClass = tone === 'green' ? 'text-green' : tone === 'red' ? 'text-red' : 'text-yellow'

  return (
    <motion.div
      className="flex-1 py-3 border-t-2"
      style={{ borderColor: `rgb(var(--${tone === 'green' ? 'green' : tone === 'red' ? 'red' : 'yellow'}))` }}
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <p className="eyebrow mb-1.5">{label}</p>
      <p className={clsx('font-mono text-base tabular-nums', toneClass)}>{formatCurrency(price)}</p>
      <div className={clsx('flex items-center gap-0.5 mt-1 text-[11px] font-mono tabular-nums', isUp ? 'text-green' : 'text-red')}>
        {isUp ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
        {Math.abs(pct).toFixed(1)}%
      </div>
    </motion.div>
  )
}

export default function AnalystPredictions({ score, currentPrice }: Props) {
  const analysts = score.components.analyst.details
  if (!analysts) return null

  const upside = analysts.upside_pct
  const upsidePositive = upside >= 0
  const range = analysts.high_target - analysts.low_target
  const currentPct = range > 0
    ? Math.max(0, Math.min(100, ((currentPrice - analysts.low_target) / range) * 100))
    : 50

  const consensusTone =
    analysts.consensus === 'Buy' || analysts.consensus === 'Strong Buy' ? 'text-green' :
    analysts.consensus === 'Sell' || analysts.consensus === 'Strong Sell' ? 'text-red' :
    'text-yellow'

  return (
    <motion.div
      className="card p-6 space-y-6"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.1 }}
    >
      <div className="flex items-baseline justify-between">
        <h3 className="section-title">Analysts</h3>
        <span className="eyebrow">{analysts.num_analysts} covering</span>
      </div>

      <div className="flex items-baseline justify-between py-3 border-y border-border-subtle">
        <div>
          <p className="eyebrow mb-1">Consensus</p>
          <p className={clsx('font-display text-xl tracking-tight', consensusTone)}>
            {analysts.consensus}
          </p>
        </div>
        <div className="text-right">
          <p className="eyebrow mb-1">Upside</p>
          <p className={clsx('font-mono text-xl tabular-nums', upsidePositive ? 'text-green' : 'text-red')}>
            {formatPercent(Math.abs(upside), 1, true)}
          </p>
        </div>
      </div>

      <div>
        <p className="eyebrow mb-2">Rating distribution</p>
        <RatingBar label="Buy" pct={analysts.buy_pct} colorVar="--green" count={analysts.buy} />
        <RatingBar label="Hold" pct={analysts.hold_pct} colorVar="--yellow" count={analysts.hold} />
        <RatingBar label="Sell" pct={analysts.sell_pct} colorVar="--red" count={analysts.sell} />
      </div>

      {analysts.target_price > 0 && (
        <div>
          <p className="eyebrow mb-3">Price targets</p>
          <div className="flex gap-6">
            <Tier label="Bearish" price={analysts.low_target} currentPrice={currentPrice} tone="red" delay={0.3} />
            <Tier label="Base case" price={analysts.target_price} currentPrice={currentPrice} tone="yellow" delay={0.35} />
            <Tier label="Bullish" price={analysts.high_target} currentPrice={currentPrice} tone="green" delay={0.4} />
          </div>

          <div className="mt-4">
            <div className="relative h-[3px] rounded-full overflow-hidden bg-bg-card-3">
              <div
                className="absolute inset-y-0 left-0 rounded-full"
                style={{
                  width: '100%',
                  background: 'linear-gradient(90deg, rgb(var(--red)) 0%, rgb(var(--yellow)) 50%, rgb(var(--green)) 100%)',
                  opacity: 0.35,
                }}
              />
              <motion.div
                className="absolute top-[-4px] w-[2px] h-[11px] bg-text-primary rounded-full"
                style={{ left: `${currentPct}%` }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-text-tertiary font-mono mt-2">
              <span>{formatCurrency(analysts.low_target)}</span>
              <span className="text-text-secondary">Now {formatCurrency(currentPrice)}</span>
              <span>{formatCurrency(analysts.high_target)}</span>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  )
}
