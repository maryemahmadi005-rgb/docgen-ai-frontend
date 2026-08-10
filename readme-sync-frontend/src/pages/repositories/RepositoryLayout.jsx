import { useEffect, useState, useCallback } from 'react'
import { useParams, Outlet, useOutletContext, Link } from 'react-router-dom'
import { ExternalLink, GitBranch, LayoutGrid, FileText, BarChart3, GitPullRequestArrow, History, Settings, Trash2 } from 'lucide-react'
import { repositoriesApi } from '../../api/repositories'
import { getErrorMessage } from '../../api/client'
import { ErrorState, Skeleton } from '../../components/ui/States'
import { Badge } from '../../components/ui/Primitives'
import { ConfirmDialog } from '../../components/ui/Modal'
import Button from '../../components/ui/Button'
import Tabs from '../../components/ui/Tabs'
import { useToast } from '../../context/ToastContext'
import { useNavigate } from 'react-router-dom'
import { toGithubUrl } from '../../utils/format'

export default function RepositoryLayout() {
  const { repoId } = useParams()
  const [repo, setRepo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const toast = useToast()
  const navigate = useNavigate()

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await repositoriesApi.get(repoId)
      setRepo(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load this repository.'))
    } finally {
      setLoading(false)
    }
  }, [repoId])

  useEffect(() => {
    load()
  }, [load])

  async function handleDelete() {
    setDeleting(true)
    try {
      await repositoriesApi.delete(repoId)
      toast.success('Repository removed.')
      navigate('/repositories')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Unable to delete this repository.'))
      setDeleting(false)
      setDeleteOpen(false)
    }
  }

  if (loading) {
    return (
      <div>
        <Skeleton width="40%" height={24} />
        <Skeleton width="60%" height={14} style={{ marginTop: 12 }} />
      </div>
    )
  }

  if (error || !repo) {
    return <ErrorState description={error || 'Repository not found.'} onRetry={load} />
  }

  const tabs = [
    { to: `/repositories/${repoId}`, label: 'Overview', icon: LayoutGrid, end: true },
    { to: `/repositories/${repoId}/readme`, label: 'README', icon: FileText },
    { to: `/repositories/${repoId}/analysis`, label: 'Analysis', icon: BarChart3 },
    { to: `/repositories/${repoId}/pending-updates`, label: 'Pending Updates', icon: GitPullRequestArrow },
    { to: `/repositories/${repoId}/versions`, label: 'Versions', icon: History },
    { to: `/repositories/${repoId}/settings`, label: 'Settings', icon: Settings },
  ]

  return (
    <div>
      <div style={styles.header} className="rs-stack-mobile">
        <div style={{ minWidth: 0 }}>
          <div style={styles.titleRow}>
            <GitBranch size={18} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />
            <h1 style={styles.title}>{repo.full_name}</h1>
            <a href={toGithubUrl(repo.full_name)} target="_blank" rel="noreferrer" style={styles.externalLink}>
              <ExternalLink size={14} />
            </a>
          </div>
          <div style={styles.metaRow}>
            <span className="mono">{repo.tracked_branch || repo.default_branch}</span>
            <span>·</span>
            <Badge variant={repo.sync_mode === 'automatic' ? 'success' : 'neutral'} dot>
              {repo.sync_mode === 'automatic' ? 'Automatic sync' : 'Manual sync'}
            </Badge>
            <Badge variant="neutral">{repo.sync_method}</Badge>
          </div>
        </div>
        <Button variant="danger" size="sm" icon={Trash2} onClick={() => setDeleteOpen(true)}>
          Delete
        </Button>
      </div>

      <Tabs items={tabs} />

      <Outlet context={{ repo, reloadRepo: load }} />

      <ConfirmDialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={handleDelete}
        loading={deleting}
        variant="danger"
        confirmLabel="Delete repository"
        title="Delete this repository?"
        description={`This will permanently remove "${repo.full_name}" and all its README history, versions, and pending updates from README Sync. This cannot be undone.`}
      />
    </div>
  )
}

export function useRepositoryContext() {
  return useOutletContext()
}

const styles = {
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, marginBottom: 20 },
  titleRow: { display: 'flex', alignItems: 'center', gap: 10 },
  title: { fontSize: 20, fontWeight: 800, letterSpacing: '-0.02em', wordBreak: 'break-word' },
  externalLink: { color: 'var(--text-tertiary)', display: 'flex', flexShrink: 0 },
  metaRow: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: 'var(--text-tertiary)', marginTop: 8, flexWrap: 'wrap' },
}
