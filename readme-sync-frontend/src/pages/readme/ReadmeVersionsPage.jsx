import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { History, ChevronRight, FileText } from 'lucide-react'
import { useRepositoryContext } from '../repositories/RepositoryLayout'
import { readmesApi } from '../../api/readmes'
import { getErrorMessage } from '../../api/client'
import { Card, Badge } from '../../components/ui/Primitives'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui/States'
import { formatDateTime, triggeredByLabels, triggeredByVariants } from '../../utils/format'

export default function ReadmeVersionsPage() {
  const { repo } = useRepositoryContext()
  const [versions, setVersions] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notFound, setNotFound] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setNotFound(false)
    try {
      const data = await readmesApi.listVersions(repo.id)
      setVersions(data.sort((a, b) => b.version_number - a.version_number))
    } catch (err) {
      if (err?.response?.status === 404) setNotFound(true)
      else setError(getErrorMessage(err, 'Unable to load version history.'))
    } finally {
      setLoading(false)
    }
  }, [repo.id])

  useEffect(() => {
    load()
  }, [load])

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {[1, 2, 3].map((i) => <Skeleton key={i} height={64} radius={10} />)}
      </div>
    )
  }

  if (error) return <ErrorState description={error} onRetry={load} />

  if (notFound || !versions || versions.length === 0) {
    return (
      <Card>
        <EmptyState
          icon={History}
          title="No version history yet"
          description="README versions will appear here once the documentation has been generated or edited."
        />
      </Card>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {versions.map((v) => (
        <Link key={v.id} to={`/repositories/${repo.id}/versions/${v.version_number}`} style={{ textDecoration: 'none' }}>
          <Card hoverable style={styles.row}>
            <div style={styles.rowLeft}>
              <div style={styles.versionBadge}>v{v.version_number}</div>
              <div>
                <div style={styles.rowTitle}>
                  <Badge variant={triggeredByVariants[v.triggered_by] || 'neutral'}>
                    {triggeredByLabels[v.triggered_by] || v.triggered_by}
                  </Badge>
                </div>
                <div style={styles.rowDate}>{formatDateTime(v.created_at)}</div>
              </div>
            </div>
            <ChevronRight size={16} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />
          </Card>
        </Link>
      ))}
    </div>
  )
}

const styles = {
  row: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, padding: 16 },
  rowLeft: { display: 'flex', alignItems: 'center', gap: 14 },
  versionBadge: {
    width: 40, height: 40, borderRadius: 10, background: 'var(--bg-surface-raised)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 12.5, fontWeight: 800, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', flexShrink: 0,
  },
  rowTitle: { display: 'flex', gap: 6 },
  rowDate: { fontSize: 12, color: 'var(--text-tertiary)', marginTop: 6 },
}
