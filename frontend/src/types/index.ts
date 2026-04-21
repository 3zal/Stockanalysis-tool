export interface StockQuote {
  ticker: string
  name: string
  price: number
  change: number
  change_pct: number
  volume: number
  avg_volume: number
  market_cap: number
  week_52_high: number
  week_52_low: number
  day_high: number
  day_low: number
  open: number
  currency: string
  exchange: string
  sector: string
  industry: string
  website?: string
  description?: string
}

export interface Fundamentals {
  pe_ratio?: number
  forward_pe?: number
  peg_ratio?: number
  eps?: number
  eps_growth?: number
  revenue_growth?: number
  roe?: number
  roa?: number
  debt_to_equity?: number
  current_ratio?: number
  quick_ratio?: number
  profit_margin?: number
  operating_margin?: number
  gross_margin?: number
  dividend_yield?: number
  dividend_rate?: number
  book_value?: number
  price_to_book?: number
  price_to_sales?: number
  ev_to_ebitda?: number
  beta?: number
  shares_outstanding?: number
  free_cashflow?: number
  total_cash?: number
  total_debt?: number
  sector?: string
  employees?: number
}

export interface Technicals {
  rsi?: number
  rsi_signal?: 'oversold' | 'overbought' | 'neutral'
  macd?: number
  macd_signal?: number
  macd_hist?: number
  macd_bullish?: boolean
  ma20?: number
  ma50?: number
  ma200?: number
  price_vs_ma20?: number
  price_vs_ma50?: number
  price_vs_ma200?: number
  bb_upper?: number
  bb_lower?: number
  bb_position?: number
  volume_ratio?: number
  avg_volume_20d?: number
  trend?: 'bullish' | 'bearish'
  momentum?: 'positive' | 'negative'
}

export interface NewsArticle {
  title: string
  url: string
  source: string
  published: string
  published_relative: string
  summary: string
  sentiment: 'positive' | 'negative' | 'neutral'
  sentiment_score: number
  sentiment_details: {
    positive: number
    negative: number
    neutral: number
  }
  impact: 'high' | 'medium' | 'low'
}

export interface ScoreComponent {
  score: number
  weight: number
  label: string
  details?: unknown
}

export interface AnalystData {
  score: number
  num_analysts: number
  buy: number
  hold: number
  sell: number
  buy_pct: number
  hold_pct: number
  sell_pct: number
  consensus: string
  recommendation_mean: number
  target_price: number
  target_median: number
  upside_pct: number
  high_target: number
  low_target: number
  _cache_age_hours?: number
  _from_cache?: boolean
}

export interface MacroSignal {
  label: string
  value: string
  signal: 'positive' | 'neutral' | 'negative'
  year?: string | null
  source: string
}

export interface MacroData {
  score: number
  signals: MacroSignal[]
  gdp_growth?: number | null
  gdp_year?: string | null
  cpi?: number | null
  cpi_year?: string | null
  nifty_change_pct?: number | null
  nifty_vs_ma200?: number | null
  vix?: number | null
  _cache_age_hours?: number
  _from_cache?: boolean
  _stale?: boolean
}

export interface ScoreData {
  total: number
  recommendation: 'BUY' | 'HOLD' | 'SELL'
  rec_color: 'green' | 'amber' | 'red'
  confidence: number
  reasoning: string
  components: {
    fundamentals: ScoreComponent
    technicals: ScoreComponent
    news_sentiment: ScoreComponent
    market_sentiment: ScoreComponent
    analyst?: ScoreComponent & { details: AnalystData }
    macro?: ScoreComponent & { details: MacroData }
  }
}

export interface HistoryPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface Competitor {
  ticker: string
  name: string
  price: number
  change_pct: number
  market_cap: number
  pe_ratio: number
  price_to_book: number
  roe: number
  profit_margin: number
  revenue_growth: number
  beta: number
}

export interface StockAnalysis {
  ticker: string
  quote: StockQuote
  fundamentals: Fundamentals
  technicals: Technicals
  history: HistoryPoint[]
  news: NewsArticle[]
  score: ScoreData
  competitors: Competitor[]
  in_watchlist: boolean
}

export interface YearlyPoint {
  fy: string
  fy_year: number
  return_pct: number
  start_price: number
  end_price: number
  is_partial: boolean
}

export interface SearchResult {
  symbol: string
  ticker: string
  ticker_bse: string
  name: string
  exchange: string
  sector: string
}

export interface WatchlistItem {
  id: number
  ticker: string
  name: string
  added_at: string
}

export interface MarketIndex {
  ticker: string
  index_name: string
  price: number
  change: number
  change_pct: number
}
