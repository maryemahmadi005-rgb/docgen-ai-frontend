import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'
import { useEffect } from 'react'
import Button from './Button'

export function Modal({ open, onClose, title, description, children, footer, width = 440 }) {
  useEffect(() => {
    if (!open) return
    const handleEsc = (e) => e.key === 'Escape' && onClose?.()
    window.addEventListener('keydown', handleEsc)
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', handleEsc)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={onClose}
            style={styles.overlay}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={{ type: 'spring', stiffness: 400, damping: 32 }}
            style={{ ...styles.modal, width }}
            role="dialog"
            aria-modal="true"
          >
            <div style={styles.header}>
              <div>
                <h3 style={styles.title}>{title}</h3>
                {description && <p style={styles.description}>{description}</p>}
              </div>
              <button onClick={onClose} style={styles.closeBtn} aria-label="Close dialog">
                <X size={18} />
              </button>
            </div>
            <div style={styles.body}>{children}</div>
            {footer && <div style={styles.footer}>{footer}</div>}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'primary',
  loading = false,
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      description={description}
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={loading}>
            {cancelLabel}
          </Button>
          <Button variant={variant} onClick={onConfirm} loading={loading}>
            {confirmLabel}
          </Button>
        </>
      }
    />
  )
}

const styles = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(4,5,6,0.65)',
    backdropFilter: 'blur(2px)',
    zIndex: 1000,
  },
  modal: {
    position: 'fixed',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    background: 'var(--bg-surface-raised)',
    border: '1px solid var(--border-default)',
    borderRadius: 'var(--radius-lg)',
    boxShadow: 'var(--shadow-lg)',
    zIndex: 1001,
    maxWidth: 'calc(100vw - 32px)',
    maxHeight: 'calc(100vh - 64px)',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    padding: '20px 20px 0 20px',
    gap: 12,
  },
  title: { fontSize: 16.5, fontWeight: 700, color: 'var(--text-primary)' },
  description: { fontSize: 13.5, color: 'var(--text-secondary)', marginTop: 6, lineHeight: 1.5 },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: 'var(--text-tertiary)',
    padding: 4,
    borderRadius: 6,
    flexShrink: 0,
  },
  body: { padding: 20, overflowY: 'auto' },
  footer: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: 8,
    padding: '0 20px 20px 20px',
  },
}
