import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  GitBranch,
  GitPullRequestArrow,
  ShieldCheck,
  Clock,
  Plus,
  ArrowRight,
  Sparkles,
} from 'lucide-react'
import { repositoriesApi } from '../../api/repositories'
import { useAuth } from '../../context/AuthContext'
import { useNotifications } from '../../context/NotificationsContext'
import { Card, Badge } from '../../components/ui/Primitives'
import { EmptyState, ErrorState, SkeletonCard, Skeleton } from '../../components/ui/States'
import Button from '../../components/ui/Button'
import { getErrorMessage } from '../../api/client'
import { timeAgo, shortSha, getGreeting, getDisplayName, deriveRepoStatus } from '../../utils/format'

export default function DashboardPage() {
  const { user } = useAuth()
  const { repoStates, events, loading: notifLoading } = useNotifications()

  const [repos, setRepos] = useState(null)
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
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load your dashboard.'))
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div>
        <Skeleton width={260} height={26} style={{ marginBottom: 8 }} />
        <Skeleton width={340} height={14} style={{ marginBottom: 28 }} />
        <div style={styles.statsGrid}>
          {[1, 2, 3, 4].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return <ErrorState description={error} onRetry={load} />
  }

  const statesByRepo = Object.fromEntries(repoStates.map((s) => [s.repository_id, s]))

  const totalRepos = repos.length
  const totalPending = repoStates.filter((s) => s.pending_prompt).length
  const reposNeedingReview = totalPending

  const syncHealth =
    totalRepos === 0 ? null : Math.round(((totalRepos - reposNeedingReview) / totalRepos) * 100)

  const lastSyncTimestamps = repoStates
    .map((s) => s.latest_version?.created_at)
    .filter(Boolean)
    .sort((a, b) => new Date(b) - new Date(a))
  const lastSync = lastSyncTimestamps[0] || null

  const recentRepos = [...repos]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5)

  const displayName = getDisplayName(user)

  return (
    <div>
      <div style={styles.header}>
        <div>
          <h1 style={styles.greeting}>
            {getGreeting()}{displayName ? `, ${displayName}` : ''} 👋
          </h1>
          <p style={styles.subtitle}>Here's what's happening with your repositories.</p>
        </div>
        <Link to="/repositories/new">
          <Button icon={Plus}>Connect repository</Button>
        </Link>
      </div>

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
            <StatCard icon={GitBranch} label="Repositories" value={totalRepos} />
            <StatCard
              icon={ShieldCheck}
              label={syncHealth === 100 ? 'All systems healthy' : 'Sync health'}
              value={syncHealth === null ? '—' : `${syncHealth}%`}
              accent={syncHealth === 100}
              warn={syncHealth !== null && syncHealth < 100}
            />
            <StatCard icon={Clock} label="Last sync" value={lastSync ? timeAgo(lastSync) : '—'} />
            <StatCard
              icon={GitPullRequestArrow}
              label="Pending updates"
              value={totalPending}
              warn={totalPending > 0}
            />
          </div>

          <div style={styles.twoCol} className="rs-stack-mobile">
            <div style={{ flex: 2, minWidth: 0 }}>
              <div style={styles.sectionHead}>
                <h3 style={styles.sectionTitle}>Recent repositories</h3>
                <Link to="/repositories" style={styles.viewAll}>
                  View all <ArrowRight size={13} />
                </Link>
              </div>

              <div style={styles.repoList}>
                {recentRepos.map((repo) => {
                  const status = deriveRepoStatus(statesByRepo[repo.id])
                  return (
                    <Link key={repo.id} to={`/repositories/${repo.id}`} style={{ textDecoration: 'none' }}>
                      <Card hoverable style={styles.repoRow}>
                        <div style={{ minWidth: 0, flex: 1 }}>
                          <div style={styles.repoTop}>
                            <span style={styles.repoName}>{repo.full_name}</span>
                            <Badge variant={repo.sync_mode === 'automatic' ? 'success' : 'neutral'} dot>
                              {repo.sync_mode === 'automatic' ? 'Automatic' : 'Manual'}
                            </Badge>
                          </div>
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
                        <Badge variant={status.variant}>{status.label}</Badge>
                      </Card>
                    </Link>
                  )
                })}
              </div>
            </div>

            <div style={{ flex: 1, minWidth: 260 }}>
              <div style={styles.sectionHead}>
                <h3 style={styles.sectionTitle}>Sync activity</h3>
              </div>
              <Card style={{ padding: 8 }}>
                {notifLoading && events.length === 0 ? (
                  <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <Skeleton height={12} />
                    <Skeleton height={12} width="80%" />
                    <Skeleton height={12} width="60%" />
                  </div>
                ) : events.length === 0 ? (
                  <EmptyState
                    icon={Sparkles}
                    title="No activity yet"
                    description="Sync events will show up here as soon as they happen."
                  />
                ) : (
                  <div style={styles.activityList}>
                    {events.slice(0, 6).map((event) => (
                      <div key={event.key} style={styles.activityItem}>
                        <span
                          style={{
                            ...styles.activityDot,
                            background:
                              event.type === 'PENDING_UPDATE_CREATED' ? 'var(--warning)' : 'var(--accent)',
                          }}
                        />
                        <div style={{ minWidth: 0, flex: 1 }}>
                          <div style={styles.activityText}>
                            {event.type === 'PENDING_UPDATE_CREATED'
                              ? `Changes detected · ${event.repositoryName}`
                              : `README updated · v${event.versionNumber} · ${event.repositoryName}`}
                          </div>
                          <div style={styles.activityMeta}>{timeAgo(event.createdAt)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
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
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 16,
    marginBottom: 28,
  },
  greeting: { fontSize: 22, fontWeight: 800, letterSpacing: '-0.03em', color: 'var(--text-primary)' },
  subtitle: { fontSize: 13.5, color: 'var(--text-secondary)', marginTop: 6 },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 14,
    marginBottom: 32,
  },
  statTop: { display: 'flex', marginBottom: 14 },
  statIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    background: 'var(--bg-surface-raised)',
    color: 'var(--text-secondary)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  statIconAccent: { background: 'var(--accent-bg)', color: 'var(--accent)' },
  statValue: { fontSize: 26, fontWeight: 800, letterSpacing: '-0.03em', color: 'var(--text-primary)' },
  statLabel: { fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 4 },
  twoCol: { display: 'flex', gap: 24, alignItems: 'flex-start' },
  sectionHead: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 },
  sectionTitle: { fontSize: 15, fontWeight: 700 },
  viewAll: { fontSize: 13, fontWeight: 600, color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: 4 },
  repoList: { display: 'flex', flexDirection: 'column', gap: 8 },
  repoRow: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, padding: 16 },
  repoTop: { display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' },
  repoName: { fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' },
  repoMeta: { display: 'flex', gap: 6, fontSize: 12.5, color: 'var(--text-tertiary)', marginTop: 4, flexWrap: 'wrap' },
  activityList: { display: 'flex', flexDirection: 'column', gap: 2 },
  activityItem: { display: 'flex', gap: 10, padding: '10px 8px' },
  activityDot: { width: 7, height: 7, borderRadius: '50%', marginTop: 5, flexShrink: 0 },
  activityText: { fontSize: 12.5, color: 'var(--text-primary)', lineHeight: 1.4 },
  activityMeta: { fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 },
}
