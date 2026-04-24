import { create } from 'zustand'
import type { StockAnalysis, HistoryPoint } from '@/types'
import { getStockAnalysis, getStockHistory } from '@/utils/api'

interface StockState {
  data: StockAnalysis | null
  loading: boolean
  error: string | null
  historyPeriod: string
  historyLoading: boolean

  fetchStock: (ticker: string) => Promise<void>
  fetchHistory: (ticker: string, period: string) => Promise<void>
  setHistoryPeriod: (period: string) => void
  setWatchlist: (inWatchlist: boolean) => void
  clear: () => void
}

export const useStockStore = create<StockState>((set, get) => ({
  data: null,
  loading: false,
  error: null,
  historyPeriod: '6mo',
  historyLoading: false,

  fetchStock: async (ticker: string) => {
    set({ loading: true, error: null })
    const attempt = async () => getStockAnalysis(ticker)
    try {
      const data = await attempt()
      set({ data, loading: false })
    } catch (err: unknown) {
      const isTimeout = (err as { code?: string })?.code === 'ECONNABORTED' ||
        (err as Error)?.message?.toLowerCase().includes('timeout')
      if (isTimeout) {
        // auto-retry once on timeout (Render cold start)
        try {
          const data = await attempt()
          set({ data, loading: false })
          return
        } catch { /* fall through to error */ }
      }
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (err as Error)?.message ||
        'Failed to load stock data'
      set({ error: msg, loading: false })
    }
  },

  fetchHistory: async (ticker: string, period: string) => {
    set({ historyLoading: true })
    try {
      const history = await getStockHistory(ticker, period)
      const current = get().data
      if (current) {
        set({ data: { ...current, history }, historyLoading: false, historyPeriod: period })
      } else {
        set({ historyLoading: false })
      }
    } catch {
      set({ historyLoading: false })
    }
  },

  setHistoryPeriod: (period: string) => set({ historyPeriod: period }),

  setWatchlist: (inWatchlist: boolean) => {
    const current = get().data
    if (current) set({ data: { ...current, in_watchlist: inWatchlist } })
  },

  clear: () => set({ data: null, error: null, loading: false }),
}))
