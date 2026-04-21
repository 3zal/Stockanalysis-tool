import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Bookmark, Search, X } from 'lucide-react'
import { useUIStore } from '@/store/useUIStore'
import { useWatchlistStore } from '@/store/useWatchlistStore'
import SearchBar from '@/components/search/SearchBar'
import { getMarketOverview } from '@/utils/api'
import type { MarketIndex } from '@/types'
import { formatPercent } from '@/utils/formatters'
import clsx from 'clsx'

export default function Header() {
  const { openWatchlist } = useUIStore()
  const { items: watchlistItems } = useWatchlistStore()
  const [showSearch, setShowSearch] = useState(false)
  const [indices, setIndices] = useState<MarketIndex[]>([])
  const navigate = useNavigate()

  useEffect(() => {
    getMarketOverview().then(setIndices).catch(() => {})
    const interval = setInterval(() => {
      getMarketOverview().then(setIndices).catch(() => {})
    }, 60000)
    return () => clearInterval(interval)
  }, [])

  const handleSelect = (ticker: string) => {
    setShowSearch(false)
    navigate(`/stock/${ticker.replace('.NS', '').replace('.BO', '')}`)
  }

  return (
    <header className="sticky top-0 z-30 w-full border-b border-border-subtle bg-bg-primary/85 backdrop-blur-xl">
      {/* Market ticker tape */}
      {indices.length > 0 && (
        <div className="border-b border-border-subtle px-4 md:px-6 lg:px-8 py-1.5 overflow-hidden">
          <div className="flex items-center gap-6 overflow-x-auto no-scrollbar text-[11px]">
            {indices.map((idx) => {
              const pos = (idx.change_pct ?? 0) >= 0
              return (
                <div key={idx.ticker} className="flex items-center gap-2 shrink-0">
                  <span className="font-medium text-text-tertiary">{idx.index_name}</span>
                  <span className="font-mono tabular-nums text-text-primary">
                    {idx.price?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </span>
                  <span className={clsx('font-mono tabular-nums', pos ? 'text-green' : 'text-red')}>
                    {formatPercent(idx.change_pct ?? 0, 2, true)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Main header */}
      <div className="flex items-center gap-4 px-4 md:px-6 lg:px-8 h-14">
        <Link to="/" className="flex items-baseline gap-1 shrink-0">
          <span className="font-display text-xl tracking-tight text-text-primary italic">investr</span>
          <span className="font-display text-xl tracking-tight text-text-tertiary">.info</span>
          <span className="hidden sm:inline ml-2 text-[10px] font-mono uppercase tracking-[0.18em] text-text-muted">
            NSE · BSE
          </span>
        </Link>

        <div className="flex-1 max-w-xl mx-auto hidden md:block">
          <SearchBar onSelect={handleSelect} compact />
        </div>

        <div className="ml-auto flex items-center gap-2">
          <button
            className="md:hidden h-8 w-8 rounded-full border border-border-subtle flex items-center justify-center text-text-secondary hover:text-text-primary hover:border-border-active transition-colors"
            onClick={() => setShowSearch(!showSearch)}
            aria-label="Search"
          >
            {showSearch ? <X size={14} /> : <Search size={14} />}
          </button>

          <button
            onClick={openWatchlist}
            className="h-8 px-3 rounded-full border border-border-subtle flex items-center gap-1.5 text-xs font-medium text-text-secondary hover:text-text-primary hover:border-border-active transition-colors"
            aria-label="Watchlist"
          >
            <Bookmark size={13} />
            <span className="hidden sm:inline">Watchlist</span>
            {watchlistItems.length > 0 && (
              <span className="font-mono text-[10px] text-text-tertiary">{watchlistItems.length}</span>
            )}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {showSearch && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="md:hidden border-t border-border-subtle overflow-hidden"
          >
            <div className="p-3">
              <SearchBar onSelect={(t) => { handleSelect(t); setShowSearch(false) }} autoFocus />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
