import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, AlertCircle, RefreshCw } from 'lucide-react'
import { useStockStore } from '@/store/useStockStore'
import { useWatchlistStore } from '@/store/useWatchlistStore'
import Dashboard from '@/components/dashboard/Dashboard'
import { DashboardSkeleton } from '@/components/common/SkeletonLoader'

export default function StockPage() {
  const { ticker } = useParams<{ ticker: string }>()
  const navigate = useNavigate()
  const { data, loading, error, fetchStock, clear } = useStockStore()
  const { fetchWatchlist } = useWatchlistStore()

  useEffect(() => {
    if (!ticker) return
    clear()
    fetchStock(ticker.toUpperCase())
    fetchWatchlist()
  }, [ticker])

  if (loading) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 mt-6 text-xs text-text-tertiary hover:text-text-primary transition-colors"
        >
          <ArrowLeft size={12} /> Back
        </button>
        <DashboardSkeleton />
      </motion.div>
    )
  }

  if (error) {
    return (
      <motion.div
        className="flex flex-col items-start gap-6 pt-24 max-w-lg"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-2 text-red">
          <AlertCircle size={16} />
          <span className="eyebrow" style={{ color: 'inherit' }}>Unavailable</span>
        </div>
        <div>
          <h2 className="font-display text-3xl text-text-primary mb-2">
            Could not load {ticker?.toUpperCase()}
          </h2>
          <p className="text-sm text-text-secondary">{error}</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => navigate('/')} className="btn-ghost">
            <ArrowLeft size={13} /> Home
          </button>
          <button
            onClick={() => ticker && fetchStock(ticker.toUpperCase())}
            className="btn-primary"
          >
            <RefreshCw size={13} /> Retry
          </button>
        </div>
      </motion.div>
    )
  }

  if (!data) return null

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.2 }}>
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1.5 mt-6 text-xs text-text-tertiary hover:text-text-primary transition-colors"
      >
        <ArrowLeft size={12} /> Back
      </button>
      <Dashboard data={data} />
    </motion.div>
  )
}
