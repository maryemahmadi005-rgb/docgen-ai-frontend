import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { History, Save, FileText, Eye, Code2 } from 'lucide-react'
import { useRepositoryContext } from '../repositories/RepositoryLayout'
import { readmesApi } from '../../api/readmes'
import { getErrorMessage } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import { Card } from '../../components/ui/Primitives'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui/States'
import Button from '../../components/ui/Button'
import { formatDateTime } from '../../utils/format'

export default function ReadmeEditorPage() {
  const { repo } = useRepositoryContext()
  const [readme, setReadme] = useState(null)
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notFound, setNotFound] = useState(false)
  const [saving, setSaving] = useState(false)
  const [mobileView, setMobileView] = useState('edit') // 'edit' | 'preview'
  const toast = useToast()

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setNotFound(false)
    try {
      const data = await readmesApi.get(repo.id)
      setReadme(data)
      setContent(data.content_md || '')
    } catch (err) {
      if (err?.response?.status === 404) setNotFound(true)
      else setError(getErrorMessage(err, 'Unable to load the README.'))
    } finally {
      setLoading(false)
    }
  }, [repo.id])

  useEffect(() => {
    load()
  }, [load])

  const hasChanges = readme && content !== (readme.content_md || '')

  async function handleSave() {
    setSaving(true)
    try {
      // sections_json is required by the backend; since this UI edits the
      // rendered markdown directly, we preserve the existing sections_json
      // structure as-is (no invented per-section editing UI here).
      const updated = await readmesApi.update(repo.id, {
        content_md: content,
        sections_json: readme.sections_json ?? {},
      })
      setReadme(updated)
      setContent(updated.content_md || '')
      toast.success('README saved.')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Unable to save the README.'))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div>
        <Skeleton width="30%" height={16} />
        <Skeleton width="100%" height={280} style={{ marginTop: 16 }} />
      </div>
    )
  }

  if (error) return <ErrorState description={error} onRetry={load} />

  if (notFound) {
    return (
      <Card>
        <EmptyState
          icon={FileText}
          title="No README generated yet"
          description="This repository doesn't have a generated README yet. Once one is created, it will appear here for editing."
        />
      </Card>
    )
  }

  return (
    <div>
      <div style={styles.toolbar} className="rs-stack-mobile">
        <div style={styles.toolbarLeft}>
          <span style={styles.updatedText}>
            Last updated {formatDateTime(readme.updated_at)}
          </span>
          {hasChanges && <span style={styles.unsavedDot}>Unsaved changes</span>}
        </div>
        <div style={styles.toolbarRight}>
          <Link to={`/repositories/${repo.id}/versions`}>
            <Button variant="secondary" size="sm" icon={History}>History</Button>
          </Link>
          <Button size="sm" icon={Save} onClick={handleSave} loading={saving} disabled={!hasChanges}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </div>
      </div>

      <div style={styles.mobileTabs} className="rs-mobile-editor-tabs">
        <button
          onClick={() => setMobileView('edit')}
          style={{ ...styles.mobileTab, ...(mobileView === 'edit' ? styles.mobileTabActive : {}) }}
        >
          <Code2 size={14} /> Editor
        </button>
        <button
          onClick={() => setMobileView('preview')}
          style={{ ...styles.mobileTab, ...(mobileView === 'preview' ? styles.mobileTabActive : {}) }}
        >
          <Eye size={14} /> Preview
        </button>
      </div>

      <div style={styles.splitView} className="rs-split-view">
        <div
          className="rs-split-pane"
          style={{ ...styles.pane, ...(mobileView !== 'edit' ? { display: 'none' } : {}) }}
          data-pane="edit"
        >
          <div style={styles.paneHeader}>
            <Code2 size={13} /> Markdown
          </div>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            spellCheck={false}
            style={styles.textarea}
          />
        </div>
        <div
          className="rs-split-pane"
          style={{ ...styles.pane, ...(mobileView !== 'preview' ? { display: 'none' } : {}) }}
          data-pane="preview"
        >
          <div style={styles.paneHeader}>
            <Eye size={13} /> Preview
          </div>
          <div style={styles.previewBody} className="rs-preview-body">
            {content.trim() ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
            ) : (
              <span style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>Nothing to preview yet.</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

const styles = {
  toolbar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, gap: 12 },
  toolbarLeft: { display: 'flex', alignItems: 'center', gap: 10 },
  updatedText: { fontSize: 12.5, color: 'var(--text-tertiary)' },
  unsavedDot: { fontSize: 12, fontWeight: 600, color: 'var(--warning)', background: 'var(--warning-bg)', padding: '3px 9px', borderRadius: 999 },
  toolbarRight: { display: 'flex', gap: 8 },
  mobileTabs: { display: 'none', gap: 4, marginBottom: 12, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: 3 },
  mobileTab: { flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, padding: '8px 0', fontSize: 12.5, fontWeight: 600, color: 'var(--text-tertiary)', background: 'none', border: 'none', borderRadius: 6 },
  mobileTabActive: { background: 'var(--bg-surface-raised)', color: 'var(--text-primary)' },
  splitView: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 1,
    background: 'var(--border-subtle)',
    border: '1px solid var(--border-subtle)',
    borderRadius: 'var(--radius-md)',
    overflow: 'hidden',
    height: 560,
  },
  pane: { display: 'flex', flexDirection: 'column', background: 'var(--bg-surface)', minWidth: 0 },
  paneHeader: {
    display: 'flex', alignItems: 'center', gap: 6, padding: '10px 14px',
    fontSize: 11.5, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase',
    letterSpacing: '0.04em', borderBottom: '1px solid var(--border-subtle)', flexShrink: 0,
  },
  textarea: {
    flex: 1, width: '100%', border: 'none', outline: 'none', resize: 'none',
    background: 'var(--bg-inset)', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)',
    fontSize: 13, lineHeight: 1.6, padding: 16, boxSizing: 'border-box',
  },
  previewBody: {
    flex: 1, overflowY: 'auto', padding: '16px 20px', fontSize: 13.5, color: 'var(--text-primary)', lineHeight: 1.7,
  },
}
