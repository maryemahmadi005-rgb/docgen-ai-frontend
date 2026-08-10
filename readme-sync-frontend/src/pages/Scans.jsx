import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Radar } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Card from '../components/ui/Card'
import StatusBadge from '../components/ui/StatusBadge'
import Badge from '../components/ui/Badge'
import Spinner from '../components/ui/Spinner'
import EmptyState from '../components/ui/EmptyState'
import { listScans } from '../services/scanService'
import { timeAgo, shortSha } from '../utils/formatDate'

export default function Scans() {
  const [scans, setScans] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    listScans().then((data) => {
      setScans(data)
      setIsLoading(false)
    })
  }, [])

  return (
    <div>
      <PageHeader
        title="Scans"
        description="Chaque commit analysé sur vos branches suivies."
      />

      {isLoading ? (
        <div className="flex h-48 items-center justify-center">
          <Spinner size={26} />
        </div>
      ) : scans.length === 0 ? (
        <Card>
          <EmptyState icon={Radar} title="Aucun scan pour le moment" description="Les commits poussés sur vos branches suivies apparaîtront ici." />
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="divide-y divide-slate-200">
            {scans.map((scan) => (
              <Link
                key={scan.id}
                to={`/scans/${scan.id}`}
                className="flex flex-col gap-2 px-5 py-4 hover:bg-slate-100/60 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-indigo-400">{shortSha(scan.sha)}</span>
                    <span className="text-xs text-ink-muted">{scan.repositoryName}</span>
                  </div>
                  <p className="truncate text-sm font-medium text-navy-800">{scan.message}</p>
                  <div className="flex flex-wrap items-center gap-1.5">
                    <Badge tone="neutral">{scan.impactCategory}</Badge>
                    {scan.affectedSections.map((s) => (
                      <Badge key={s} tone="blue">
                        {s}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-3 sm:flex-col sm:items-end sm:gap-1.5">
                  <StatusBadge status={scan.status} />
                  <span className="text-xs text-ink-muted">{timeAgo(scan.createdAt)}</span>
                </div>
              </Link>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
