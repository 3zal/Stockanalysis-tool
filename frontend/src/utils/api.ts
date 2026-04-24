import axios from 'axios'
import type { StockAnalysis, SearchResult, WatchlistItem, MarketIndex, HistoryPoint, YearlyPoint } from '@/types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
  timeout: 65000,
})

export const searchStocks = async (query: string): Promise<SearchResult[]> => {
  const { data } = await api.get('/stocks/search', { params: { q: query } })
  return data.results
}

export const getStockAnalysis = async (ticker: string): Promise<StockAnalysis> => {
  const { data } = await api.get(`/stocks/${ticker}`)
  return data
}

export const getStockHistory = async (ticker: string, period: string): Promise<HistoryPoint[]> => {
  const { data } = await api.get(`/stocks/${ticker}/history`, { params: { period } })
  return data.history
}

export const getYearlyPerformance = async (ticker: string): Promise<YearlyPoint[]> => {
  const { data } = await api.get(`/stocks/${ticker}/yearly-performance`)
  return data.yearly_performance
}

export const getMarketOverview = async (): Promise<MarketIndex[]> => {
  const { data } = await api.get('/market/overview')
  return data.indices
}

export const getWatchlist = async (): Promise<WatchlistItem[]> => {
  const { data } = await api.get('/watchlist')
  return data.items
}

export const addToWatchlist = async (ticker: string, name: string): Promise<void> => {
  await api.post('/watchlist', { ticker, name })
}

export const removeFromWatchlist = async (ticker: string): Promise<void> => {
  await api.delete(`/watchlist/${ticker}`)
}

export const getSearchHistory = async (): Promise<{ ticker: string; name: string; searched_at: string }[]> => {
  const { data } = await api.get('/search-history')
  return data.items
}

export const clearSearchHistory = async (): Promise<void> => {
  await api.delete('/search-history')
}

export default api
