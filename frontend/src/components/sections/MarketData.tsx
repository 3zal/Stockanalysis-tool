import { motion } from 'framer-motion'
import type { StockQuote, Fundamentals, Technicals } from '@/types'
import { formatCurrency, formatPercent, formatMarketCap, formatNumber } from '@/utils/formatters'
import clsx from 'clsx'

function StatRow({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="flex items-baseline justify-between py-2 border-b border-border-subtle last:border-0">
      <span className="text-[12px] text-text-tertiary">{label}</span>
      <div className="text-right">
        <span className="text-[12px] font-mono tabular-nums text-text-primary">{value}</span>
        {sub && <span className="block text-[10px] text-text-tertiary font-mono">{sub}</span>}
      </div>
    </div>
  )
}

function TechChip({ label, value, tone }: { label: string; value: string; tone: 'pos' | 'neg' | 'neutral' }) {
  const toneClass =
    tone === 'pos' ? 'text-green' :
    tone === 'neg' ? 'text-red' :
    'text-text-secondary'
  return (
    <div className="py-2 px-3 border border-border-subtle rounded-md">
      <p className="text-[9px] text-text-tertiary uppercase tracking-[0.12em]">{label}</p>
      <p className={clsx('text-[12px] font-mono tabular-nums mt-0.5', toneClass)}>{value}</p>
    </div>
  )
}

interface Props {
  quote: StockQuote
  fundamentals: Fundamentals
  technicals: Technicals
}

export default function MarketData({ quote, fundamentals, technicals }: Props) {
  return (
    <motion.div
      className="card p-6 space-y-6"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
    >
      <div className="flex items-baseline justify-between">
        <h3 className="section-title">Market data</h3>
        <span className="eyebrow">Live</span>
      </div>

      <div>
        <p className="eyebrow mb-2">Price range</p>
        <div className="border-t border-border-subtle">
          <StatRow label="Open" value={formatCurrency(quote.open)} />
          <StatRow label="Day high" value={formatCurrency(quote.day_high)} />
          <StatRow label="Day low" value={formatCurrency(quote.day_low)} />
          <StatRow label="52W high" value={formatCurrency(quote.week_52_high)} />
          <StatRow label="52W low" value={formatCurrency(quote.week_52_low)} />
          <StatRow label="Volume" value={formatNumber(quote.volume)} sub={`Avg ${formatNumber(quote.avg_volume)}`} />
          <StatRow label="Market cap" value={formatMarketCap(quote.market_cap)} />
        </div>
      </div>

      <div>
        <p className="eyebrow mb-2">Fundamentals</p>
        <div className="border-t border-border-subtle">
          {fundamentals.pe_ratio != null && <StatRow label="P/E" value={fundamentals.pe_ratio.toFixed(2)} />}
          {fundamentals.forward_pe != null && <StatRow label="Forward P/E" value={fundamentals.forward_pe.toFixed(2)} />}
          {fundamentals.eps != null && <StatRow label="EPS" value={formatCurrency(fundamentals.eps)} />}
          {fundamentals.price_to_book != null && <StatRow label="P/B" value={fundamentals.price_to_book.toFixed(2)} />}
          {fundamentals.roe != null && <StatRow label="ROE" value={formatPercent(fundamentals.roe)} />}
          {fundamentals.debt_to_equity != null && <StatRow label="D/E" value={fundamentals.debt_to_equity.toFixed(2)} />}
          {fundamentals.profit_margin != null && <StatRow label="Profit margin" value={formatPercent(fundamentals.profit_margin)} />}
          {fundamentals.dividend_yield != null && fundamentals.dividend_yield > 0 && (
            <StatRow label="Div yield" value={formatPercent(fundamentals.dividend_yield)} />
          )}
          {fundamentals.beta != null && <StatRow label="Beta" value={fundamentals.beta.toFixed(2)} />}
        </div>
      </div>

      {(technicals.rsi != null || technicals.trend) && (
        <div>
          <p className="eyebrow mb-2">Technical signals</p>
          <div className="grid grid-cols-3 gap-1.5">
            {technicals.rsi != null && (
              <TechChip
                label="RSI"
                value={technicals.rsi.toFixed(0)}
                tone={technicals.rsi_signal === 'oversold' ? 'pos' : technicals.rsi_signal === 'overbought' ? 'neg' : 'neutral'}
              />
            )}
            {technicals.macd_bullish != null && (
              <TechChip label="MACD" value={technicals.macd_bullish ? 'Bullish' : 'Bearish'} tone={technicals.macd_bullish ? 'pos' : 'neg'} />
            )}
            {technicals.trend && (
              <TechChip label="Trend" value={technicals.trend === 'bullish' ? 'Up' : 'Down'} tone={technicals.trend === 'bullish' ? 'pos' : 'neg'} />
            )}
            {technicals.price_vs_ma50 != null && (
              <TechChip label="vs MA50" value={formatPercent(technicals.price_vs_ma50, 1, true)} tone={technicals.price_vs_ma50 > 0 ? 'pos' : 'neg'} />
            )}
            {technicals.volume_ratio != null && (
              <TechChip label="Vol ratio" value={`${technicals.volume_ratio.toFixed(1)}x`} tone={technicals.volume_ratio > 1 ? 'pos' : 'neutral'} />
            )}
            {technicals.momentum && (
              <TechChip label="Momentum" value={technicals.momentum === 'positive' ? 'Pos' : 'Neg'} tone={technicals.momentum === 'positive' ? 'pos' : 'neg'} />
            )}
          </div>
        </div>
      )}
    </motion.div>
  )
}
