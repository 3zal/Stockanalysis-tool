import { motion } from 'framer-motion'
import type { ScoreData } from '@/types'
import clsx from 'clsx'

function scoreTone(score: number) {
  if (score >= 61) return { color: 'rgb(var(--green))', label: 'text-green', tier: 'Strong' }
  if (score >= 31) return { color: 'rgb(var(--yellow))', label: 'text-yellow', tier: 'Neutral' }
  return { color: 'rgb(var(--red))', label: 'text-red', tier: 'Weak' }
}

function ComponentBar({ label, score, weight, delay }: { label: string; score: number; weight: number; delay: number }) {
  const tone = scoreTone(score)
  return (
    <div className="py-2.5 border-b border-border-subtle last:border-0">
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="text-[13px] text-text-secondary">{label}</span>
        <div className="flex items-baseline gap-3">
          <span className="text-[11px] text-text-tertiary font-mono">{(weight * 100).toFixed(0)}%</span>
          <span className={clsx('text-[13px] font-mono tabular-nums w-8 text-right', tone.label)}>{score.toFixed(0)}</span>
        </div>
      </div>
      <div className="h-[2px] bg-bg-card-3 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: tone.color }}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.8, delay, ease: 'easeOut' }}
        />
      </div>
    </div>
  )
}

interface Props {
  score: ScoreData
}

export default function ScoreCard({ score }: Props) {
  const tone = scoreTone(score.total)
  const recTone = score.rec_color === 'green' ? 'text-green' : score.rec_color === 'red' ? 'text-red' : 'text-yellow'

  const allComponents = [
    { key: 'fundamentals', label: 'Fundamentals' },
    { key: 'technicals', label: 'Technicals' },
    { key: 'news_sentiment', label: 'News sentiment' },
    { key: 'market_sentiment', label: 'Market sentiment' },
    { key: 'analyst', label: 'Analyst ratings' },
    { key: 'macro', label: 'India macro' },
  ] as const
  const components = allComponents.filter(c => !!score.components[c.key])

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-x-10 gap-y-8">
      <div className="md:col-span-4">
        <p className="eyebrow mb-4">Composite score</p>
        <div className="flex items-baseline gap-2">
          <motion.span
            className="font-display text-[88px] leading-none tracking-tight"
            style={{ color: tone.color }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            {score.total}
          </motion.span>
          <span className="text-sm text-text-tertiary font-mono">/ 100</span>
        </div>
        <p className={clsx('mt-1 text-sm font-mono uppercase tracking-[0.18em]', tone.label)}>
          {tone.tier}
        </p>

        <div className="mt-6 pt-5 border-t border-border-subtle">
          <p className="eyebrow mb-2">Recommendation</p>
          <p className={clsx('font-display text-2xl tracking-tight', recTone)}>
            {score.recommendation}
          </p>
          <p className="mt-1 text-xs text-text-tertiary">
            Confidence <span className="font-mono text-text-secondary">{score.confidence}%</span>
          </p>
        </div>
      </div>

      <div className="md:col-span-8">
        <p className="eyebrow mb-2">Breakdown</p>
        <div className="border-t border-border-subtle">
          {components.map((c, i) => {
            const comp = score.components[c.key]!
            return (
              <ComponentBar
                key={c.key}
                label={c.label}
                score={comp.score}
                weight={comp.weight}
                delay={0.2 + i * 0.06}
              />
            )
          })}
        </div>

        {score.reasoning && (
          <div className="mt-6 pt-5 border-t border-border-subtle">
            <p className="eyebrow mb-2">AI assessment</p>
            <p className="text-sm text-text-secondary leading-relaxed">{score.reasoning}</p>
          </div>
        )}
      </div>
    </div>
  )
}
