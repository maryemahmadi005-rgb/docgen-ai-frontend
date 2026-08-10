import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, GitBranch, Calendar, RefreshCw } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Card, { CardBody, CardHeader } from '../components/ui/Card'
import StatusBadge from '../components/ui/StatusBadge'
import Tabs from '../components/ui/Tabs'
import Spinner from '../components/ui/Spinner'
import { getRepository, getRepositoryReadme } from '../services/repositoryService'
import { formatDate, timeAgo } from '../utils/formatDate'

export default function RepositoryDetails() {
  const { id } = useParams()
  const [repo, setRepo] = useState(null)
  const [readme, setReadme] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    setIsLoading(true)
    Promise.all([getRepository(id), getRepositoryReadme(id)]).then(([r, rd]) => {
      setRepo(r)
      setReadme(rd)
      setIsLoading(false)
    })
  }, [id])

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size={26} />
      </div>
    )
  }

  if (!repo) return null

  return (
    <div>
      <Link to="/repositories" className="mb-4 inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-navy-800">
        <ArrowLeft size={15} /> Retour aux repositories
      </Link>

      <PageHeader title={repo.fullName} description={repo.description} actions={<StatusBadge status={repo.status} />} />

      <Tabs
        items={[
          { to: `/repositories/${id}`, label: 'Vue d\u2019ensemble', end: true },
          { to: `/repositories/${id}/settings`, label: 'Paramètres' },
        ]}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-1">
          <Card>
            <CardBody className="space-y-3.5 text-sm">
              <div className="flex items-center gap-2.5 text-ink-muted">
                <GitBranch size={15} />
                Branche suivie : <span className="font-mono text-navy-800">{repo.trackedBranch}</span>
              </div>
              <div className="flex items-center gap-2.5 text-ink-muted">
                <RefreshCw size={15} />
                Sync {repo.syncMode === 'auto' ? 'automatique' : 'manuelle'} · {repo.syncMethod}
              </div>
              <div className="flex items-center gap-2.5 text-ink-muted">
                <Calendar size={15} />
                Connecté le {formatDate(repo.connectedAt)}
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody className="grid grid-cols-2 gap-4 text-center">
              <div>
                <p className="text-xl font-semibold text-navy-800">{repo.readmeUpdatedCount}</p>
                <p className="text-xs text-ink-muted">Mises à jour</p>
              </div>
              <div>
                <p className="text-xl font-semibold text-navy-800">{repo.pendingUpdates}</p>
                <p className="text-xs text-ink-muted">En attente</p>
              </div>
            </CardBody>
          </Card>
        </div>

        <Card className="lg:col-span-2">
          <CardHeader className="flex items-center justify-between">
            <h2 className="font-display text-base font-semibold text-navy-800">README courant</h2>
            <span className="text-xs text-ink-muted">Dernière sync {timeAgo(repo.lastSyncAt)}</span>
          </CardHeader>
          <CardBody>
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap font-mono text-xs leading-relaxed text-navy-800">
              {readme?.contentMd}
            </pre>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
