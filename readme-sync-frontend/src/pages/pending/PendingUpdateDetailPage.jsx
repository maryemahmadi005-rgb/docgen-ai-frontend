import { useEffect, useState, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ArrowLeft, Check, X } from 'lucide-react'
import { useRepositoryContext } from '../repositories/RepositoryLayout'
import { pendingUpdatesApi } from '../../api/pendingUpdates'
import { getErrorMessage } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import { Card, Badge } from '../../components/ui/Primitives'
import { ErrorState, Skeleton } from '../../components/ui/States'
import { Modal, ConfirmDialog } from '../../components/ui/Modal'
import Button from '../../components/ui/Button'
import { formatDateTime, pendingStatusVariants, shortSha } from '../../utils/format'

export default function PendingUpdateDetailPage() {
  const { repo } = useRepositoryContext()
  const { updateId } = useParams()
  const navigate = useNavigate()
  const toast = useToast()

  const [update, setUpdate] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [approveOpen, setApproveOpen] = useState(false)
  const [approving, setApproving] = useState(false)
  const [rejectOpen, setRejectOpen] = useState(false)
  const [rejecting, setRejecting] = useState(false)
  const [rejectReason, setRejectReason] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await pendingUpdatesApi.get(repo.id, updateId)
      setUpdate(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load this pending update.'))
    } finally {
      setLoading(false)
    }
  }, [repo.id, updateId])

  useEffect(() => {
    load()
  }, [load])

  async function handleApprove() {
    setApproving(true)
    try {
      const updated = await pendingUpdatesApi.approve(repo.id, updateId)
      setUpdate(updated)
      toast.success('Update approved and applied to the README.')
      setApproveOpen(false)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Unable to approve this update.'))
    } finally {
      setApproving(false)
    }
  }

  async function handleReject() {
    setRejecting(true)
    try {
      const updated = await pendingUpdatesApi.reject(repo.id, updateId, rejectReason.trim() || undefined)
      setUpdate(updated)
      toast.success('Update rejected.')
      setRejectOpen(false)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Unable to reject this update.'))
    } finally {
      setRejecting(false)
    }
  }

  if (loading) {
    return (
      <div>
        <Skeleton width="30%" height={16} />
        <Skeleton width="100%" height={280} style={{ marginTop: 16 }} />
      </div>
    )
  }

  if (error || !update) return <ErrorState description={error} onRetry={load} />

  const isPending = update.status === 'pending'
  const sectionsDiff = update.sections_diff || {}
  const sectionNames = Object.keys(sectionsDiff)

  return (
    <div>
      <Link to={`/repositories/${repo.id}/pending-updates`} style={styles.back}>
        <ArrowLeft size={14} /> Back to pending updates
      </Link>

      <div style={styles.header} className="rs-stack-mobile">
        <div>
          <div style={styles.headerRow}>
            <h2 style={styles.title}>Documentation update proposal</h2>
            <Badge variant={pendingStatusVariants[update.status] || 'neutral'} dot>
              {update.status}
            </Badge>
          </div>
          <div style={styles.metaRow}>
            <span className="mono">Commit {shortSha(update.commit_id)}</span>
            <span>·</span>
            <span>{formatDateTime(update.created_at)}</span>
          </div>
        </div>

        {isPending && (
          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <Button variant="danger" icon={X} onClick={() => setRejectOpen(true)}>
              Reject
            </Button>
            <Button icon={Check} onClick={() => setApproveOpen(true)}>
              Approve
            </Button>
          </div>
        )}
      </div>

      {sectionNames.length > 0 && (
        <Card style={{ marginBottom: 14 }}>
          <div style={styles.sectionsLabel}>Affected sections</div>
          <div style={styles.sectionPills}>
            {sectionNames.map((s) => (
              <Badge key={s} variant="info">{s}</Badge>
            ))}
          </div>
        </Card>
      )}

      {sectionNames.length > 0 && (
        <Card style={{ marginBottom: 14 }}>
          <div style={styles.sectionsLabel}>Section changes</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 12 }}>
            {sectionNames.map((section) => {
              const diff = sectionsDiff[section]
              return (
                <div key={section}>
                  <div style={styles.diffSectionTitle}>{section}</div>
                  <div style={styles.diffGrid} className="rs-stack-mobile">
                    <div style={styles.diffCol}>
                      <div style={styles.diffColLabel}>Before</div>
                      <pre style={{ ...styles.diffPre, ...styles.diffBefore }}>
                        {formatDiffValue(diff?.before)}
                      </pre>
                    </div>
                    <div style={styles.diffCol}>
                      <div style={styles.diffColLabel}>After</div>
                      <pre style={{ ...styles.diffPre, ...styles.diffAfter }}>
                        {formatDiffValue(diff?.after)}
                      </pre>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      )}

      {update.proposed_content_md && (
        <Card>
          <div style={styles.sectionsLabel}>Proposed README</div>
          <div className="rs-preview-body" style={{ fontSize: 13.5, lineHeight: 1.7, marginTop: 10 }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{update.proposed_content_md}</ReactMarkdown>
          </div>
        </Card>
      )}

      <ConfirmDialog
        open={approveOpen}
        onClose={() => setApproveOpen(false)}
        onConfirm={handleApprove}
        loading={approving}
        confirmLabel="Approve update"
        title="Approve this update?"
        description="The proposed changes will be applied to the README immediately and a new version will be created."
      />

      <Modal
        open={rejectOpen}
        onClose={() => setRejectOpen(false)}
        title="Reject this update?"
        description="Why are you rejecting this update? This is optional but helps track decisions."
        footer={
          <>
            <Button variant="ghost" onClick={() => setRejectOpen(false)} disabled={rejecting}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleReject} loading={rejecting}>
              Reject update
            </Button>
          </>
        }
      >
        <textarea
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          placeholder="Optional reason…"
          style={styles.rejectTextarea}
        />
      </Modal>
    </div>
  )
}

function formatDiffValue(value) {
  if (value === undefined || value === null || value === '') return '(empty)'
  if (Array.isArray(value)) return value.map((v) => `- ${v}`).join('\n')
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

const styles = {
  back: { display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 20 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 18, gap: 12 },
  headerRow: { display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' },
  title: { fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' },
  metaRow: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: 'var(--text-tertiary)', marginTop: 8 },
  sectionsLabel: { fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' },
  sectionPills: { display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 10 },
  diffSectionTitle: { fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8, textTransform: 'capitalize' },
  diffGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 },
  diffCol: {},
  diffColLabel: { fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' },
  diffPre: {
    fontSize: 12.5, lineHeight: 1.6, padding: 12, borderRadius: 8, margin: 0,
    whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: 'var(--font-mono)',
    maxHeight: 220, overflowY: 'auto',
  },
  diffBefore: { background: 'rgba(240,85,90,0.06)', border: '1px solid rgba(240,85,90,0.18)', color: 'var(--text-secondary)' },
  diffAfter: { background: 'rgba(0,217,163,0.06)', border: '1px solid rgba(0,217,163,0.18)', color: 'var(--text-primary)' },
  rejectTextarea: {
    width: '100%', minHeight: 90, background: 'var(--bg-inset)', border: '1px solid var(--border-default)',
    borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontSize: 13.5, padding: 10,
    resize: 'vertical', outline: 'none', fontFamily: 'inherit', boxSizing: 'border-box',
  },
}
