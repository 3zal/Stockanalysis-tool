import { motion } from 'framer-motion'
import type { ScoreData, Fundamentals } from '@/types'
import clsx from 'clsx'

interface Props {
  score: ScoreData
  fundamentals: Fundamentals
  companyName: string
}

function Point({ text, type }: { text: string; type: 'positive' | 'negative' | 'neutral' }) {
  const markerClass =
    type === 'positive' ? 'bg-accent-green' :
    type === 'negative' ? 'bg-accent-red' :
    'bg-text-tertiary'
  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-border-subtle last:border-0">
      <span className={clsx('w-[3px] h-[14px] rounded-full mt-[3px] shrink-0', markerClass)} />
      <p className="text-[13px] text-text-secondary leading-relaxed">{text}</p>
    </div>
  )
}

function buildPoints(score: ScoreData, fundamentals: Fundamentals) {
  const points: { text: string; type: 'positive' | 'negative' | 'neutral' }[] = []
  const f = score.components.fundamentals.score
  const t = score.components.technicals.score
  const n = score.components.news_sentiment.score
  const a = score.components.analyst.score

  if (f >= 65) points.push({ text: 'Strong fundamentals. Balance sheet and earnings quality support the current valuation.', type: 'positive' })
  else if (f < 40) points.push({ text: 'Weak fundamental indicators. Watch earnings momentum and debt levels.', type: 'negative' })
  else points.push({ text: 'Mixed fundamentals. Key ratios sit in acceptable ranges with no clear tailwind.', type: 'neutral' })

  if (t >= 65) points.push({ text: 'Technical setup is constructive. Price action and momentum align upward.', type: 'positive' })
  else if (t < 40) points.push({ text: 'Technicals point to near-term weakness. Wait for a confirmed reversal.', type: 'negative' })
  else points.push({ text: 'Technical picture is mixed. No clear directional conviction from the tape.', type: 'neutral' })

  if (n >= 65) points.push({ text: 'Positive news flow with constructive analyst commentary and press coverage.', type: 'positive' })
  else if (n < 40) points.push({ text: 'Negative news sentiment could create near-term headwinds.', type: 'negative' })

  if (a >= 65) points.push({ text: 'Sell-side is bullish with meaningful upside to consensus price target.', type: 'positive' })
  else if (a < 40) points.push({ text: 'Sell-side is cautious. Limited upside versus current valuation.', type: 'negative' })

  if (fundamentals.revenue_growth != null && fundamentals.revenue_growth > 0.15) {
    points.push({ text: `Revenue growth of ${(fundamentals.revenue_growth * 100).toFixed(1)}% signals business momentum.`, type: 'positive' })
  }

  return points.slice(0, 4)
}

export default function AIInsight({ score, fundamentals }: Props) {
  const macroScore = score.components.macro.score
  const points = buildPoints(score, fundamentals)
  const macroTone =
    macroScore >= 55 ? 'text-green' :
    macroScore < 40 ? 'text-red' :
    'text-yellow'

  return (
    <motion.div
      className="card p-6 space-y-5"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.2 }}
    >
      <h3 className="section-title">Assessment</h3>

      {score.reasoning && (
        <p className="text-[13px] text-text-secondary leading-relaxed">
          {score.reasoning}
        </p>
      )}

      <div>
        <p className="eyebrow mb-2">Key takeaways</p>
        <div className="border-t border-border-subtle">
          {points.map((pt, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 + i * 0.06 }}
            >
              <Point text={pt.text} type={pt.type} />
            </motion.div>
          ))}
        </div>
      </div>

      <div className="pt-4 border-t border-border-subtle">
        <div className="flex items-baseline justify-between">
          <p className="eyebrow">India macro</p>
          <span className={clsx('text-[13px] font-mono tabular-nums', macroTone)}>
            {macroScore.toFixed(0)} / 100
          </span>
        </div>
        <p className="text-[11px] text-text-tertiary mt-1.5 leading-relaxed">
          Composite of GDP growth, RBI stance, FII flows, and sector tailwinds.
          Simulated indicator based on current economic data, not financial advice.
        </p>
      </div>
    </motion.div>
  )
}
