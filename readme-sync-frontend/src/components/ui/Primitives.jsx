export function Card({ children, style, hoverable = false, onClick, ...props }) {
  return (
    <div
      onClick={onClick}
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: 20,
        transition: 'border-color 0.15s ease, transform 0.15s ease',
        cursor: onClick ? 'pointer' : 'default',
        ...style,
      }}
      onMouseEnter={(e) => {
        if (hoverable || onClick) e.currentTarget.style.borderColor = 'var(--border-strong)'
      }}
      onMouseLeave={(e) => {
        if (hoverable || onClick) e.currentTarget.style.borderColor = 'var(--border-subtle)'
      }}
      {...props}
    >
      {children}
    </div>
  )
}

const badgeVariants = {
  neutral: { bg: 'var(--bg-surface-raised)', color: 'var(--text-secondary)', border: 'var(--border-default)' },
  success: { bg: 'var(--success-bg)', color: 'var(--success)', border: 'var(--accent-border)' },
  warning: { bg: 'var(--warning-bg)', color: 'var(--warning)', border: 'rgba(233,185,73,0.28)' },
  danger: { bg: 'var(--danger-bg)', color: 'var(--danger)', border: 'rgba(240,85,90,0.28)' },
  info: { bg: 'var(--info-bg)', color: 'var(--info)', border: 'rgba(91,157,249,0.28)' },
}

export function Badge({ children, variant = 'neutral', dot = false, style }) {
  const v = badgeVariants[variant] || badgeVariants.neutral
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '3px 9px',
        borderRadius: 'var(--radius-full)',
        fontSize: 12,
        fontWeight: 600,
        letterSpacing: '-0.01em',
        background: v.bg,
        color: v.color,
        border: `1px solid ${v.border}`,
        whiteSpace: 'nowrap',
        ...style,
      }}
    >
      {dot && (
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: v.color,
            flexShrink: 0,
          }}
        />
      )}
      {children}
    </span>
  )
}

export function Spinner({ size = 20, color = 'var(--accent)' }) {
  return (
    <div
      className="spin"
      style={{
        width: size,
        height: size,
        border: `2px solid ${color}22`,
        borderTopColor: color,
        borderRadius: '50%',
      }}
    />
  )
}
