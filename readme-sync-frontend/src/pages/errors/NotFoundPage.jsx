import { Link } from 'react-router-dom'
import { GitBranch, ArrowLeft } from 'lucide-react'
import Button from '../../components/ui/Button'

export default function NotFoundPage() {
  return (
    <div style={styles.wrap}>
      <div style={styles.icon}><GitBranch size={24} /></div>
      <div style={styles.code}>404</div>
      <h1 style={styles.title}>Page not found</h1>
      <p style={styles.description}>The page you're looking for doesn't exist or may have been moved.</p>
      <Link to="/dashboard">
        <Button icon={ArrowLeft}>Back to dashboard</Button>
      </Link>
    </div>
  )
}

const styles = {
  wrap: {
    minHeight: '100vh', display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: 24,
    background: 'var(--bg-canvas)',
  },
  icon: {
    width: 48, height: 48, borderRadius: 12, background: 'var(--bg-surface-raised)',
    color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20,
  },
  code: { fontSize: 13, fontWeight: 700, color: 'var(--accent)', fontFamily: 'var(--font-mono)', marginBottom: 8 },
  title: { fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' },
  description: { fontSize: 14, color: 'var(--text-secondary)', margin: '10px 0 26px 0', maxWidth: 380 },
}
