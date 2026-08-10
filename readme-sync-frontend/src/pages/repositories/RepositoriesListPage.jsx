import { useEffect, useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Search, Plus, GitBranch, ExternalLink } from 'lucide-react'
import { repositoriesApi } from '../../api/repositories'
import { Card, Badge } from '../../components/ui/Primitives'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui/States'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import PageHeader from '../../components/ui/PageHeader'
import { getErrorMessage } from '../../api/client'
import { timeAgo, shortSha, toGithubUrl } from '../../utils/format'

export default function RepositoriesListPage() {
  const [repos, setRepos] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [syncModeFilter, setSyncModeFilter] = useState('all')

  useEffect(() => {
    load()
  }, [])

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await repositoriesApi.list()
      setRepos(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load repositories.'))
    } finally {
      setLoading(false)
    }
  }

  const filtered = useMemo(() => {
    if (!repos) return []
    return repos.filter((r) => {
      const matchesSearch = r.full_name.toLowerCase().includes(search.toLowerCase())
      const matchesMode = syncModeFilter === 'all' || r.sync_mode === syncModeFilter
      return matchesSearch && matchesMode
    })
  }, [repos, search, syncModeFilter])

  return (
    <div>
      <PageHeader
        title="Repositories"
        description="Manage the GitHub repositories you're tracking."
        actions={
          <Link to="/repositories/new">
            <Button icon={Plus}>Add repository</Button>
          </Link>
        }
      />

      {!loading && repos && repos.length > 0 && (
        <div style={styles.toolbar} className="rs-stack-mobile">
          <Input
            placeholder="Search repositories..."
            icon={Search}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ height: 36 }}
          />
          <div style={styles.filterGroup}>
            {['all', 'manual', 'automatic'].map((mode) => (
              <button
                key={mode}
                onClick={() => setSyncModeFilter(mode)}
                style={{
                  ...styles.filterBtn,
                  ...(syncModeFilter === mode ? styles.filterBtnActive : {}),
                }}
              >
                {mode === 'all' ? 'All' : mode === 'manual' ? 'Manual' : 'Automatic'}
              </button>
            ))}
          </div>
        </div>
      )}

      {loading && (
        <div style={styles.grid}>
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <Skeleton width="60%" height={16} />
              <Skeleton width="40%" height={12} style={{ marginTop: 10 }} />
            </Card>
          ))}
        </div>
      )}

      {!loading && error && <ErrorState description={error} onRetry={load} />}

      {!loading && !error && repos && repos.length === 0 && (
        <Card>
          <EmptyState
            icon={GitBranch}
            title="No repositories connected yet"
            description="Add a GitHub repository to start tracking its README."
            action={
              <Link to="/repositories/new">
                <Button icon={Plus}>Connect repository</Button>
              </Link>
            }
          />
        </Card>
      )}

      {!loading && !error && repos && repos.length > 0 && filtered.length === 0 && (
        <Card>
          <EmptyState title="No matches" description="No repositories match your search or filter." />
        </Card>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div style={styles.grid}>
          {filtered.map((repo) => (
            <Link key={repo.id} to={`/repositories/${repo.id}`} style={{ textDecoration: 'none' }}>
              <Card hoverable style={{ height: '100%' }}>
                <div style={styles.cardTop}>
                  <div style={styles.repoIcon}><GitBranch size={15} /></div>
                  <a
                    href={toGithubUrl(repo.full_name)}
                    target="_blank"
                    rel="noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    style={styles.externalLink}
                  >
                    <ExternalLink size={13} />
                  </a>
                </div>
                <div style={styles.repoName}>{repo.full_name}</div>
                <div style={styles.repoBranch} className="mono">
                  {repo.tracked_branch || repo.default_branch}
                </div>
                <div style={styles.badgeRow}>
                  <Badge variant={repo.sync_mode === 'automatic' ? 'success' : 'neutral'} dot>
                    {repo.sync_mode === 'automatic' ? 'Automatic' : 'Manual'}
                  </Badge>
                  <Badge variant="neutral">{repo.sync_method}</Badge>
                </div>
                <div style={styles.repoFooter}>
                  {repo.last_synced_commit_sha ? (
                    <span className="mono">Last commit {shortSha(repo.last_synced_commit_sha)}</span>
                  ) : (
                    <span>No commits synced yet</span>
                  )}
                  <span>·</span>
                  <span>Added {timeAgo(repo.created_at)}</span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

const styles = {
  toolbar: { display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' },
  filterGroup: { display: 'flex', gap: 4, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: 3, flexShrink: 0 },
  filterBtn: { padding: '6px 12px', fontSize: 12.5, fontWeight: 600, color: 'var(--text-tertiary)', background: 'none', border: 'none', borderRadius: 6, whiteSpace: 'nowrap' },
  filterBtnActive: { background: 'var(--bg-surface-raised)', color: 'var(--text-primary)' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 },
  cardTop: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 },
  repoIcon: { width: 30, height: 30, borderRadius: 8, background: 'var(--bg-surface-raised)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  externalLink: { color: 'var(--text-tertiary)', padding: 4, display: 'flex' },
  repoName: { fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', wordBreak: 'break-word' },
  repoBranch: { fontSize: 12.5, color: 'var(--text-tertiary)', marginTop: 4 },
  badgeRow: { display: 'flex', gap: 6, marginTop: 14 },
  repoFooter: { display: 'flex', gap: 6, fontSize: 12, color: 'var(--text-tertiary)', marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--border-subtle)', flexWrap: 'wrap' },
}
