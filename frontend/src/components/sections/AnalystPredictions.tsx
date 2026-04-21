import { motion } from 'framer-motion'
import type { AnalystData } from '@/types'
import { formatCurrency } from '@/utils/formatters'
import clsx from 'clsx'

interface Props {
  analyst: AnalystData
  currentPrice: number
}

function Bar({ label, pct, tone }: { label: string; pct: number; tone: 'pos' | 'neutral' | 'neg' }) {
  const barColor = tone === 'pos' ? 'bg-accent-green' : tone === 'neg' ? 'bg-accent-red' : 'bg-text-tertiary'
  const txtColor = tone === 'pos' ? 'text-green' : tone === 'neg' ? 'text-red' : 'text-text-secondary'
  return (
    <div className="py-2.5 border-b border-border-subtle last:border-0">
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="text-[12px] text-text-secondary">{label}</span>
        <span className={clsx('text-[12px] font-mono tabular-nums', txtColor)}>{pct.toFixed(0)}%</span>
      </div>
      <div className="h-[2px] bg-bg-card-3 rounded-full overflow-hidden">
        <motion.div
          className={clsx('h-full rounded-full', barColor)}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.2 }}
        />
      </div>
    </div>
  )
}

export default function AnalystPredictions({ analyst, currentPrice }: Props) {
  const { num_analysts, buy, hold, sell, buy_pct, hold_pct, sell_pct,
          consensus, target_price, upside_pct, high_target, low_target } = analyst

  const upsideTone = upside_pct > 0 ? 'text-green' : 'text-red'
  const cacheLabel = analyst._cache_age_hours != null
    ? analyst._cache_age_hours < 1
      ? 'Just updated'
      : analyst._cache_age_hours < 24
        ? `Updated ${Math.round(analyst._cache_age_hours)}h ago`
        : `Updated ${Math.round(analyst._cache_age_hours / 24)}d ago`
    : ''

  return (
    <motion.div
      className="card p-6 space-y-6 md:col-span-2 xl:col-span-3"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.1 }}
    >
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <h3 className="section-title">Analyst consensus</h3>
        <span className="text-[11px] text-text-tertiary font-mono">
          {num_analysts} analyst{num_analysts === 1 ? '' : 's'} · {cacheLabel} · Yahoo Finance
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        <div className="md:col-span-4 space-y-5">
          <div>
            <p className="eyebrow mb-2">Consensus</p>
            <p className="font-display text-3xl tracking-tight text-text-primary">{consensus}</p>
          </div>

          <div className="pt-4 border-t border-border-subtle">
            <p className="eyebrow mb-2">12-month target</p>
            <div className="flex items-baseline gap-2">
              <span className="font-mono tabular-nums text-3xl text-text-primary">
                {formatCurrency(target_price)}
              </span>
            </div>
            <p className={clsx('mt-1 text-sm font-mono', upsideTone)}>
              {upside_pct >= 0 ? '+' : ''}{upside_pct.toFixed(1)}% upside
            </p>
            <p className="text-[11px] text-text-tertiary mt-1">
              from {formatCurrency(currentPrice)}
            </p>
          </div>
        </div>

        <div className="md:col-span-4 space-y-5">
          <div>
            <p className="eyebrow mb-2">Breakdown</p>
            <div className="border-t border-border-subtle">
              <Bar label={`Buy · ${buy}`} pct={buy_pct} tone="pos" />
              <Bar label={`Hold · ${hold}`} pct={hold_pct} tone="neutral" />
              <Bar label={`Sell · ${sell}`} pct={sell_pct} tone="neg" />
            </div>
          </div>
        </div>

        <div className="md:col-span-4 space-y-5">
          <div>
            <p className="eyebrow mb-2">Target range</p>
            <div className="border-t border-border-subtle">
              <div className="flex items-baseline justify-between py-2.5 border-b border-border-subtle">
                <span className="text-[12px] text-text-secondary">High target</span>
                <span className="text-[12px] font-mono tabular-nums text-text-primary">
                  {formatCurrency(high_target)}
                </span>
              </div>
              <div className="flex items-baseline justify-between py-2.5 border-b border-border-subtle">
                <span className="text-[12px] text-text-secondary">Mean target</span>
                <span className="text-[12px] font-mono tabular-nums text-text-primary">
                  {formatCurrency(target_price)}
                </span>
              </div>
              <div className="flex items-baseline justify-between py-2.5">
                <span className="text-[12px] text-text-secondary">Low target</span>
                <span className="text-[12px] font-mono tabular-nums text-text-primary">
                  {formatCurrency(low_target)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
