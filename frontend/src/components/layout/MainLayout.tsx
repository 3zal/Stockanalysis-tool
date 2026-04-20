import { Outlet } from 'react-router-dom'
import Header from './Header'
import Watchlist from '@/components/watchlist/Watchlist'
import { useUIStore } from '@/store/useUIStore'
import { useWatchlistStore } from '@/store/useWatchlistStore'
import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function MainLayout() {
  const { watchlistOpen, closeWatchlist } = useUIStore()
  const { fetchWatchlist } = useWatchlistStore()

  useEffect(() => {
    fetchWatchlist()
  }, [])

  return (
    <div className="min-h-dvh flex flex-col bg-bg-primary">
      <Header />
      <main className="flex-1 w-full max-w-[1320px] mx-auto px-4 md:px-6 lg:px-8 pb-16">
        <Outlet />
      </main>

      <footer className="border-t border-border-subtle">
        <div className="max-w-[1320px] mx-auto px-4 md:px-6 lg:px-8 py-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-[11px] text-text-tertiary">
          <span className="font-mono uppercase tracking-[0.14em]">StockLens · Research Tool</span>
          <span>Data sourced from NSE India &amp; Twelve Data. Not financial advice.</span>
        </div>
      </footer>

      <AnimatePresence>
        {watchlistOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
              onClick={closeWatchlist}
            />
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 30, stiffness: 320 }}
              className="fixed top-0 right-0 h-full w-full max-w-sm z-50 bg-bg-primary border-l border-border-subtle"
            >
              <Watchlist onClose={closeWatchlist} />
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
