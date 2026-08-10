import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, User, GitCommit } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Card, { CardBody, CardHeader } from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import StatusBadge from '../components/ui/StatusBadge'
import SectionCode from '../components/ui/SectionCode'
import Spinner from '../components/ui/Spinner'
import { getScan } from '../services/scanService'
import { formatDateTime, shortSha } from '../utils/formatDate'

export default function ScanDetails() {
  const { id } = useParams()
  const [scan, setScan] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    getScan(id).then((data) => {
      setScan(data)
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

  if (!scan) return null

  const sectionEntries = Object.entries(scan.sectionsDiff || {})

  return (
    <div>
      <Link to="/scans" className="mb-4 inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-navy-800">
        <ArrowLeft size={15} /> Retour aux scans
      </Link>

      <PageHeader
        title={scan.message}
        description={scan.repositoryName}
        actions={<StatusBadge status={scan.status} />}
      />

      <div className="mb-6 flex flex-wrap items-center gap-4 text-sm text-ink-muted">
        <span className="flex items-center gap-1.5">
          <GitCommit size={15} />
          <span className="font-mono text-indigo-400">{shortSha(scan.sha)}</span>
        </span>
        <span className="flex items-center gap-1.5">
          <User size={15} />
          {scan.author}
        </span>
        <span>{formatDateTime(scan.createdAt)}</span>
        <Badge tone="neutral">{scan.impactCategory}</Badge>
        <Badge tone="indigo">confiance {Math.round(scan.confidenceScore * 100)}%</Badge>
      </div>

      {scan.fileChanges?.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <h2 className="font-display text-base font-semibold text-navy-800">Fichiers modifiés</h2>
          </CardHeader>
          <div className="divide-y divide-slate-200">
            {scan.fileChanges.map((fc) => (
              <div key={fc.path} className="flex items-center justify-between px-5 py-2.5">
                <span className="font-mono text-sm text-navy-800">{fc.path}</span>
                <Badge tone={fc.type === 'added' ? 'blue' : 'indigo'}>{fc.type}</Badge>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="space-y-5">
        <h2 className="font-display text-base font-semibold text-navy-800">Sections analysées</h2>
        {sectionEntries.length === 0 ? (
          <Card>
            <CardBody className="text-sm text-ink-muted">
              Aucune section README affectée par ce commit.
            </CardBody>
          </Card>
        ) : (
          sectionEntries.map(([section, diff]) => (
            <Card key={section}>
              <CardHeader>
                <h3 className="font-mono text-sm font-medium text-navy-800">## {section}</h3>
              </CardHeader>
              <CardBody>
                <SectionCode before={diff.before} after={diff.after} />
              </CardBody>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
