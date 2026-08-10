import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ArrowLeft, RotateCcw } from 'lucide-react'
import { useRepositoryContext } from '../repositories/RepositoryLayout'
import { readmesApi } from '../../api/readmes'
import { getErrorMessage } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import { Card, Badge } from '../../components/ui/Primitives'
import { ErrorState, Skeleton } from '../../components/ui/States'
import { ConfirmDialog } from '../../components/ui/Modal'
import Button from '../../components/ui/Button'
import { formatDateTime, triggeredByLabels, triggeredByVariants } from '../../utils/format'

export default function ReadmeVersionDetailPage() {
  const { repo } = useRepositoryContext()
  const { versionNumber } = useParams()
  const navigate = useNavigate()
  const toast = useToast()

  const [version, setVersion] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [restoreOpen, setRestoreOpen] = useState(false)
  const [restoring, setRestoring] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await readmesApi.getVersion(repo.id, versionNumber)
      setVersion(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load this version.'))
    } finally {
      setLoading(false)
    }
  }, [repo.id, versionNumber])

  useEffect(() => {
    load()
  }, [load])

  async function handleRestore() {
    setRestoring(true)
    try {
      await readmesApi.rollbackToVersion(repo.id, versionNumber)
      toast.success(`Restored version ${versionNumber} as the current README.`)
      navigate(`/repositories/${repo.id}/readme`)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Unable to restore this version.'))
      setRestoring(false)
      setRestoreOpen(false)
    }
  }

  if (loading) {
    return (
      <div>
        <Skeleton width="30%" height={16} />
        <Skeleton width="100%" height={320} style={{ marginTop: 16 }} />
      </div>
    )
  }

  if (error || !version) return <ErrorState description={error} onRetry={load} />

  return (
    <div>
      <Link to={`/repositories/${repo.id}/versions`} style={styles.back}>
        <ArrowLeft size={14} /> Back to version history
      </Link>

      <div style={styles.header} className="rs-stack-mobile">
        <div>
          <div style={styles.headerRow}>
            <h2 style={styles.title}>Version {version.version_number}</h2>
            <Badge variant={triggeredByVariants[version.triggered_by] || 'neutral'}>
              {triggeredByLabels[version.triggered_by] || version.triggered_by}
            </Badge>
          </div>
          <div style={styles.date}>{formatDateTime(version.created_at)}</div>
        </div>
        <Button icon={RotateCcw} onClick={() => setRestoreOpen(true)}>
          Restore this version
        </Button>
      </div>

      <Card>
        <div className="rs-preview-body" style={{ fontSize: 13.5, lineHeight: 1.7 }}>
          {version.content_md?.trim() ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{version.content_md}</ReactMarkdown>
          ) : (
            <span style={{ color: 'var(--text-tertiary)' }}>This version has no content.</span>
          )}
        </div>
      </Card>

      <ConfirmDialog
        open={restoreOpen}
        onClose={() => setRestoreOpen(false)}
        onConfirm={handleRestore}
        loading={restoring}
        confirmLabel="Restore version"
        title={`Restore version ${version.version_number}?`}
        description="This will set this version's content as the current README. The full history is preserved — this action itself creates a new version entry."
      />
    </div>
  )
}

const styles = {
  back: { display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 20 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, gap: 12 },
  headerRow: { display: 'flex', alignItems: 'center', gap: 10 },
  title: { fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' },
  date: { fontSize: 12.5, color: 'var(--text-tertiary)', marginTop: 6 },
}
