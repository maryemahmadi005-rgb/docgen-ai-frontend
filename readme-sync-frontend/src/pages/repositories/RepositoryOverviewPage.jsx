import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FileText, GitCommit, GitPullRequestArrow, History, Sparkles } from 'lucide-react'
import { useRepositoryContext } from './RepositoryLayout'
import { repositoriesApi } from '../../api/repositories'
import { getErrorMessage } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import { Card } from '../../components/ui/Primitives'
import Button from '../../components/ui/Button'
import { formatDateTime, shortSha } from '../../utils/format'

export default function RepositoryOverviewPage() {
  const { repo, reloadRepo } = useRepositoryContext()
  const [generating, setGenerating] = useState(false)
  const [generateError, setGenerateError] = useState(null)
  const toast = useToast()
  const navigate = useNavigate()

  async function handleGenerate() {
    setGenerating(true)
    setGenerateError(null)
    try {
      await repositoriesApi.generate(repo.id)
      await reloadRepo()
      toast.success('README generated.')
      navigate(`/repositories/${repo.id}/readme`)
    } catch (err) {
      setGenerateError(getErrorMessage(err, 'Unable to generate the README.'))
    } finally {
      setGenerating(false)
    }
  }

  const cards = [
    {
      icon: GitCommit,
      label: 'Last synced commit',
      value: repo.last_synced_commit_sha ? shortSha(repo.last_synced_commit_sha) : 'None yet',
      mono: !!repo.last_synced_commit_sha,
    },
    {
      icon: FileText,
      label: 'Tracked branch',
      value: repo.tracked_branch || repo.default_branch,
      mono: true,
    },
    {
      icon: History,
      label: 'Repository added',
      value: formatDateTime(repo.created_at),
    },
    {
      icon: GitPullRequestArrow,
      label: 'Sync method',
      value: repo.sync_method === 'webhook' ? 'Webhook' : 'Polling',
    },
  ]

  return (
    <div>
      <div style={styles.actionsRow}>
        <Button icon={Sparkles} onClick={handleGenerate} loading={generating}>
          {generating ? 'Generating…' : 'Generate README'}
        </Button>
        {generateError && <span style={styles.generateError}>{generateError}</span>}
      </div>

      <div style={styles.grid}>
        {cards.map(({ icon: Icon, label, value, mono }) => (
          <Card key={label}>
            <div style={styles.cardIcon}><Icon size={15} /></div>
            <div style={{ ...styles.cardValue, ...(mono ? { fontFamily: 'var(--font-mono)' } : {}) }}>
              {value}
            </div>
            <div style={styles.cardLabel}>{label}</div>
          </Card>
        ))}
      </div>

      <div style={styles.quickLinks}>
        <Link to={`/repositories/${repo.id}/readme`} style={{ textDecoration: 'none' }}>
          <Card hoverable>
            <div style={styles.quickTitle}>View README</div>
            <div style={styles.quickDesc}>Read and edit the current documentation.</div>
          </Card>
        </Link>
        <Link to={`/repositories/${repo.id}/pending-updates`} style={{ textDecoration: 'none' }}>
          <Card hoverable>
            <div style={styles.quickTitle}>Review pending updates</div>
            <div style={styles.quickDesc}>Approve or reject proposed README changes.</div>
          </Card>
        </Link>
        <Link to={`/repositories/${repo.id}/analysis`} style={{ textDecoration: 'none' }}>
          <Card hoverable>
            <div style={styles.quickTitle}>See analysis</div>
            <div style={styles.quickDesc}>Languages, frameworks and dependencies detected.</div>
          </Card>
        </Link>
      </div>
    </div>
  )
}

const styles = {
  actionsRow: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20, flexWrap: 'wrap' },
  generateError: { fontSize: 12.5, color: 'var(--danger)' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14, marginBottom: 28 },
  cardIcon: { width: 30, height: 30, borderRadius: 8, background: 'var(--bg-surface-raised)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 14 },
  cardValue: { fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', wordBreak: 'break-word' },
  cardLabel: { fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 },
  quickLinks: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 },
  quickTitle: { fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' },
  quickDesc: { fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 6, lineHeight: 1.5 },
}