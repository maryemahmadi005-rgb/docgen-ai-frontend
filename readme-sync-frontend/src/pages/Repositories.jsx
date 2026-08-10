import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, FolderGit2, GitBranch } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import StatusBadge from '../components/ui/StatusBadge'
import Spinner from '../components/ui/Spinner'
import EmptyState from '../components/ui/EmptyState'
import { listRepositories } from '../services/repositoryService'
import { timeAgo } from '../utils/formatDate'

export default function Repositories() {
  const [repos, setRepos] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    listRepositories().then((data) => {
      setRepos(data)
      setIsLoading(false)
    })
  }, [])

  return (
    <div>
      <PageHeader
        title="Repositories"
        description="Tous les dépôts connectés à votre compte."
        actions={
          <Button as={Link} to="/repositories/add" icon={Plus}>
            Ajouter un repository
          </Button>
        }
      />

      {isLoading ? (
        <div className="flex h-48 items-center justify-center">
          <Spinner size={26} />
        </div>
      ) : repos.length === 0 ? (
        <Card>
          <EmptyState
            icon={FolderGit2}
            title="Aucun repository connecté"
            description="Ajoutez votre premier dépôt GitHub pour démarrer la synchronisation automatique de votre README."
            action={
              <Button as={Link} to="/repositories/add" icon={Plus}>
                Ajouter un repository
              </Button>
            }
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {repos.map((repo) => (
            <Link key={repo.id} to={`/repositories/${repo.id}`}>
              <Card className="h-full transition-shadow hover:shadow-md">
                <div className="p-5">
                  <div className="mb-3 flex items-start justify-between gap-2">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-700/10 text-blue-700">
                      <FolderGit2 size={17} />
                    </div>
                    <StatusBadge status={repo.status} />
                  </div>
                  <p className="truncate text-sm font-semibold text-navy-800">{repo.fullName}</p>
                  <p className="mt-1 line-clamp-2 min-h-[2.5em] text-xs text-ink-muted">
                    {repo.description || 'Aucune description.'}
                  </p>
                  <div className="mt-4 flex items-center justify-between text-xs text-ink-muted">
                    <span className="flex items-center gap-1">
                      <GitBranch size={12} />
                      {repo.trackedBranch}
                    </span>
                    <span>Sync {timeAgo(repo.lastSyncAt)}</span>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
