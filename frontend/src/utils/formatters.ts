export const formatCurrency = (value: number, currency = 'INR', compact = false): string => {
  if (!value && value !== 0) return '—'
  if (compact) {
    if (Math.abs(value) >= 1e12) return `₹${(value / 1e12).toFixed(2)}T`
    if (Math.abs(value) >= 1e9) return `₹${(value / 1e9).toFixed(2)}B`
    if (Math.abs(value) >= 1e7) return `₹${(value / 1e7).toFixed(2)}Cr`
    if (Math.abs(value) >= 1e5) return `₹${(value / 1e5).toFixed(2)}L`
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(value)
}

export const formatNumber = (value: number, decimals = 2): string => {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
  }).format(value)
}

export const formatPercent = (value: number, decimals = 2, showSign = true): string => {
  if (value === null || value === undefined) return '—'
  const sign = showSign && value > 0 ? '+' : ''
  return `${sign}${value.toFixed(decimals)}%`
}

export const formatVolume = (value: number): string => {
  if (!value) return '—'
  if (value >= 1e7) return `${(value / 1e7).toFixed(2)}Cr`
  if (value >= 1e5) return `${(value / 1e5).toFixed(2)}L`
  if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`
  return value.toString()
}

export const formatMarketCap = (value: number): string => {
  if (!value) return '—'
  if (value >= 1e12) return `₹${(value / 1e12).toFixed(2)}T`
  if (value >= 1e9) return `₹${(value / 1e9).toFixed(2)}B`
  if (value >= 1e7) return `₹${(value / 1e7).toFixed(2)}Cr`
  return `₹${(value / 1e5).toFixed(2)}L`
}

export const formatDate = (dateStr: string): string => {
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric',
    })
  } catch {
    return dateStr
  }
}

export const getChangeColor = (value: number): string => {
  if (value > 0) return 'text-accent-green'
  if (value < 0) return 'text-accent-red'
  return 'text-text-secondary'
}

export const getScoreColor = (score: number): string => {
  if (score >= 61) return 'text-accent-green'
  if (score >= 31) return 'text-accent-amber'
  return 'text-accent-red'
}

export const getScoreBg = (score: number): string => {
  if (score >= 61) return 'bg-accent-green-dim border-accent-green/20'
  if (score >= 31) return 'bg-accent-amber-dim border-accent-amber/20'
  return 'bg-accent-red-dim border-accent-red/20'
}

export const getRecommendationColor = (rec: string): string => {
  switch (rec) {
    case 'BUY': return 'text-accent-green'
    case 'SELL': return 'text-accent-red'
    default: return 'text-accent-amber'
  }
}

export const clampScore = (score: number): number => Math.min(Math.max(score, 0), 100)

export const truncate = (str: string, length: number): string =>
  str.length > length ? str.slice(0, length) + '...' : str
