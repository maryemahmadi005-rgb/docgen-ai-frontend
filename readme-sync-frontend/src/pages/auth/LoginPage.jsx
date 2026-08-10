import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { GitMerge, Mail, Lock, ArrowRight } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import AnimatedBackground from '../../components/intro/AnimatedBackground'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const fromIntro = location.state?.fromIntro === true
  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState('')

  function validate() {
    const errs = {}
    if (!form.email.trim()) errs.email = 'Email is required'
    else if (!/^\S+@\S+\.\S+$/.test(form.email)) errs.email = 'Enter a valid email'
    if (!form.password) errs.password = 'Password is required'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setApiError('')
    if (!validate()) return

    setLoading(true)
    const result = await login(form.email.trim().toLowerCase(), form.password)
    setLoading(false)

    if (result.success) {
      const redirectTo = location.state?.from?.pathname || '/dashboard'
      navigate(redirectTo, { replace: true })
    } else {
      setApiError(result.error)
    }
  }

  return (
    <div style={styles.page}>
      <AnimatedBackground intensity={0.5} />
      <motion.div
        initial={{ opacity: 0, y: fromIntro ? 18 : 12, scale: fromIntro ? 0.98 : 1 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: fromIntro ? 0.55 : 0.35, ease: [0.16, 1, 0.3, 1], delay: fromIntro ? 0.1 : 0 }}
        style={styles.card}
      >
        <Link to="/" style={styles.brand}>
          <div style={styles.brandMark}>
            <GitMerge size={18} strokeWidth={2.5} />
          </div>
          <span>README Sync</span>
        </Link>

        <h1 style={styles.title}>Welcome back</h1>
        <p style={styles.subtitle}>Sign in to manage your synchronized documentation.</p>

        <form onSubmit={handleSubmit} style={styles.form} noValidate>
          <Input
            label="Email"
            type="email"
            name="email"
            placeholder="you@company.com"
            icon={Mail}
            value={form.email}
            error={errors.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            autoComplete="email"
            autoFocus
          />
          <Input
            label="Password"
            type="password"
            name="password"
            placeholder="••••••••"
            icon={Lock}
            value={form.password}
            error={errors.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            autoComplete="current-password"
          />

          {apiError && <div style={styles.apiError}>{apiError}</div>}

          <Button type="submit" size="lg" loading={loading} iconRight={ArrowRight} style={{ width: '100%', marginTop: 4 }}>
            Sign in
          </Button>
        </form>

        <p style={styles.footerText}>
          Don't have an account? <Link to="/register" style={styles.link}>Create one</Link>
        </p>
      </motion.div>
    </div>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--bg-canvas)',
    padding: 20,
  },
  card: {
    position: 'relative',
    zIndex: 1,
    width: '100%',
    maxWidth: 380,
    background: 'var(--bg-surface)',
    border: '1px solid var(--border-subtle)',
    borderRadius: 'var(--radius-lg)',
    padding: 32,
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: 9,
    fontSize: 14.5,
    fontWeight: 700,
    color: 'var(--text-primary)',
    marginBottom: 28,
  },
  brandMark: {
    width: 28,
    height: 28,
    borderRadius: 8,
    background: 'var(--accent)',
    color: '#04120D',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: { fontSize: 21, fontWeight: 800, letterSpacing: '-0.03em' },
  subtitle: { fontSize: 13.5, color: 'var(--text-secondary)', marginTop: 6, marginBottom: 26 },
  form: { display: 'flex', flexDirection: 'column', gap: 16 },
  apiError: {
    fontSize: 13,
    color: 'var(--danger)',
    background: 'var(--danger-bg)',
    border: '1px solid rgba(240,85,90,0.25)',
    borderRadius: 'var(--radius-sm)',
    padding: '9px 12px',
  },
  footerText: {
    fontSize: 13,
    color: 'var(--text-tertiary)',
    textAlign: 'center',
    marginTop: 22,
  },
  link: { color: 'var(--accent)', fontWeight: 600 },
}
