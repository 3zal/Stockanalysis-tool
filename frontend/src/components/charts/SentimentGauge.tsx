import { motion } from 'framer-motion'

interface Props {
  score: number  // -1 to 1
  size?: number
}

function polarToXY(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = (angleDeg * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

function arcPath(cx: number, cy: number, r: number, startDeg: number, endDeg: number) {
  const start = polarToXY(cx, cy, r, startDeg)
  const end = polarToXY(cx, cy, r, endDeg)
  const large = Math.abs(endDeg - startDeg) > 180 ? 1 : 0
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${large} 1 ${end.x} ${end.y}`
}

export default function SentimentGauge({ score, size = 120 }: Props) {
  const pct = (Math.max(-1, Math.min(1, score)) + 1) / 2
  const needleAngle = -180 + pct * 180

  const cx = 60, cy = 58, r = 40, strokeW = 4
  const needleLen = r - 4

  const sections = [
    { start: -180, end: -120, color: 'rgb(var(--red))' },
    { start: -120, end: -60, color: 'rgb(var(--yellow))' },
    { start: -60, end: 0, color: 'rgb(var(--green))' },
  ]

  const activeColor = score > 0.2 ? 'rgb(var(--green))' : score < -0.2 ? 'rgb(var(--red))' : 'rgb(var(--yellow))'
  const label = score > 0.2 ? 'Bullish' : score < -0.2 ? 'Bearish' : 'Neutral'
  const labelClass = score > 0.2 ? 'text-green' : score < -0.2 ? 'text-red' : 'text-yellow'
  const scorePercent = Math.round(pct * 100)

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size * 0.65} viewBox="0 0 120 78">
        {sections.map((s, i) => (
          <path
            key={i}
            d={arcPath(cx, cy, r, s.start, s.end)}
            fill="none"
            stroke={s.color}
            strokeWidth={strokeW}
            strokeLinecap="butt"
            opacity={0.22}
          />
        ))}

        <motion.path
          d={arcPath(cx, cy, r, -180, needleAngle)}
          fill="none"
          stroke={activeColor}
          strokeWidth={strokeW}
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.9, ease: 'easeOut', delay: 0.2 }}
        />

        <motion.g
          style={{ transformOrigin: `${cx}px ${cy}px` }}
          initial={{ rotate: -180 }}
          animate={{ rotate: needleAngle }}
          transition={{ duration: 1.1, type: 'spring', stiffness: 80, damping: 16, delay: 0.15 }}
        >
          <line
            x1={cx}
            y1={cy}
            x2={cx + needleLen}
            y2={cy}
            stroke={activeColor}
            strokeWidth={1.5}
            strokeLinecap="round"
          />
        </motion.g>

        <circle cx={cx} cy={cy} r={3} fill={activeColor} />
      </svg>

      <div className="text-center mt-1">
        <p className={`text-[13px] font-mono ${labelClass}`}>{label}</p>
        <p className="text-[10px] text-text-tertiary font-mono tabular-nums">{scorePercent}%</p>
      </div>
    </div>
  )
}
