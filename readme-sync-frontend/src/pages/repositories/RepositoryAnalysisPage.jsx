import { useEffect, useState } from 'react'
import { Code2, Package, Layers, Terminal, PlayCircle, FolderTree } from 'lucide-react'
import { useRepositoryContext } from './RepositoryLayout'
import { analysisApi } from '../../api/analysis'
import { getErrorMessage } from '../../api/client'
import { Card, Badge } from '../../components/ui/Primitives'
import { EmptyState, ErrorState, SkeletonCard } from '../../components/ui/States'
import { formatDateTime } from '../../utils/format'

export default function RepositoryAnalysisPage() {
  const { repo } = useRepositoryContext()
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    load()
  }, [repo.id])

  async function load() {
    setLoading(true)
    setError(null)
    setNotFound(false)
    try {
      const data = await analysisApi.getLatest(repo.id)
      setAnalysis(data)
    } catch (err) {
      if (err?.response?.status === 404) setNotFound(true)
      else setError(getErrorMessage(err, 'Unable to load the analysis.'))
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div style={styles.grid}>
        {[1, 2, 3, 4].map((i) => <SkeletonCard key={i} />)}
      </div>
    )
  }

  if (error) return <ErrorState description={error} onRetry={load} />

  if (notFound) {
    return (
      <Card>
        <EmptyState
          icon={Code2}
          title="No analysis available"
          description="This repository hasn't been analyzed yet. Analysis data will appear here once available."
        />
      </Card>
    )
  }

  const languages = toEntries(analysis.languages)
  const frameworks = toEntries(analysis.frameworks)
  const dependencies = toEntries(analysis.dependencies)
  const importantFiles = toList(analysis.important_files)
  const installScripts = toList(analysis.install_scripts)
  const runScripts = toList(analysis.run_scripts)

  return (
    <div>
      <div style={styles.timestamp}>Analyzed {formatDateTime(analysis.created_at)}</div>

      <div style={styles.grid}>
        <AnalysisCard icon={Code2} title="Languages" empty={languages.length === 0}>
          <div style={styles.pillRow}>
            {languages.map(([name, value]) => (
              <Badge key={name} variant="info">{name}{value ? ` · ${value}` : ''}</Badge>
            ))}
          </div>
        </AnalysisCard>

        <AnalysisCard icon={Layers} title="Frameworks" empty={frameworks.length === 0}>
          <div style={styles.pillRow}>
            {frameworks.map(([name, value]) => (
              <Badge key={name} variant="success">{name}{value ? ` · ${value}` : ''}</Badge>
            ))}
          </div>
        </AnalysisCard>

        <AnalysisCard icon={Package} title="Dependencies" empty={dependencies.length === 0} wide>
          <div style={styles.pillRow}>
            {dependencies.map(([name, value]) => (
              <Badge key={name} variant="neutral">{name}{typeof value === 'string' ? ` @ ${value}` : ''}</Badge>
            ))}
          </div>
        </AnalysisCard>

        <AnalysisCard icon={FolderTree} title="Important files" empty={importantFiles.length === 0}>
          <ul style={styles.list}>
            {importantFiles.map((f) => <li key={f} className="mono" style={styles.listItem}>{f}</li>)}
          </ul>
        </AnalysisCard>

        <AnalysisCard icon={Terminal} title="Install scripts" empty={installScripts.length === 0}>
          <ul style={styles.list}>
            {installScripts.map((s, i) => <li key={i} className="mono" style={styles.listItem}>{s}</li>)}
          </ul>
        </AnalysisCard>

        <AnalysisCard icon={PlayCircle} title="Run scripts" empty={runScripts.length === 0}>
          <ul style={styles.list}>
            {runScripts.map((s, i) => <li key={i} className="mono" style={styles.listItem}>{s}</li>)}
          </ul>
        </AnalysisCard>
      </div>

      {analysis.file_structure && Object.keys(analysis.file_structure).length > 0 && (
        <Card style={{ marginTop: 14 }}>
          <div style={styles.cardHeader}>
            <FolderTree size={15} style={{ color: 'var(--accent)' }} />
            <span style={styles.cardTitle}>File structure</span>
          </div>
          <pre style={styles.pre}>{JSON.stringify(analysis.file_structure, null, 2)}</pre>
        </Card>
      )}
    </div>
  )
}

function AnalysisCard({ icon: Icon, title, children, empty, wide }) {
  return (
    <Card style={wide ? { gridColumn: '1 / -1' } : undefined}>
      <div style={styles.cardHeader}>
        <Icon size={15} style={{ color: 'var(--accent)' }} />
        <span style={styles.cardTitle}>{title}</span>
      </div>
      {empty ? (
        <div style={styles.emptyText}>No data available</div>
      ) : (
        children
      )}
    </Card>
  )
}

function toEntries(value) {
  if (!value) return []
  if (Array.isArray(value)) return value.map((v) => [v, null])
  if (typeof value === 'object') return Object.entries(value)
  return []
}

function toList(value) {
  if (!value) return []
  if (Array.isArray(value)) return value
  if (typeof value === 'object') return Object.values(value)
  return []
}

const styles = {
  timestamp: { fontSize: 12.5, color: 'var(--text-tertiary)', marginBottom: 16 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 },
  cardHeader: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 },
  cardTitle: { fontSize: 13.5, fontWeight: 700, color: 'var(--text-primary)' },
  pillRow: { display: 'flex', flexWrap: 'wrap', gap: 6 },
  list: { margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 6 },
  listItem: { fontSize: 12.5, color: 'var(--text-secondary)', background: 'var(--bg-inset)', padding: '6px 10px', borderRadius: 6 },
  emptyText: { fontSize: 12.5, color: 'var(--text-tertiary)' },
  pre: {
    fontSize: 12, color: 'var(--text-secondary)', background: 'var(--bg-inset)',
    padding: 14, borderRadius: 'var(--radius-sm)', overflowX: 'auto', margin: 0,
    maxHeight: 320, overflowY: 'auto',
  },
}
