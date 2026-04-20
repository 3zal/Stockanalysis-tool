import { motion } from 'framer-motion'
import type { ScoreData } from '@/types'
import SentimentGauge from '@/components/charts/SentimentGauge'
import clsx from 'clsx'

interface Props {
  score: ScoreData
}

function toneFor(s: number) {
  if (s >= 61) return { cssVar: '--green', className: 'text-green' as const }
  if (s >= 31) return { cssVar: '--yellow', className: 'text-yellow' as const }
  return { cssVar: '--red', className: 'text-red' as const }
}

function sentimentLabel(s: number): string {
  if (s >= 80) return 'Very bullish'
  if (s >= 61) return 'Bullish'
  if (s >= 50) return 'Mildly bullish'
  if (s >= 40) return 'Neutral'
  if (s >= 25) return 'Bearish'
  return 'Very bearish'
}

function Meter({ label, value }: { label: string; value: number }) {
  const tone = toneFor(value)
  return (
    <div className="py-2.5 border-b border-border-subtle last:border-0">
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="text-[12px] text-text-secondary">{label}</span>
        <span className={clsx('text-[12px] font-mono tabular-nums', tone.className)}>
          {value.toFixed(0)}
        </span>
      </div>
      <div className="h-[2px] rounded-full bg-bg-card-3 overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: `rgb(var(${tone.cssVar}))` }}
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.9, ease: 'easeOut', delay: 0.3 }}
        />
      </div>
    </div>
  )
}

function Signal({ label, value, tone }: { label: string; value: string; tone: 'pos' | 'neg' | 'neutral' }) {
  const toneClass = tone === 'pos' ? 'text-green' : tone === 'neg' ? 'text-red' : 'text-text-secondary'
  return (
    <div className="flex items-baseline justify-between py-2 border-b border-border-subtle last:border-0">
      <span className="text-[12px] text-text-tertiary">{label}</span>
      <span className={clsx('text-[12px] font-mono', toneClass)}>{value}</span>
    </div>
  )
}

export default function MarketSentiment({ score }: Props) {
  const sentiment = score.components.market_sentiment
  const news = score.components.news_sentiment
  const analyst = score.components.analyst
  const analystDetails = analyst?.details

  const gaugeScore = (sentiment.score / 100) * 2 - 1
  const newsGaugeScore = (news.score / 100) * 2 - 1

  const overall = Math.round((sentiment.score + news.score) / 2)
  const overallTone = toneFor(overall)

  const signals: { label: string; value: string; tone: 'pos' | 'neg' | 'neutral' }[] = []
  if (analystDetails) {
    const buyPct = analystDetails.buy_pct ?? 0
    signals.push({
      label: 'Analyst consensus',
      value: analystDetails.consensus || 'N/A',
      tone: buyPct >= 60 ? 'pos' : buyPct <= 30 ? 'neg' : 'neutral',
    })
    if (analystDetails.upside_pct !== undefined) {
      signals.push({
        label: 'Price upside',
        value: `${analystDetails.upside_pct >= 0 ? '+' : ''}${analystDetails.upside_pct.toFixed(1)}%`,
        tone: analystDetails.upside_pct >= 5 ? 'pos' : analystDetails.upside_pct <= -5 ? 'neg' : 'neutral',
      })
    }
  }
  signals.push({ label: 'Market mood', value: sentimentLabel(sentiment.score), tone: sentiment.score >= 55 ? 'pos' : sentiment.score <= 40 ? 'neg' : 'neutral' })
  signals.push({ label: 'News flow', value: sentimentLabel(news.score), tone: news.score >= 55 ? 'pos' : news.score <= 40 ? 'neg' : 'neutral' })
  if (score.components.macro) {
    signals.push({ label: 'Macro outlook', value: sentimentLabel(score.components.macro.score), tone: score.components.macro.score >= 55 ? 'pos' : score.components.macro.score <= 40 ? 'neg' : 'neutral' })
  }

  return (
    <motion.div
      className="card p-6 space-y-6"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.15 }}
    >
      <div className="flex items-baseline justify-between">
        <h3 className="section-title">Sentiment</h3>
        <span className={clsx('eyebrow', overallTone.className)} style={{ color: 'inherit' }}>
          {sentimentLabel(overall)}
        </span>
      </div>

      <div className="flex items-center justify-around py-2">
        <div className="flex flex-col items-center gap-1">
          <p className="eyebrow">Market</p>
          <SentimentGauge score={gaugeScore} size={96} />
        </div>
        <div className="w-px h-16 bg-border-subtle" />
        <div className="flex flex-col items-center gap-1">
          <p className="eyebrow">News</p>
          <SentimentGauge score={newsGaugeScore} size={96} />
        </div>
      </div>

      <div>
        <p className="eyebrow mb-2">Breakdown</p>
        <div className="border-t border-border-subtle">
          <Meter label="Market sentiment" value={sentiment.score} />
          <Meter label="News sentiment" value={news.score} />
          {score.components.macro && <Meter label="Macro outlook" value={score.components.macro.score} />}
        </div>
      </div>

      <div>
        <p className="eyebrow mb-2">Key signals</p>
        <div className="border-t border-border-subtle">
          {signals.map(sig => <Signal key={sig.label} {...sig} />)}
        </div>
      </div>
    </motion.div>
  )
}
