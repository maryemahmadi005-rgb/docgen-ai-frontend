import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { GitBranch, GitPullRequestArrow, Zap, Clock, Plus, ArrowRight } from 'lucide-react'
import { repositoriesApi } from '../../api/repositories'
import { pendingUpdatesApi } from '../../api/pendingUpdates'
import { Card, Badge } from '../../components/ui/Primitives'
import { EmptyState, ErrorState, SkeletonCard } from '../../components/ui/States'
import Button from '../../components/ui/Button'
import PageHeader from '../../components/ui/PageHeader'
import { getErrorMessage } from '../../api/client'
import { timeAgo, shortSha } from '../../utils/format'

export default function DashboardPage() {
  const [repos, setRepos] = useState(null)
  const [pendingCounts, setPendingCounts] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    load()
  }, [])

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await repositoriesApi.list()
      setRepos(data)

      // Real data only: fetch pending counts per repo (no fake aggregate endpoint exists)
      const counts = {}
      await Promise.all(
        data.map(async (repo) => {
          try {
            const updates = await pendingUpdatesApi.list(repo.id, 'pending')
            counts[repo.id] = updates.length
          } catch {
            counts[repo.id] = 0
          }
        })
      )
      setPendingCounts(counts)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load your dashboard.'))
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div>
        <PageHeader title="Dashboard" description="Overview of your tracked repositories." />
        <div style={styles.statsGrid}>
          {[1, 2, 3, 4].map((i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    )
  }

  if (error) {
    return <ErrorState description={error} onRetry={load} />
  }

  const totalRepos = repos.length
  const automaticCount = repos.filter((r) => r.sync_mode === 'automatic').length
  const manualCount = repos.filter((r) => r.sync_mode === 'manual').length
  const totalPending = Object.values(pendingCounts).reduce((a, b) => a + b, 0)

  const recentRepos = [...repos]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5)

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of your tracked repositories."
        actions={
          <Link to="/repositories/new">
            <Button icon={Plus}>Add repository</Button>
          </Link>
        }
      />

      {totalRepos === 0 ? (
        <Card>
          <EmptyState
            icon={GitBranch}
            title="No repositories connected yet"
            description="Connect your first GitHub repository to start tracking documentation changes."
            action={
              <Link to="/repositories/new">
                <Button icon={Plus}>Connect repository</Button>
              </Link>
            }
          />
        </Card>
      ) : (
        <>
          <div style={styles.statsGrid}>
            <StatCard icon={GitBranch} label="Total repositories" value={totalRepos} />
            <StatCard icon={Zap} label="Automatic sync" value={automaticCount} accent />
            <StatCard icon={Clock} label="Manual sync" value={manualCount} />
            <StatCard icon={GitPullRequestArrow} label="Pending updates" value={totalPending} warn={totalPending > 0} />
          </div>

          <div style={styles.sectionHead}>
            <h3 style={styles.sectionTitle}>Recent repositories</h3>
            <Link to="/repositories" style={styles.viewAll}>
              View all <ArrowRight size={13} />
            </Link>
          </div>

          <div style={styles.repoList}>
            {recentRepos.map((repo) => (
              <Link key={repo.id} to={`/repositories/${repo.id}`} style={{ textDecoration: 'none' }}>
                <Card hoverable style={styles.repoRow}>
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={styles.repoName}>{repo.full_name}</div>
                    <div style={styles.repoMeta}>
                      <span className="mono">{repo.tracked_branch || repo.default_branch}</span>
                      {repo.last_synced_commit_sha && (
                        <>
                          <span>·</span>
                          <span className="mono">{shortSha(repo.last_synced_commit_sha)}</span>
                        </>
                      )}
                      <span>·</span>
                      <span>{timeAgo(repo.created_at)}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                    <Badge variant={repo.sync_mode === 'automatic' ? 'success' : 'neutral'} dot>
                      {repo.sync_mode === 'automatic' ? 'Automatic' : 'Manual'}
                    </Badge>
                    {pendingCounts[repo.id] > 0 && (
                      <Badge variant="warning">{pendingCounts[repo.id]} pending</Badge>
                    )}
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function StatCard({ icon: Icon, label, value, accent, warn }) {
  return (
    <Card>
      <div style={styles.statTop}>
        <div style={{ ...styles.statIcon, ...(accent ? styles.statIconAccent : {}) }}>
          <Icon size={16} />
        </div>
      </div>
      <div style={{ ...styles.statValue, ...(warn ? { color: 'var(--warning)' } : {}) }}>{value}</div>
      <div style={styles.statLabel}>{label}</div>
    </Card>
  )
}

const styles = {
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 14,
    marginBottom: 36,
  },
  statTop: { display: 'flex', marginBottom: 14 },
  statIcon: {
    width: 32, height: 32, borderRadius: 8,
    background: 'var(--bg-surface-raised)', color: 'var(--text-secondary)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  statIconAccent: { background: 'var(--accent-bg)', color: 'var(--accent)' },
  statValue: { fontSize: 26, fontWeight: 800, letterSpacing: '-0.03em', color: 'var(--text-primary)' },
  statLabel: { fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 4 },
  sectionHead: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 },
  sectionTitle: { fontSize: 15, fontWeight: 700 },
  viewAll: { fontSize: 13, fontWeight: 600, color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: 4 },
  repoList: { display: 'flex', flexDirection: 'column', gap: 8 },
  repoRow: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, padding: 16 },
  repoName: { fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' },
  repoMeta: { display: 'flex', gap: 6, fontSize: 12.5, color: 'var(--text-tertiary)', marginTop: 4, flexWrap: 'wrap' },
}
