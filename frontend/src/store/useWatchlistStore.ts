import { create } from 'zustand'
import type { WatchlistItem } from '@/types'
import { getWatchlist, addToWatchlist, removeFromWatchlist } from '@/utils/api'

interface WatchlistState {
  items: WatchlistItem[]
  loading: boolean

  fetchWatchlist: () => Promise<void>
  add: (ticker: string, name: string) => Promise<void>
  remove: (ticker: string) => Promise<void>
  isInWatchlist: (ticker: string) => boolean
}

export const useWatchlistStore = create<WatchlistState>((set, get) => ({
  items: [],
  loading: false,

  fetchWatchlist: async () => {
    set({ loading: true })
    try {
      const items = await getWatchlist()
      set({ items, loading: false })
    } catch {
      set({ loading: false })
    }
  },

  add: async (ticker, name) => {
    await addToWatchlist(ticker, name)
    await get().fetchWatchlist()
  },

  remove: async (ticker) => {
    await removeFromWatchlist(ticker)
    set((s) => ({ items: s.items.filter((i) => i.ticker !== ticker) }))
  },

  isInWatchlist: (ticker) => get().items.some((i) => i.ticker === ticker),
}))
