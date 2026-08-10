import { createContext, useContext, useState, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, XCircle, Info, X } from 'lucide-react'

const ToastContext = createContext(null)

let idCounter = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const push = useCallback(
    (message, type = 'info', duration = 4000) => {
      const id = ++idCounter
      setToasts((prev) => [...prev, { id, message, type }])
      if (duration) {
        setTimeout(() => dismiss(id), duration)
      }
      return id
    },
    [dismiss]
  )

  const toast = {
    success: (msg, duration) => push(msg, 'success', duration),
    error: (msg, duration) => push(msg, 'error', duration),
    info: (msg, duration) => push(msg, 'info', duration),
  }

  const icons = {
    success: CheckCircle2,
    error: XCircle,
    info: Info,
  }

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div style={styles.container}>
        <AnimatePresence>
          {toasts.map((t) => {
            const Icon = icons[t.type]
            return (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, y: -12, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.15 } }}
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                style={{ ...styles.toast, ...styles[t.type] }}
              >
                <Icon size={17} style={{ flexShrink: 0 }} />
                <span style={styles.message}>{t.message}</span>
                <button
                  onClick={() => dismiss(t.id)}
                  style={styles.closeBtn}
                  aria-label="Dismiss notification"
                >
                  <X size={14} />
                </button>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}

const styles = {
  container: {
    position: 'fixed',
    top: 16,
    right: 16,
    zIndex: 9999,
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    maxWidth: 380,
    width: 'calc(100% - 32px)',
  },
  toast: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 10,
    padding: '12px 14px',
    borderRadius: 'var(--radius-md)',
    background: 'var(--bg-surface-raised)',
    border: '1px solid var(--border-default)',
    boxShadow: 'var(--shadow-lg)',
    fontSize: 13.5,
    color: 'var(--text-primary)',
  },
  success: { borderColor: 'var(--accent-border)', color: 'var(--accent)' },
  error: { borderColor: 'rgba(240,85,90,0.3)', color: 'var(--danger)' },
  info: { borderColor: 'rgba(91,157,249,0.3)', color: 'var(--info)' },
  message: { flex: 1, color: 'var(--text-primary)', lineHeight: 1.4, paddingTop: 1 },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: 'var(--text-tertiary)',
    padding: 2,
    display: 'flex',
    borderRadius: 4,
  },
}
