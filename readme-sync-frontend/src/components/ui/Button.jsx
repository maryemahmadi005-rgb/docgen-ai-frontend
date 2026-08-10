import { forwardRef } from 'react'
import { Loader2 } from 'lucide-react'

const variants = {
  primary: {
    background: 'var(--accent)',
    color: '#04120D',
    border: '1px solid var(--accent)',
  },
  secondary: {
    background: 'var(--bg-surface-raised)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border-default)',
  },
  ghost: {
    background: 'transparent',
    color: 'var(--text-secondary)',
    border: '1px solid transparent',
  },
  danger: {
    background: 'var(--danger-bg)',
    color: 'var(--danger)',
    border: '1px solid rgba(240,85,90,0.3)',
  },
}

const sizes = {
  sm: { padding: '6px 12px', fontSize: 13, height: 30 },
  md: { padding: '8px 16px', fontSize: 13.5, height: 36 },
  lg: { padding: '10px 20px', fontSize: 14.5, height: 42 },
}

const Button = forwardRef(function Button(
  { variant = 'primary', size = 'md', loading = false, disabled, icon: Icon, iconRight: IconRight, children, style, ...props },
  ref
) {
  const isDisabled = disabled || loading

  return (
    <button
      ref={ref}
      disabled={isDisabled}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 7,
        borderRadius: 'var(--radius-sm)',
        fontWeight: 600,
        letterSpacing: '-0.01em',
        transition: 'all 0.12s ease',
        opacity: isDisabled ? 0.55 : 1,
        cursor: isDisabled ? 'not-allowed' : 'pointer',
        whiteSpace: 'nowrap',
        ...variants[variant],
        ...sizes[size],
        ...style,
      }}
      onMouseEnter={(e) => {
        if (isDisabled) return
        if (variant === 'primary') e.currentTarget.style.background = 'var(--accent-dim)'
        else if (variant === 'secondary') e.currentTarget.style.background = 'var(--bg-surface-hover)'
        else if (variant === 'ghost') e.currentTarget.style.background = 'var(--bg-surface-raised)'
      }}
      onMouseLeave={(e) => {
        if (isDisabled) return
        e.currentTarget.style.background = variants[variant].background
      }}
      {...props}
    >
      {loading ? (
        <Loader2 size={size === 'sm' ? 14 : 16} className="spin" />
      ) : (
        Icon && <Icon size={size === 'sm' ? 14 : 16} />
      )}
      {children}
      {!loading && IconRight && <IconRight size={size === 'sm' ? 14 : 16} />}
    </button>
  )
})

export default Button
