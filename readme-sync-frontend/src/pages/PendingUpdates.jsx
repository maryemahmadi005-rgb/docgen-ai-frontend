import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ClipboardList } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import DiffPill from '../components/ui/DiffPill'
import Spinner from '../components/ui/Spinner'
import EmptyState from '../components/ui/EmptyState'
import { listPendingUpdates } from '../services/pendingUpdateService'
import { timeAgo } from '../utils/formatDate'

function countLines(text) {
  return text ? text.split('\n').length : 0
}

export default function PendingUpdates() {
  const [updates, setUpdates] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    listPendingUpdates().then((data) => {
      setUpdates(data)
      setIsLoading(false)
    })
  }, [])

  return (
    <div>
      <PageHeader
        title="Pending Updates"
        description="Propositions de mise à jour en attente de votre validation."
      />

      {isLoading ? (
        <div className="flex h-48 items-center justify-center">
          <Spinner size={26} />
        </div>
      ) : updates.length === 0 ? (
        <Card>
          <EmptyState
            icon={ClipboardList}
            title="Rien en attente"
            description="Toutes les propositions de synchronisation ont été traitées."
          />
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="divide-y divide-slate-200">
            {updates.map((update) => {
              const sections = Object.keys(update.sectionsDiff || {})
              return (
                <Link
                  key={update.id}
                  to={`/pending-updates/${update.id}`}
                  className="flex flex-col gap-2 px-5 py-4 hover:bg-slate-100/60 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0 space-y-1.5">
                    <p className="text-sm font-medium text-navy-800">{update.repositoryName}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {sections.map((s) => (
                        <Badge key={s} tone="indigo">
                          {s}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-4">
                    <DiffPill
                      added={sections.reduce(
                        (acc, s) => acc + countLines(update.sectionsDiff[s].after),
                        0,
                      )}
                      removed={sections.reduce(
                        (acc, s) => acc + countLines(update.sectionsDiff[s].before),
                        0,
                      )}
                    />
                    <span className="text-xs text-ink-muted">{timeAgo(update.createdAt)}</span>
                  </div>
                </Link>
              )
            })}
          </div>
        </Card>
      )}
    </div>
  )
}
