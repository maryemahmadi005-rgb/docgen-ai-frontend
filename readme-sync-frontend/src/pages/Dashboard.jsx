import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FolderGit2, Zap, ClipboardList, Radar, ArrowRight } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Card, { CardBody, CardHeader } from '../components/ui/Card'
import StatusBadge from '../components/ui/StatusBadge'
import Spinner from '../components/ui/Spinner'
import { useAuth } from '../hooks/useAuth'
import { listRepositories } from '../services/repositoryService'
import { listScans } from '../services/scanService'
import { listPendingUpdates } from '../services/pendingUpdateService'
import { timeAgo, shortSha } from '../utils/formatDate'

function StatCard({ icon: Icon, label, value, tone }) {
  return (
    <Card>
      <CardBody className="flex items-center gap-4">
        <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-lg ${tone}`}>
          <Icon size={19} strokeWidth={2} />
        </div>
        <div>
          <p className="text-2xl font-semibold text-navy-800">{value}</p>
          <p className="text-sm text-ink-muted">{label}</p>
        </div>
      </CardBody>
    </Card>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [repos, setRepos] = useState([])
  const [scans, setScans] = useState([])
  const [pending, setPending] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    Promise.all([listRepositories(), listScans(), listPendingUpdates()]).then(
      ([r, s, p]) => {
        if (!mounted) return
        setRepos(r)
        setScans(s)
        setPending(p)
        setIsLoading(false)
      },
    )
    return () => {
      mounted = false
    }
  }, [])

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size={26} />
      </div>
    )
  }

  const activeSyncs = repos.filter((r) => r.syncMode === 'auto').length

  return (
    <div>
      <PageHeader
        title={`Bonjour, ${user?.name || ''}`}
        description="Vue d'ensemble de vos repositories et de leur documentation."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={FolderGit2} label="Repositories" value={repos.length} tone="bg-blue-700/10 text-blue-700" />
        <StatCard icon={Zap} label="Sync automatique" value={activeSyncs} tone="bg-indigo-400/15 text-indigo-400" />
        <StatCard icon={ClipboardList} label="En attente" value={pending.length} tone="bg-amber-100 text-amber-500" />
        <StatCard icon={Radar} label="Scans récents" value={scans.length} tone="bg-coral-100 text-coral-500" />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader className="flex items-center justify-between">
            <h2 className="font-display text-base font-semibold text-navy-800">Repositories récents</h2>
            <Link to="/repositories" className="flex items-center gap-1 text-sm text-blue-700 hover:underline">
              Tout voir <ArrowRight size={14} />
            </Link>
          </CardHeader>
          <div className="divide-y divide-slate-200">
            {repos.slice(0, 4).map((repo) => (
              <Link
                key={repo.id}
                to={`/repositories/${repo.id}`}
                className="flex items-center justify-between gap-4 px-5 py-3.5 hover:bg-slate-100/60"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-navy-800">{repo.fullName}</p>
                  <p className="truncate text-xs text-ink-muted">
                    Dernière sync {timeAgo(repo.lastSyncAt)}
                  </p>
                </div>
                <StatusBadge status={repo.status} />
              </Link>
            ))}
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="flex items-center justify-between">
            <h2 className="font-display text-base font-semibold text-navy-800">Derniers scans</h2>
            <Link to="/scans" className="flex items-center gap-1 text-sm text-blue-700 hover:underline">
              Tout voir <ArrowRight size={14} />
            </Link>
          </CardHeader>
          <div className="divide-y divide-slate-200">
            {scans.slice(0, 4).map((scan) => (
              <Link
                key={scan.id}
                to={`/scans/${scan.id}`}
                className="block px-5 py-3.5 hover:bg-slate-100/60"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs text-indigo-400">{shortSha(scan.sha)}</span>
                  <StatusBadge status={scan.status} />
                </div>
                <p className="mt-1 truncate text-sm text-navy-800">{scan.message}</p>
              </Link>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
