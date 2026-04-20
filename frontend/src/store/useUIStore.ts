import { create } from 'zustand'

interface UIState {
  sidebarOpen: boolean
  watchlistOpen: boolean
  toast: { message: string; type: 'success' | 'error' | 'info' } | null

  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  openWatchlist: () => void
  closeWatchlist: () => void
  showToast: (message: string, type?: 'success' | 'error' | 'info') => void
  clearToast: () => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  watchlistOpen: false,
  toast: null,

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  openWatchlist: () => set({ watchlistOpen: true }),
  closeWatchlist: () => set({ watchlistOpen: false }),

  showToast: (message, type = 'info') => {
    set({ toast: { message, type } })
    setTimeout(() => set({ toast: null }), 4000)
  },
  clearToast: () => set({ toast: null }),
}))
