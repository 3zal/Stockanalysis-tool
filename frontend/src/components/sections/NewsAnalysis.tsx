import { ExternalLink, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react'
import { motion } from 'framer-motion'
import type { NewsArticle } from '@/types'
import clsx from 'clsx'

function SentimentIcon({ sentiment }: { sentiment: NewsArticle['sentiment'] }) {
  if (sentiment === 'positive') return <ArrowUpRight size={10} className="text-green" />
  if (sentiment === 'negative') return <ArrowDownRight size={10} className="text-red" />
  return <Minus size={10} className="text-text-tertiary" />
}

interface Props {
  articles: NewsArticle[]
}

export default function NewsAnalysis({ articles }: Props) {
  if (!articles.length) {
    return (
      <div className="card p-6 flex flex-col items-start gap-1 min-h-[180px]">
        <h3 className="section-title">News</h3>
        <p className="text-xs text-text-tertiary mt-auto">No recent news found.</p>
      </div>
    )
  }

  const positive = articles.filter(a => a.sentiment === 'positive').length
  const negative = articles.filter(a => a.sentiment === 'negative').length
  const neutral = articles.filter(a => a.sentiment === 'neutral').length

  return (
    <motion.div
      className="card p-6 space-y-4"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.05 }}
    >
      <div className="flex items-baseline justify-between">
        <h3 className="section-title">News flow</h3>
        <div className="flex items-center gap-3 text-[11px] font-mono tabular-nums">
          <span className="text-green">+{positive}</span>
          <span className="text-text-tertiary">{neutral}</span>
          <span className="text-red">−{negative}</span>
        </div>
      </div>

      <div className="flex h-[3px] overflow-hidden gap-[2px]">
        {positive > 0 && <div className="bg-accent-green" style={{ flex: positive }} />}
        {neutral > 0 && <div className="bg-bg-card-3" style={{ flex: neutral }} />}
        {negative > 0 && <div className="bg-accent-red" style={{ flex: negative }} />}
      </div>

      <div className="divide-y divide-border-subtle max-h-[460px] overflow-y-auto -mx-1">
        {articles.slice(0, 12).map((article, i) => (
          <motion.a
            key={i}
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 + i * 0.03 }}
            className="group flex items-start gap-3 py-3 px-1 hover:bg-bg-card-2 transition-colors"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <p className="text-[13px] text-text-primary leading-snug line-clamp-2 group-hover:underline underline-offset-2">
                  {article.title}
                </p>
                <ExternalLink size={10} className="text-text-tertiary shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <div className="flex items-center gap-2 mt-1.5 text-[10px] text-text-tertiary font-mono">
                <span>{article.source}</span>
                <span>·</span>
                <span>{article.published_relative}</span>
                <span className="ml-auto flex items-center gap-1">
                  <SentimentIcon sentiment={article.sentiment} />
                  <span className={clsx({
                    'text-green': article.sentiment === 'positive',
                    'text-red': article.sentiment === 'negative',
                    'text-text-tertiary': article.sentiment === 'neutral',
                  })}>
                    {(article.sentiment_score * 100).toFixed(0)}%
                  </span>
                </span>
              </div>
            </div>
          </motion.a>
        ))}
      </div>
    </motion.div>
  )
}
