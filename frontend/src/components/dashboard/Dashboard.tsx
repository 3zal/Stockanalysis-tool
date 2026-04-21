import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Bookmark, BookmarkCheck, Share2, ArrowUp, ArrowDown } from 'lucide-react'
import type { StockAnalysis } from '@/types'
import { useStockStore } from '@/store/useStockStore'
import { useWatchlistStore } from '@/store/useWatchlistStore'
import { useUIStore } from '@/store/useUIStore'
import { formatCurrency, formatPercent, formatMarketCap } from '@/utils/formatters'
import ScoreCard from './ScoreCard'
import PriceChart from '@/components/charts/PriceChart'
import MarketData from '@/components/sections/MarketData'
import NewsAnalysis from '@/components/sections/NewsAnalysis'
import MarketSentiment from '@/components/sections/MarketSentiment'
import AIInsight from '@/components/sections/AIInsight'
import AnalystPredictions from '@/components/sections/AnalystPredictions'
import MacroOutlook from '@/components/sections/MacroOutlook'
import CompetitorComparison from '@/components/sections/CompetitorComparison'
import YearlyPerformance from '@/components/sections/YearlyPerformance'
import { getYearlyPerformance } from '@/utils/api'
import type { YearlyPoint } from '@/types'
import clsx from 'clsx'

interface Props {
  data: StockAnalysis
}

export default function Dashboard({ data }: Props) {
  const { quote, fundamentals, technicals, history, news, score, competitors } = data
  const { fetchHistory, historyPeriod, historyLoading, setWatchlist } = useStockStore()
  const { add, remove, isInWatchlist } = useWatchlistStore()
  const { showToast } = useUIStore()
  const [watchlistLoading, setWatchlistLoading] = useState(false)
  const [yearlyData, setYearlyData] = useState<YearlyPoint[]>([])
  const [yearlyLoading, setYearlyLoading] = useState(true)

  useEffect(() => {
    const ticker = data.ticker.replace('.NS', '').replace('.BO', '')
    setYearlyLoading(true)
    getYearlyPerformance(ticker)
      .then(setYearlyData)
      .catch(() => setYearlyData([]))
      .finally(() => setYearlyLoading(false))
  }, [data.ticker])

  const inWatchlist = isInWatchlist(data.ticker) || data.in_watchlist
  const positive = quote.change_pct >= 0

  const handleWatchlistToggle = async () => {
    setWatchlistLoading(true)
    try {
      if (inWatchlist) {
        await remove(data.ticker)
        setWatchlist(false)
        showToast(`Removed ${quote.name} from watchlist`, 'info')
      } else {
        await add(data.ticker, quote.name)
        setWatchlist(true)
        showToast(`Added ${quote.name} to watchlist`, 'success')
      }
    } catch {
      showToast('Failed to update watchlist', 'error')
    } finally {
      setWatchlistLoading(false)
    }
  }

  const handlePeriodChange = (period: string) => {
    fetchHistory(data.ticker.replace('.NS', '').replace('.BO', ''), period)
  }

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href)
    showToast('Link copied to clipboard', 'success')
  }

  const cleanTicker = data.ticker.replace('.NS', '').replace('.BO', '')

  return (
    <motion.div
      className="pt-8 space-y-10"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Masthead */}
      <div className="space-y-6 pb-6 border-b border-border-subtle">
        <div className="flex items-start justify-between gap-6 flex-wrap">
          <div className="space-y-2">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="font-mono text-xs text-text-tertiary tracking-wider">
                {cleanTicker} · {quote.exchange}
              </span>
              {quote.sector && <span className="text-xs text-text-tertiary">· {quote.sector}</span>}
              {quote.industry && <span className="text-xs text-text-tertiary hidden sm:inline">· {quote.industry}</span>}
            </div>
            <h1 className="font-display text-4xl md:text-5xl text-text-primary tracking-tight leading-[1.05]">
              {quote.name}
            </h1>
            {quote.market_cap > 0 && (
              <p className="text-xs text-text-tertiary">
                Market cap {formatMarketCap(quote.market_cap)}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleShare}
              className="h-9 w-9 rounded-full border border-border-subtle flex items-center justify-center text-text-secondary hover:text-text-primary hover:border-border-active transition-colors"
              title="Copy link"
            >
              <Share2 size={14} />
            </button>
            <button
              onClick={handleWatchlistToggle}
              disabled={watchlistLoading}
              className={clsx(
                'h-9 px-4 rounded-full border flex items-center gap-1.5 text-xs font-medium transition-colors',
                inWatchlist
                  ? 'border-border-active bg-bg-card-2 text-text-primary hover:bg-bg-card-3'
                  : 'border-border-subtle text-text-secondary hover:text-text-primary hover:border-border-active'
              )}
            >
              {inWatchlist ? <BookmarkCheck size={13} /> : <Bookmark size={13} />}
              {inWatchlist ? 'Saved' : 'Save'}
            </button>
          </div>
        </div>

        {/* Price */}
        <div className="flex items-end gap-6 flex-wrap">
          <div className="flex items-baseline gap-2">
            <span className="font-mono tabular-nums text-5xl md:text-6xl text-text-primary tracking-tight leading-none">
              {formatCurrency(quote.price)}
            </span>
            <span className="text-sm text-text-tertiary font-mono">{quote.currency}</span>
          </div>
          <div className={clsx('flex items-center gap-1 text-base font-mono tabular-nums', positive ? 'text-green' : 'text-red')}>
            {positive ? <ArrowUp size={16} /> : <ArrowDown size={16} />}
            {formatCurrency(Math.abs(quote.change))} ({formatPercent(Math.abs(quote.change_pct), 2, true)})
          </div>
          <div className="text-xs text-text-tertiary font-mono pb-1">
            Day {formatCurrency(quote.day_low)} – {formatCurrency(quote.day_high)}
          </div>
        </div>
      </div>

      <ScoreCard score={score} />

      <PriceChart
        history={history}
        period={historyPeriod}
        loading={historyLoading}
        onPeriodChange={handlePeriodChange}
        currentPrice={quote.price}
      />

      <YearlyPerformance data={yearlyData} loading={yearlyLoading} />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <MarketData quote={quote} fundamentals={fundamentals} technicals={technicals} />
        <NewsAnalysis articles={news} />
        <MarketSentiment score={score} />
        <AIInsight score={score} fundamentals={fundamentals} companyName={quote.name} />
        {score.components.macro && <MacroOutlook macro={score.components.macro.details} />}
        {score.components.analyst && (
          <AnalystPredictions analyst={score.components.analyst.details} currentPrice={quote.price} />
        )}
        {competitors.length > 0 && (
          <div className="md:col-span-2 xl:col-span-3">
            <CompetitorComparison competitors={competitors} currentTicker={data.ticker} quote={quote} />
          </div>
        )}
      </div>
    </motion.div>
  )
}
