import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { GitPullRequestArrow, ChevronRight } from 'lucide-react'
import { repositoriesApi } from '../../api/repositories'
import { pendingUpdatesApi } from '../../api/pendingUpdates'
import { getErrorMessage } from '../../api/client'
import { Card, Badge } from '../../components/ui/Primitives'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui/States'
import PageHeader from '../../components/ui/PageHeader'
import { formatDateTime, pendingStatusVariants, shortSha } from '../../utils/format'

export default function GlobalPendingUpdatesPage() {
  const [items, setItems] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const repos = await repositoriesApi.list()
      const results = await Promise.all(
        repos.map(async (repo) => {
          try {
            const updates = await pendingUpdatesApi.list(repo.id, 'pending')
            return updates.map((u) => ({ ...u, repo }))
          } catch {
            return []
          }
        })
      )
      const flat = results.flat().sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      setItems(flat)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load pending updates.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div>
      <PageHeader
        title="Pending Updates"
        description="README proposals awaiting your review, across all repositories."
      />

      {loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[1, 2, 3].map((i) => <Skeleton key={i} height={76} radius={10} />)}
        </div>
      )}

      {!loading && error && <ErrorState description={error} onRetry={load} />}

      {!loading && !error && items && items.length === 0 && (
        <Card>
          <EmptyState
            icon={GitPullRequestArrow}
            title="Nothing pending review"
            description="When README changes are detected across your repositories, they'll appear here for approval."
          />
        </Card>
      )}

      {!loading && !error && items && items.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {items.map((u) => (
            <Link
              key={u.id}
              to={`/repositories/${u.repo.id}/pending-updates/${u.id}`}
              style={{ textDecoration: 'none' }}
            >
              <Card hoverable style={styles.row}>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={styles.rowTop}>
                    <span style={styles.repoName}>{u.repo.full_name}</span>
                    <Badge variant={pendingStatusVariants[u.status] || 'neutral'} dot>
                      {u.status}
                    </Badge>
                  </div>
                  <div style={styles.rowMeta}>
                    <span className="mono">Commit {shortSha(u.commit_id)}</span>
                    <span>·</span>
                    <span>{formatDateTime(u.created_at)}</span>
                  </div>
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
  row: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, padding: 16 },
  rowTop: { display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' },
  repoName: { fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' },
  rowMeta: { display: 'flex', gap: 6, fontSize: 12, color: 'var(--text-tertiary)', marginTop: 8, flexWrap: 'wrap' },
}
