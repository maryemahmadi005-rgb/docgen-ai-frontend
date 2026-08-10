import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, GitBranch } from 'lucide-react'
import { repositoriesApi } from '../../api/repositories'
import { getErrorMessage } from '../../api/client'
import { parseGithubUrl } from '../../utils/format'
import { useToast } from '../../context/ToastContext'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import { Card } from '../../components/ui/Primitives'

export default function AddRepositoryPage() {
  const navigate = useNavigate()
  const toast = useToast()

  const [githubUrl, setGithubUrl] = useState('')
  const [fullName, setFullName] = useState('')
  const [defaultBranch, setDefaultBranch] = useState('main')
  const [syncMode, setSyncMode] = useState('manual')
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState('')

  function handleUrlChange(value) {
    setGithubUrl(value)
    const parsed = parseGithubUrl(value)
    if (parsed) setFullName(parsed)
  }

  function validate() {
    const errs = {}
    if (!githubUrl.trim()) errs.githubUrl = 'GitHub URL is required'
    if (!fullName.trim()) errs.fullName = 'Repository name is required'
    else if (!/^[^/\s]+\/[^/\s]+$/.test(fullName.trim())) {
      errs.fullName = 'Use the owner/repo format, e.g. octocat/hello-world'
    }
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setApiError('')
    if (!validate()) return

    setLoading(true)
    try {
      const repo = await repositoriesApi.create({
        github_url: githubUrl.trim(),
        full_name: fullName.trim(),
        default_branch: defaultBranch.trim() || 'main',
        sync_mode: syncMode,
      })
      toast.success('Repository added.')
      navigate(`/repositories/${repo.id}`)
    } catch (err) {
      setApiError(getErrorMessage(err, 'Unable to add this repository.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 520 }}>
      <Link to="/repositories" style={styles.back}>
        <ArrowLeft size={14} /> Back to repositories
      </Link>

      <div style={styles.header}>
        <div style={styles.headerIcon}><GitBranch size={18} /></div>
        <div>
          <h1 style={styles.title}>Add a repository</h1>
          <p style={styles.subtitle}>Track a GitHub repository for README synchronization.</p>
        </div>
      </div>

      <Card>
        <form onSubmit={handleSubmit} style={styles.form} noValidate>
          <Input
            label="GitHub repository URL"
            placeholder="https://github.com/owner/repository"
            value={githubUrl}
            error={errors.githubUrl}
            onChange={(e) => handleUrlChange(e.target.value)}
            autoFocus
          />
          <Input
            label="Repository name"
            hint="owner/repo — auto-filled from the URL, editable if needed"
            placeholder="owner/repository"
            value={fullName}
            error={errors.fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
          <Input
            label="Default branch"
            placeholder="main"
            value={defaultBranch}
            onChange={(e) => setDefaultBranch(e.target.value)}
          />

          <div>
            <label style={styles.label}>Sync mode</label>
            <div style={styles.modeGroup}>
              <button
                type="button"
                onClick={() => setSyncMode('manual')}
                style={{ ...styles.modeCard, ...(syncMode === 'manual' ? styles.modeCardActive : {}) }}
              >
                <div style={styles.modeTitle}>Manual</div>
                <div style={styles.modeDesc}>Review changes before they apply.</div>
              </button>
              <button
                type="button"
                onClick={() => setSyncMode('automatic')}
                style={{ ...styles.modeCard, ...(syncMode === 'automatic' ? styles.modeCardActive : {}) }}
              >
                <div style={styles.modeTitle}>Automatic</div>
                <div style={styles.modeDesc}>Apply detected changes immediately.</div>
              </button>
            </div>
          </div>

          {apiError && <div style={styles.apiError}>{apiError}</div>}

          <Button type="submit" size="lg" loading={loading} style={{ width: '100%' }}>
            {loading ? 'Adding repository…' : 'Add repository'}
          </Button>
        </form>
      </Card>
    </div>
  )
}

const styles = {
  back: { display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 20 },
  header: { display: 'flex', alignItems: 'center', gap: 14, marginBottom: 24 },
  headerIcon: { width: 40, height: 40, borderRadius: 10, background: 'var(--accent-bg)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  title: { fontSize: 19, fontWeight: 800, letterSpacing: '-0.02em' },
  subtitle: { fontSize: 13, color: 'var(--text-secondary)', marginTop: 3 },
  form: { display: 'flex', flexDirection: 'column', gap: 18 },
  label: { fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 8 },
  modeGroup: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 },
  modeCard: { textAlign: 'left', padding: 14, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', background: 'var(--bg-inset)' },
  modeCardActive: { borderColor: 'var(--accent)', background: 'var(--accent-bg)' },
  modeTitle: { fontSize: 13.5, fontWeight: 700, color: 'var(--text-primary)' },
  modeDesc: { fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4, lineHeight: 1.4 },
  apiError: { fontSize: 13, color: 'var(--danger)', background: 'var(--danger-bg)', border: '1px solid rgba(240,85,90,0.25)', borderRadius: 'var(--radius-sm)', padding: '9px 12px' },
}
