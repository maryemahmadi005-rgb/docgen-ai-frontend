import { forwardRef, useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'

const Input = forwardRef(function Input(
  { label, error, hint, type = 'text', icon: Icon, style, id, ...props },
  ref
) {
  const [showPassword, setShowPassword] = useState(false)
  const isPassword = type === 'password'
  const actualType = isPassword && showPassword ? 'text' : type
  const inputId = id || props.name

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, width: '100%' }}>
      {label && (
        <label htmlFor={inputId} style={styles.label}>
          {label}
        </label>
      )}
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        {Icon && <Icon size={16} style={styles.leftIcon} />}
        <input
          ref={ref}
          id={inputId}
          type={actualType}
          style={{
            ...styles.input,
            paddingLeft: Icon ? 38 : 12,
            paddingRight: isPassword ? 40 : 12,
            borderColor: error ? 'var(--danger)' : 'var(--border-default)',
            ...style,
          }}
          onFocus={(e) => {
            e.target.style.borderColor = error ? 'var(--danger)' : 'var(--accent)'
            e.target.style.boxShadow = `0 0 0 3px ${error ? 'rgba(240,85,90,0.12)' : 'var(--accent-bg)'}`
          }}
          onBlur={(e) => {
            e.target.style.borderColor = error ? 'var(--danger)' : 'var(--border-default)'
            e.target.style.boxShadow = 'none'
          }}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword((s) => !s)}
            style={styles.eyeButton}
            tabIndex={-1}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
      {error && <span style={styles.errorText}>{error}</span>}
      {hint && !error && <span style={styles.hintText}>{hint}</span>}
    </div>
  )
})

const styles = {
  label: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--text-secondary)',
    letterSpacing: '-0.01em',
  },
  input: {
    width: '100%',
    height: 40,
    borderRadius: 'var(--radius-sm)',
    background: 'var(--bg-inset)',
    border: '1px solid var(--border-default)',
    color: 'var(--text-primary)',
    fontSize: 14,
    outline: 'none',
    transition: 'border-color 0.12s ease, box-shadow 0.12s ease',
  },
  leftIcon: {
    position: 'absolute',
    left: 12,
    color: 'var(--text-tertiary)',
    pointerEvents: 'none',
  },
  eyeButton: {
    position: 'absolute',
    right: 10,
    background: 'none',
    border: 'none',
    color: 'var(--text-tertiary)',
    display: 'flex',
    padding: 4,
  },
  errorText: {
    fontSize: 12.5,
    color: 'var(--danger)',
  },
  hintText: {
    fontSize: 12.5,
    color: 'var(--text-tertiary)',
  },
}

export default Input
