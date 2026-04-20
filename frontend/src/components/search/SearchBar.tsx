import { useState, useEffect, useRef, useCallback } from 'react'
import { Search, Clock, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { searchStocks, getSearchHistory } from '@/utils/api'
import type { SearchResult } from '@/types'
import clsx from 'clsx'

interface Props {
  onSelect: (ticker: string) => void
  compact?: boolean
  autoFocus?: boolean
}

export default function SearchBar({ onSelect, compact, autoFocus }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [history, setHistory] = useState<{ ticker: string; name: string }[]>([])
  const [loading, setLoading] = useState(false)
  const [focused, setFocused] = useState(false)
  const [activeIdx, setActiveIdx] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus()
  }, [autoFocus])

  useEffect(() => {
    getSearchHistory().then(setHistory).catch(() => {})
  }, [])

  const search = useCallback((q: string) => {
    if (!q.trim()) { setResults([]); return }
    setLoading(true)
    searchStocks(q)
      .then(setResults)
      .catch(() => setResults([]))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => search(query), 280)
    return () => clearTimeout(timerRef.current)
  }, [query, search])

  const showDropdown = focused && (query ? results.length > 0 || loading : history.length > 0)
  const dropdownItems = query
    ? results.map(r => ({ symbol: r.ticker, name: r.name, exchange: r.exchange, sector: r.sector }))
    : history.slice(0, 6).map(h => ({ symbol: h.ticker, name: h.name, exchange: '', sector: '' }))

  const handleSelect = (ticker: string) => {
    setQuery('')
    setResults([])
    setFocused(false)
    onSelect(ticker)
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (!showDropdown) return
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx(i => Math.min(i + 1, dropdownItems.length - 1)) }
    if (e.key === 'ArrowUp')   { e.preventDefault(); setActiveIdx(i => Math.max(i - 1, -1)) }
    if (e.key === 'Enter' && activeIdx >= 0) handleSelect(dropdownItems[activeIdx].symbol)
    if (e.key === 'Escape')    { setFocused(false); setQuery('') }
  }

  return (
    <div className="relative w-full">
      <div className={clsx(
        'flex items-center gap-2.5 rounded-full border bg-bg-primary transition-colors',
        compact ? 'h-9 px-3.5' : 'h-12 px-5',
        focused ? 'border-border-active' : 'border-border-subtle hover:border-border-active'
      )}>
        <Search size={compact ? 13 : 15} className="shrink-0 text-text-tertiary" />
        <input
          ref={inputRef}
          value={query}
          onChange={e => { setQuery(e.target.value); setActiveIdx(-1) }}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 150)}
          onKeyDown={handleKey}
          placeholder={compact ? 'Search stocks' : 'Search NSE or BSE by name or symbol'}
          className="flex-1 bg-transparent outline-none text-sm text-text-primary placeholder:text-text-tertiary"
        />
        {query && (
          <button onClick={() => { setQuery(''); setResults([]) }} className="text-text-tertiary hover:text-text-primary transition-colors">
            <X size={13} />
          </button>
        )}
        {!query && !compact && (
          <kbd className="hidden md:inline-flex items-center px-1.5 py-0.5 rounded-md border border-border-subtle text-[10px] text-text-tertiary font-mono">
            /
          </kbd>
        )}
      </div>

      <AnimatePresence>
        {showDropdown && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full mt-2 w-full bg-bg-primary border border-border-subtle rounded-2xl shadow-card-elevated overflow-hidden z-50"
          >
            {!query && history.length > 0 && (
              <div className="px-4 pt-3 pb-1 flex items-center">
                <span className="eyebrow">Recent</span>
              </div>
            )}
            {loading && (
              <div className="px-4 py-3 text-sm text-text-tertiary flex items-center gap-2">
                <div className="w-3 h-3 border-2 border-text-tertiary border-t-transparent rounded-full animate-spin" />
                Searching
              </div>
            )}
            {!loading && dropdownItems.length === 0 && query && (
              <div className="px-4 py-4 text-sm text-text-tertiary text-center">No results for &ldquo;{query}&rdquo;</div>
            )}
            {!loading && dropdownItems.map((item, i) => (
              <button
                key={`${item.symbol}-${i}`}
                onMouseDown={() => handleSelect(item.symbol)}
                className={clsx(
                  'w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors',
                  activeIdx === i ? 'bg-bg-card-2' : 'hover:bg-bg-card-2'
                )}
              >
                <span className="w-6 flex items-center justify-center shrink-0">
                  {!query ? (
                    <Clock size={12} className="text-text-tertiary" />
                  ) : (
                    <span className="text-[9px] font-mono text-text-tertiary">
                      {(item.exchange || '').slice(0, 3) || '—'}
                    </span>
                  )}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2">
                    <span className="text-sm font-medium font-mono text-text-primary">
                      {item.symbol.replace('.NS', '').replace('.BO', '')}
                    </span>
                    <span className="text-xs text-text-tertiary truncate">{item.name}</span>
                  </div>
                </div>
                {item.sector && (
                  <span className="text-[10px] text-text-tertiary shrink-0 hidden sm:block">{item.sector}</span>
                )}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
