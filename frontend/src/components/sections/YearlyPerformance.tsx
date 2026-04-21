import { motion } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts'
import type { YearlyPoint } from '@/types'

interface Props {
  data: YearlyPoint[]
  loading: boolean
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: { payload: YearlyPoint }[] }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  const pos = d.return_pct >= 0
  return (
    <div className="bg-bg-card-2 border border-border-subtle rounded-xl p-3 text-xs space-y-1.5 shadow-lg">
      <p className="font-medium text-text-primary">{d.fy}</p>
      <p className={pos ? 'text-green font-mono' : 'text-red font-mono'}>
        {pos ? '+' : ''}{d.return_pct.toFixed(1)}%
      </p>
      <p className="text-text-tertiary font-mono">
        ₹{d.start_price.toLocaleString('en-IN')} → ₹{d.end_price.toLocaleString('en-IN')}
      </p>
    </div>
  )
}

function xLabel(fy: string) {
  if (fy.includes('YTD')) return 'YTD'
  const m = fy.match(/FY(\d{4})/)
  return m ? `FY${m[1].slice(2)}` : fy
}

export default function YearlyPerformance({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="card p-6 h-56 flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-border-subtle border-t-text-tertiary rounded-full animate-spin" />
      </div>
    )
  }

  if (!data.length) return null

  const complete = data.filter(d => !d.is_partial)
  const best  = Math.max(...data.map(d => d.return_pct))
  const worst = Math.min(...data.map(d => d.return_pct))
  const positiveYears = complete.filter(d => d.return_pct >= 0).length

  return (
    <motion.div
      className="card p-6 space-y-5"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.1 }}
    >
      <div className="flex items-baseline justify-between">
        <h3 className="section-title">Annual Returns</h3>
        <span className="eyebrow">Financial year · Apr – Mar</span>
      </div>

      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 12, right: 4, bottom: 0, left: -10 }} barCategoryGap="28%">
            <XAxis
              dataKey="fy"
              tickFormatter={xLabel}
              tick={{ fontSize: 10, fill: 'rgb(var(--text-3))' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: 'rgb(var(--text-3))' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: number) => `${v > 0 ? '+' : ''}${v}%`}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgb(var(--surface-3) / 0.6)' }} />
            <ReferenceLine y={0} stroke="rgb(var(--border-strong))" strokeWidth={1} />
            <Bar dataKey="return_pct" radius={[3, 3, 0, 0]} maxBarSize={36}>
              {data.map((d, i) => (
                <Cell
                  key={i}
                  fill={d.return_pct >= 0
                    ? 'rgb(40 200 64 / 0.8)'
                    : 'rgb(255 95 87 / 0.8)'}
                  stroke={d.is_partial
                    ? (d.return_pct >= 0 ? 'rgb(40 200 64)' : 'rgb(255 95 87)')
                    : 'none'}
                  strokeWidth={d.is_partial ? 1.5 : 0}
                  strokeDasharray={d.is_partial ? '3 2' : undefined}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border-subtle">
        <div>
          <p className="eyebrow mb-1">Best year</p>
          <p className="font-mono text-sm text-green">+{best.toFixed(1)}%</p>
        </div>
        <div>
          <p className="eyebrow mb-1">Worst year</p>
          <p className="font-mono text-sm text-red">{worst.toFixed(1)}%</p>
        </div>
        <div>
          <p className="eyebrow mb-1">Green years</p>
          <p className="font-mono text-sm text-text-primary">
            {positiveYears}/{complete.length}
          </p>
        </div>
      </div>
    </motion.div>
  )
}
