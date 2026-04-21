import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Clock, X, ArrowUpRight } from 'lucide-react'
import SearchBar from '@/components/search/SearchBar'
import { getMarketOverview, getSearchHistory, clearSearchHistory } from '@/utils/api'
import { formatPercent } from '@/utils/formatters'
import type { MarketIndex } from '@/types'
import clsx from 'clsx'

const POPULAR = [
  { ticker: 'RELIANCE', label: 'Reliance Industries', sector: 'Energy' },
  { ticker: 'TCS', label: 'Tata Consultancy Services', sector: 'IT' },
  { ticker: 'HDFCBANK', label: 'HDFC Bank', sector: 'Banking' },
  { ticker: 'INFY', label: 'Infosys', sector: 'IT' },
  { ticker: 'ICICIBANK', label: 'ICICI Bank', sector: 'Banking' },
  { ticker: 'BAJFINANCE', label: 'Bajaj Finance', sector: 'NBFC' },
  { ticker: 'BHARTIARTL', label: 'Bharti Airtel', sector: 'Telecom' },
  { ticker: 'HINDUNILVR', label: 'Hindustan Unilever', sector: 'FMCG' },
  { ticker: 'ASIANPAINT', label: 'Asian Paints', sector: 'Paints' },
  { ticker: 'MARUTI', label: 'Maruti Suzuki', sector: 'Auto' },
]

interface HistoryItem { ticker: string; name: string; searched_at: string }

function IndexRow({ idx }: { idx: MarketIndex }) {
  const positive = idx.change_pct >= 0
  return (
    <div className="flex items-baseline justify-between py-3 border-b border-border-subtle last:border-0">
      <span className="text-sm text-text-secondary">{idx.index_name}</span>
      <div className="flex items-baseline gap-4">
        <span className="font-mono tabular-nums text-sm text-text-primary">
          {idx.price?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
        </span>
        <span className={clsx('font-mono tabular-nums text-xs w-16 text-right', positive ? 'text-green' : 'text-red')}>
          {formatPercent(idx.change_pct, 2, true)}
        </span>
      </div>
    </div>
  )
}

export default function Home() {
  const navigate = useNavigate()
  const [indices, setIndices] = useState<MarketIndex[]>([])
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [indicesLoading, setIndicesLoading] = useState(true)

  useEffect(() => {
    getMarketOverview()
      .then(setIndices)
      .catch(() => {})
      .finally(() => setIndicesLoading(false))

    getSearchHistory().then(setHistory).catch(() => {})
  }, [])

  const handleSelect = (ticker: string) => {
    navigate(`/stock/${ticker.replace('.NS', '').replace('.BO', '')}`)
  }

  const handleClearHistory = async () => {
    await clearSearchHistory().catch(() => {})
    setHistory([])
  }

  return (
    <div className="max-w-5xl mx-auto pt-16 pb-8">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-14 text-center"
      >
        <p className="eyebrow mb-4">Research tool for Indian equities</p>
        <h1 className="font-display text-5xl md:text-6xl text-text-primary tracking-tight leading-[1.02] mb-5">
          Evidence-based<br />
          <span className="italic text-text-secondary">stock analysis.</span>
        </h1>
        <p className="text-base text-text-secondary max-w-xl mx-auto leading-relaxed">
          A single view on any NSE or BSE listed company — fundamentals, technicals,
          analyst consensus, news sentiment, and a weighted composite score.
        </p>
      </motion.div>

      {/* Search */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.08 }}
        className="mb-16 max-w-2xl mx-auto"
      >
        <SearchBar onSelect={handleSelect} />
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-x-14 gap-y-14">
        {/* Popular / recent column */}
        <div className="lg:col-span-3 space-y-12">
          <section>
            <h2 className="eyebrow mb-4">Commonly researched</h2>
            <div className="border-t border-border-subtle">
              {POPULAR.map((s, i) => (
                <motion.button
                  key={s.ticker}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.12 + i * 0.02 }}
                  onClick={() => handleSelect(s.ticker)}
                  className="group w-full flex items-center justify-between py-3 border-b border-border-subtle hover:bg-bg-card-2 -mx-2 px-2 transition-colors"
                >
                  <div className="flex items-baseline gap-4 min-w-0">
                    <span className="font-mono text-sm text-text-primary w-24 shrink-0">{s.ticker}</span>
                    <span className="text-sm text-text-secondary truncate">{s.label}</span>
                  </div>
                  <div className="flex items-center gap-4 shrink-0">
                    <span className="text-xs text-text-tertiary hidden sm:block">{s.sector}</span>
                    <ArrowUpRight size={14} className="text-text-tertiary group-hover:text-text-primary transition-colors" />
                  </div>
                </motion.button>
              ))}
            </div>
          </section>

          {history.length > 0 && (
            <section>
              <div className="flex items-baseline justify-between mb-4">
                <h2 className="eyebrow flex items-center gap-1.5">
                  <Clock size={10} /> Recent
                </h2>
                <button
                  onClick={handleClearHistory}
                  className="text-[11px] text-text-tertiary hover:text-text-primary transition-colors flex items-center gap-1"
                >
                  <X size={10} /> Clear
                </button>
              </div>
              <div className="border-t border-border-subtle">
                {history.slice(0, 6).map(item => (
                  <button
                    key={item.ticker}
                    onClick={() => handleSelect(item.ticker)}
                    className="w-full flex items-center justify-between py-2.5 border-b border-border-subtle hover:bg-bg-card-2 -mx-2 px-2 transition-colors"
                  >
                    <div className="flex items-baseline gap-4 min-w-0">
                      <span className="font-mono text-sm text-text-primary w-24 shrink-0">
                        {item.ticker.replace('.NS', '').replace('.BO', '')}
                      </span>
                      <span className="text-sm text-text-secondary truncate">{item.name}</span>
                    </div>
                    <ArrowUpRight size={14} className="text-text-tertiary" />
                  </button>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Market column */}
        <div className="lg:col-span-2">
          <h2 className="eyebrow mb-4">Market today</h2>
          <div className="border-t border-border-subtle">
            {indicesLoading ? (
              [0, 1, 2, 3].map(i => (
                <div key={i} className="py-3 border-b border-border-subtle">
                  <div className="shimmer h-4 rounded w-full" />
                </div>
              ))
            ) : indices.length > 0 ? (
              indices.map(idx => <IndexRow key={idx.ticker} idx={idx} />)
            ) : (
              <p className="py-3 text-sm text-text-tertiary">Market data unavailable.</p>
            )}
          </div>

          <p className="mt-8 text-[11px] text-text-tertiary leading-relaxed">
            All data is pulled from public sources. Composite scores are generated from quantitative
            and AI-assisted signals and are for informational use only.
          </p>
        </div>
      </div>
    </div>
  )
}
