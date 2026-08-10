import { useState } from 'react'
import { Zap, Clock } from 'lucide-react'
import { useRepositoryContext } from './RepositoryLayout'
import { repositoriesApi } from '../../api/repositories'
import { getErrorMessage } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import { Card, Badge } from '../../components/ui/Primitives'
import Button from '../../components/ui/Button'

export default function RepositorySettingsPage() {
  const { repo, reloadRepo } = useRepositoryContext()
  const toast = useToast()
  const [selectedMode, setSelectedMode] = useState(repo.sync_mode)
  const [saving, setSaving] = useState(false)

  const hasChanges = selectedMode !== repo.sync_mode

  async function handleSave() {
    setSaving(true)
    try {
      await repositoriesApi.updateSyncMode(repo.id, selectedMode)
      await reloadRepo()
      toast.success('Sync mode updated.')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Unable to update sync mode.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ maxWidth: 640, display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Card>
        <h3 style={styles.title}>Synchronization mode</h3>
        <p style={styles.description}>
          Choose how README updates are applied when changes are detected in your repository.
        </p>

        <div style={styles.modeGroup}>
          <button
            onClick={() => setSelectedMode('manual')}
            style={{ ...styles.modeCard, ...(selectedMode === 'manual' ? styles.modeCardActive : {}) }}
          >
            <div style={styles.modeIcon}><Clock size={16} /></div>
            <div style={styles.modeTitle}>Manual</div>
            <div style={styles.modeDesc}>
              Review proposed README changes before they're applied. Each detected change
              becomes a pending update you approve or reject.
            </div>
          </button>
          <button
            onClick={() => setSelectedMode('automatic')}
            style={{ ...styles.modeCard, ...(selectedMode === 'automatic' ? styles.modeCardActive : {}) }}
          >
            <div style={styles.modeIcon}><Zap size={16} /></div>
            <div style={styles.modeTitle}>Automatic</div>
            <div style={styles.modeDesc}>
              README changes are applied automatically as soon as they're detected,
              without requiring approval.
            </div>
          </button>
        </div>

        <div style={styles.footer}>
          <Button onClick={handleSave} loading={saving} disabled={!hasChanges}>
            Save changes
          </Button>
        </div>
      </Card>

      <Card>
        <h3 style={styles.title}>Repository details</h3>
        <div style={styles.detailRow}>
          <span style={styles.detailLabel}>Tracked branch</span>
          <span className="mono" style={styles.detailValue}>{repo.tracked_branch || repo.default_branch}</span>
        </div>
        <div style={styles.detailRow}>
          <span style={styles.detailLabel}>Sync method</span>
          <Badge variant="neutral">{repo.sync_method}</Badge>
        </div>
        <div style={styles.detailRow}>
          <span style={styles.detailLabel}>GitHub URL</span>
          <a href={repo.github_url} target="_blank" rel="noreferrer" className="mono" style={styles.detailLink}>
            {repo.github_url}
          </a>
        </div>
      </Card>
    </div>
  )
}

const styles = {
  title: { fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' },
  description: { fontSize: 13, color: 'var(--text-secondary)', marginTop: 6, marginBottom: 18, lineHeight: 1.5 },
  modeGroup: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 },
  modeCard: { textAlign: 'left', padding: 16, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', background: 'var(--bg-inset)' },
  modeCardActive: { borderColor: 'var(--accent)', background: 'var(--accent-bg)' },
  modeIcon: { width: 30, height: 30, borderRadius: 8, background: 'var(--bg-surface-raised)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10 },
  modeTitle: { fontSize: 13.5, fontWeight: 700, color: 'var(--text-primary)' },
  modeDesc: { fontSize: 12, color: 'var(--text-tertiary)', marginTop: 6, lineHeight: 1.5 },
  footer: { display: 'flex', justifyContent: 'flex-end', marginTop: 18, paddingTop: 16, borderTop: '1px solid var(--border-subtle)' },
  detailRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border-subtle)', gap: 12 },
  detailLabel: { fontSize: 13, color: 'var(--text-secondary)' },
  detailValue: { fontSize: 13, color: 'var(--text-primary)' },
  detailLink: { fontSize: 12.5, color: 'var(--accent)', wordBreak: 'break-all', textAlign: 'right' },
}
