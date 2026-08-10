import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { GitPullRequestArrow, ChevronRight } from 'lucide-react'
import { useRepositoryContext } from '../repositories/RepositoryLayout'
import { pendingUpdatesApi } from '../../api/pendingUpdates'
import { getErrorMessage } from '../../api/client'
import { Card, Badge } from '../../components/ui/Primitives'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui/States'
import { formatDateTime, pendingStatusVariants, shortSha } from '../../utils/format'

const STATUS_FILTERS = ['pending', 'approved', 'rejected', 'stale', 'all']

export default function PendingUpdatesListPage() {
  const { repo } = useRepositoryContext()
  const [updates, setUpdates] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState('pending')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await pendingUpdatesApi.list(repo.id, statusFilter === 'all' ? null : statusFilter)
      setUpdates(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load pending updates.'))
    } finally {
      setLoading(false)
    }
  }, [repo.id, statusFilter])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div>
      <div style={styles.filterGroup}>
        {STATUS_FILTERS.map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            style={{ ...styles.filterBtn, ...(statusFilter === s ? styles.filterBtnActive : {}) }}
          >
            {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[1, 2].map((i) => <Skeleton key={i} height={72} radius={10} />)}
        </div>
      )}

      {!loading && error && <ErrorState description={error} onRetry={load} />}

      {!loading && !error && updates && updates.length === 0 && (
        <Card>
          <EmptyState
            icon={GitPullRequestArrow}
            title={statusFilter === 'pending' ? 'No pending updates' : `No ${statusFilter} updates`}
            description={
              statusFilter === 'pending'
                ? 'When changes are detected in this repository, proposed README updates will appear here for review.'
                : 'There are no updates with this status.'
            }
          />
        </Card>
      )}

      {!loading && !error && updates && updates.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {updates.map((u) => (
            <Link key={u.id} to={`/repositories/${repo.id}/pending-updates/${u.id}`} style={{ textDecoration: 'none' }}>
              <Card hoverable style={styles.row}>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={styles.rowTop}>
                    <Badge variant={pendingStatusVariants[u.status] || 'neutral'} dot>
                      {u.status}
                    </Badge>
                    <span style={styles.commitSha} className="mono">Commit {shortSha(u.commit_id)}</span>
                  </div>
                  <div style={styles.rowDate}>{formatDateTime(u.created_at)}</div>
                </div>
                <ChevronRight size={16} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

const styles = {
  filterGroup: { display: 'flex', gap: 4, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: 3, marginBottom: 18, width: 'fit-content', flexWrap: 'wrap' },
  filterBtn: { padding: '6px 12px', fontSize: 12.5, fontWeight: 600, color: 'var(--text-tertiary)', background: 'none', border: 'none', borderRadius: 6, whiteSpace: 'nowrap' },
  filterBtnActive: { background: 'var(--bg-surface-raised)', color: 'var(--text-primary)' },
  row: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, padding: 16 },
  rowTop: { display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' },
  commitSha: { fontSize: 12.5, color: 'var(--text-tertiary)' },
  rowDate: { fontSize: 12, color: 'var(--text-tertiary)', marginTop: 8 },
}
