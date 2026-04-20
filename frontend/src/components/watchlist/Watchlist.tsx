import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, BookmarkX, ArrowUp, ArrowDown, RefreshCw, ArrowUpRight } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useWatchlistStore } from '@/store/useWatchlistStore'
import { useUIStore } from '@/store/useUIStore'
import { getStockAnalysis } from '@/utils/api'
import { formatCurrency, formatPercent } from '@/utils/formatters'
import clsx from 'clsx'

interface QuoteCache {
  price: number
  change_pct: number
}

interface Props {
  onClose: () => void
}

export default function Watchlist({ onClose }: Props) {
  const { items, remove, fetchWatchlist, loading } = useWatchlistStore()
  const { showToast } = useUIStore()
  const navigate = useNavigate()
  const [quotes, setQuotes] = useState<Record<string, QuoteCache>>({})
  const [quoteLoading, setQuoteLoading] = useState(false)

  useEffect(() => { fetchWatchlist() }, [])

  const fetchQuotes = async () => {
    if (!items.length) return
    setQuoteLoading(true)
    const results = await Promise.allSettled(
      items.map(item => getStockAnalysis(item.ticker.replace('.NS', '').replace('.BO', '')))
    )
    const cache: Record<string, QuoteCache> = {}
    results.forEach((r, i) => {
      if (r.status === 'fulfilled') {
        cache[items[i].ticker] = { price: r.value.quote.price, change_pct: r.value.quote.change_pct }
      }
    })
    setQuotes(cache)
    setQuoteLoading(false)
  }

  useEffect(() => {
    if (items.length > 0) fetchQuotes()
  }, [items.length])

  const handleRemove = async (ticker: string, name: string) => {
    await remove(ticker)
    showToast(`Removed ${name} from watchlist`, 'info')
  }

  const handleNavigate = (ticker: string) => {
    const clean = ticker.replace('.NS', '').replace('.BO', '')
    onClose()
    navigate(`/stock/${clean}`)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 h-14 border-b border-border-subtle">
        <div className="flex items-baseline gap-2">
          <span className="font-display text-lg text-text-primary">Watchlist</span>
          {items.length > 0 && (
            <span className="font-mono text-xs text-text-tertiary">{items.length}</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {items.length > 0 && (
            <button
              onClick={fetchQuotes}
              disabled={quoteLoading}
              className="h-8 w-8 rounded-full flex items-center justify-center text-text-tertiary hover:text-text-primary hover:bg-bg-card-2 transition-colors"
              title="Refresh"
            >
              <RefreshCw size={13} className={clsx(quoteLoading && 'animate-spin')} />
            </button>
          )}
          <button
            onClick={onClose}
            className="h-8 w-8 rounded-full flex items-center justify-center text-text-tertiary hover:text-text-primary hover:bg-bg-card-2 transition-colors"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-5 space-y-3">
            {[0, 1, 2].map(i => <div key={i} className="shimmer h-14 rounded-lg" />)}
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-start gap-2 px-6 pt-12">
            <p className="font-display text-xl text-text-primary">Nothing saved yet.</p>
            <p className="text-xs text-text-tertiary leading-relaxed max-w-xs">
              Save stocks from the analysis page and they&apos;ll appear here for quick monitoring.
            </p>
          </div>
        ) : (
          <div>
            <AnimatePresence>
              {items.map((item, i) => {
                const q = quotes[item.ticker]
                const pos = q ? q.change_pct >= 0 : true
                return (
                  <motion.div
                    key={item.ticker}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className="group flex items-center gap-3 px-6 py-3 border-b border-border-subtle hover:bg-bg-card-2 cursor-pointer transition-colors"
                    onClick={() => handleNavigate(item.ticker)}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-mono text-text-primary">
                        {item.ticker.replace('.NS', '').replace('.BO', '')}
                      </p>
                      <p className="text-xs text-text-tertiary truncate">{item.name}</p>
                    </div>
                    {q ? (
                      <div className="text-right shrink-0">
                        <p className="text-sm font-mono tabular-nums text-text-primary">{formatCurrency(q.price)}</p>
                        <p className={clsx('text-[11px] font-mono tabular-nums flex items-center justify-end gap-0.5', pos ? 'text-green' : 'text-red')}>
                          {pos ? <ArrowUp size={9} /> : <ArrowDown size={9} />}
                          {formatPercent(Math.abs(q.change_pct), 2)}
                        </p>
                      </div>
                    ) : quoteLoading ? (
                      <div className="shrink-0 space-y-1">
                        <div className="shimmer w-16 h-4 rounded" />
                        <div className="shimmer w-10 h-3 rounded" />
                      </div>
                    ) : null}
                    <button
                      onClick={e => { e.stopPropagation(); handleRemove(item.ticker, item.name) }}
                      className="text-text-tertiary hover:text-red p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <BookmarkX size={13} />
                    </button>
                    <ArrowUpRight size={12} className="text-text-tertiary shrink-0" />
                  </motion.div>
                )
              })}
            </AnimatePresence>
          </div>
        )}
      </div>

      {items.length > 0 && (
        <div className="px-6 py-3 border-t border-border-subtle">
          <p className="text-[11px] text-text-tertiary font-mono">
            {items.length} stock{items.length !== 1 ? 's' : ''} tracked
          </p>
        </div>
      )}
    </div>
  )
}
