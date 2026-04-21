import { motion } from 'framer-motion'
import type { MacroData } from '@/types'
import clsx from 'clsx'

interface Props {
  macro: MacroData
}

function toneClass(signal: 'positive' | 'neutral' | 'negative') {
  if (signal === 'positive') return 'text-green'
  if (signal === 'negative') return 'text-red'
  return 'text-text-secondary'
}

export default function MacroOutlook({ macro }: Props) {
  const cacheLabel = macro._cache_age_hours != null
    ? macro._cache_age_hours < 1
      ? 'Just updated'
      : macro._cache_age_hours < 24
        ? `Updated ${Math.round(macro._cache_age_hours)}h ago`
        : `Updated ${Math.round(macro._cache_age_hours / 24)}d ago`
    : ''

  return (
    <motion.div
      className="card p-6 space-y-5"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.25 }}
    >
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <h3 className="section-title">India macro</h3>
        <span className="text-[11px] text-text-tertiary font-mono">{cacheLabel}</span>
      </div>

      <div>
        <p className="eyebrow mb-2">Signals</p>
        <div className="border-t border-border-subtle">
          {macro.signals.map(sig => (
            <div
              key={sig.label}
              className="flex items-baseline justify-between py-2.5 border-b border-border-subtle last:border-0"
            >
              <div className="flex flex-col">
                <span className="text-[12px] text-text-secondary">{sig.label}</span>
                <span className="text-[10px] text-text-tertiary mt-0.5">
                  {sig.source}{sig.year ? ` · ${sig.year}` : ''}
                </span>
              </div>
              <span className={clsx('text-[12px] font-mono tabular-nums', toneClass(sig.signal))}>
                {sig.value}
              </span>
            </div>
          ))}
        </div>
      </div>

      <p className="text-[11px] text-text-tertiary leading-relaxed">
        Blended from World Bank (GDP, CPI) and NSE (NIFTY 50 trend, India VIX). Refreshed every 3 days.
      </p>
    </motion.div>
  )
}
