import { AlertTriangle, Inbox, RefreshCw } from 'lucide-react'
import Button from './Button'

export function EmptyState({ icon: Icon = Inbox, title, description, action }) {
  return (
    <div style={styles.wrap}>
      <div style={styles.iconWrap}>
        <Icon size={22} style={{ color: 'var(--text-tertiary)' }} />
      </div>
      <h4 style={styles.title}>{title}</h4>
      {description && <p style={styles.description}>{description}</p>}
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  )
}

export function ErrorState({ title = 'Something went wrong', description, onRetry }) {
  return (
    <div style={styles.wrap}>
      <div style={{ ...styles.iconWrap, background: 'var(--danger-bg)' }}>
        <AlertTriangle size={22} style={{ color: 'var(--danger)' }} />
      </div>
      <h4 style={styles.title}>{title}</h4>
      {description && <p style={styles.description}>{description}</p>}
      {onRetry && (
        <div style={{ marginTop: 16 }}>
          <Button variant="secondary" icon={RefreshCw} onClick={onRetry}>
            Try again
          </Button>
        </div>
      )}
    </div>
  )
}

export function Skeleton({ width = '100%', height = 16, radius = 6, style }) {
  return (
    <div
      className="pulse"
      style={{
        width,
        height,
        borderRadius: radius,
        background: 'var(--bg-surface-raised)',
        ...style,
      }}
    />
  )
}

export function SkeletonCard() {
  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: 20,
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
      }}
    >
      <Skeleton width="40%" height={14} />
      <Skeleton width="70%" height={20} />
      <Skeleton width="90%" height={12} />
      <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
        <Skeleton width={60} height={22} radius={999} />
        <Skeleton width={60} height={22} radius={999} />
      </div>
    </div>
  )
}

const styles = {
  wrap: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    textAlign: 'center',
    padding: '56px 24px',
  },
  iconWrap: {
    width: 44,
    height: 44,
    borderRadius: 'var(--radius-md)',
    background: 'var(--bg-surface-raised)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  title: { fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' },
  description: {
    fontSize: 13.5,
    color: 'var(--text-secondary)',
    marginTop: 6,
    maxWidth: 340,
    lineHeight: 1.55,
  },
}
