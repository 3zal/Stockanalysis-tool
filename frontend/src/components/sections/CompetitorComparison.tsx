import { motion } from 'framer-motion'
import { ArrowUp, ArrowDown } from 'lucide-react'
import type { Competitor, StockQuote } from '@/types'
import { formatCurrency, formatPercent, formatMarketCap } from '@/utils/formatters'
import { useNavigate } from 'react-router-dom'
import clsx from 'clsx'

interface Props {
  competitors: Competitor[]
  currentTicker: string
  quote: StockQuote
}

function Cell({ value, format, highlight }: { value: number | null | undefined; format: 'pct' | 'num' | 'currency'; highlight?: boolean }) {
  if (value == null || isNaN(value)) return <span className="text-text-tertiary font-mono text-xs">—</span>
  const formatted = format === 'pct' ? formatPercent(value, 1, true) :
    format === 'currency' ? formatCurrency(value) :
    value.toFixed(2)
  return (
    <span className={clsx('font-mono text-xs tabular-nums', highlight ? 'text-text-primary' : 'text-text-secondary')}>
      {formatted}
    </span>
  )
}

export default function CompetitorComparison({ competitors, currentTicker, quote }: Props) {
  const navigate = useNavigate()
  if (!competitors.length) return null

  const cleanTicker = (t: string) => t.replace('.NS', '').replace('.BO', '')
  const subject = cleanTicker(currentTicker)

  const allRows = [
    { ticker: subject, name: quote.name, price: quote.price, change_pct: quote.change_pct, market_cap: quote.market_cap, pe_ratio: null, price_to_book: null, roe: null, profit_margin: null, revenue_growth: null, beta: null } as Competitor & { isSubject: boolean },
    ...competitors.map(c => ({ ...c, isSubject: false })),
  ]

  return (
    <motion.div
      className="card p-6 space-y-5"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.2 }}
    >
      <div className="flex items-baseline justify-between">
        <h3 className="section-title">Peer comparison</h3>
        <span className="eyebrow">{competitors.length} peers</span>
      </div>

      <div className="overflow-x-auto -mx-1">
        <table className="w-full min-w-[620px] text-left">
          <thead>
            <tr className="border-b border-border-subtle">
              {['Company', 'Price', '1D', 'Mkt cap', 'P/E', 'P/B', 'ROE', 'Margin'].map(h => (
                <th key={h} className="eyebrow pb-3 pr-4 whitespace-nowrap font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {allRows.map((row, i) => {
              const isSubject = cleanTicker(row.ticker) === subject && i === 0
              const changePos = row.change_pct >= 0
              return (
                <motion.tr
                  key={row.ticker}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.15 + i * 0.04 }}
                  onClick={() => !isSubject && navigate(`/stock/${cleanTicker(row.ticker)}`)}
                  className={clsx('border-b border-border-subtle last:border-0 transition-colors', {
                    'bg-bg-card-2': isSubject,
                    'hover:bg-bg-card-2 cursor-pointer': !isSubject,
                  })}
                >
                  <td className="py-3 pr-4">
                    <p className={clsx('text-[13px] font-mono', isSubject ? 'text-text-primary font-semibold' : 'text-text-primary')}>
                      {cleanTicker(row.ticker)}
                    </p>
                    <p className="text-[11px] text-text-tertiary truncate max-w-[180px]">{row.name}</p>
                  </td>
                  <td className="py-3 pr-4">
                    <span className="text-xs font-mono text-text-secondary tabular-nums">{formatCurrency(row.price)}</span>
                  </td>
                  <td className="py-3 pr-4">
                    <span className={clsx('flex items-center gap-0.5 text-xs font-mono tabular-nums', changePos ? 'text-green' : 'text-red')}>
                      {changePos ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
                      {formatPercent(Math.abs(row.change_pct), 2)}
                    </span>
                  </td>
                  <td className="py-3 pr-4">
                    <span className="text-xs font-mono text-text-secondary tabular-nums">{formatMarketCap(row.market_cap)}</span>
                  </td>
                  <td className="py-3 pr-4"><Cell value={row.pe_ratio} format="num" highlight={isSubject} /></td>
                  <td className="py-3 pr-4"><Cell value={row.price_to_book} format="num" highlight={isSubject} /></td>
                  <td className="py-3 pr-4"><Cell value={row.roe != null ? row.roe * 100 : null} format="pct" highlight={isSubject} /></td>
                  <td className="py-3 pr-4"><Cell value={row.profit_margin != null ? row.profit_margin * 100 : null} format="pct" highlight={isSubject} /></td>
                </motion.tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}
