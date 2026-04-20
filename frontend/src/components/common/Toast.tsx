import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react'
import { useUIStore } from '@/store/useUIStore'
import clsx from 'clsx'

const VARIANTS = {
  success: { icon: CheckCircle2, iconClass: 'text-green' },
  error:   { icon: AlertCircle,  iconClass: 'text-red' },
  info:    { icon: Info,         iconClass: 'text-text-secondary' },
}

export default function Toast() {
  const { toast, clearToast } = useUIStore()

  return (
    <div className="fixed bottom-6 right-6 z-[200] pointer-events-none">
      <AnimatePresence>
        {toast && (
          <motion.div
            key={toast.message}
            initial={{ opacity: 0, y: 12, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.96 }}
            transition={{ type: 'spring', stiffness: 420, damping: 32 }}
            className="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-2xl border border-border-subtle bg-bg-primary shadow-card-elevated min-w-[240px] max-w-sm"
          >
            {(() => {
              const Icon = VARIANTS[toast.type].icon
              return <Icon size={15} className={clsx('shrink-0', VARIANTS[toast.type].iconClass)} />
            })()}
            <span className="text-[13px] text-text-primary flex-1 leading-snug">{toast.message}</span>
            <button
              onClick={clearToast}
              className="text-text-tertiary hover:text-text-primary transition-colors ml-1"
            >
              <X size={13} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
