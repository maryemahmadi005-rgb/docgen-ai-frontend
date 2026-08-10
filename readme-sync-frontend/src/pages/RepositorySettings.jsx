import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Trash2, AlertCircle, CheckCircle2 } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Card, { CardBody, CardHeader } from '../components/ui/Card'
import Button from '../components/ui/Button'
import Tabs from '../components/ui/Tabs'
import Spinner from '../components/ui/Spinner'
import {
  getRepository,
  getRepositorySettings,
  updateRepositorySettings,
  deleteRepository,
} from '../services/repositoryService'

export default function RepositorySettings() {
  const { id } = useParams()
  const [repo, setRepo] = useState(null)
  const [settings, setSettings] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [savedMessage, setSavedMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getRepository(id), getRepositorySettings(id)]).then(([r, s]) => {
      setRepo(r)
      setSettings(s)
      setIsLoading(false)
    })
  }, [id])

  const handleSyncModeChange = async (mode) => {
    setError('')
    setSavedMessage('')
    setIsSaving(true)
    try {
      await updateRepositorySettings(id, { syncMode: mode })
      setSettings((prev) => ({ ...prev, syncMode: mode }))
      setSavedMessage('Paramètres enregistrés.')
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSaving(false)
    }
  }

  const handleTrackedBranchSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSavedMessage('')
    setIsSaving(true)
    const form = new FormData(e.target)
    try {
      await updateRepositorySettings(id, { trackedBranch: form.get('trackedBranch') })
      setSavedMessage('Branche suivie mise à jour.')
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm(`Supprimer définitivement ${repo.fullName} ? Cette action retire aussi le webhook GitHub.`)) return
    await deleteRepository(id)
    window.location.href = '/repositories'
  }

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size={26} />
      </div>
    )
  }

  return (
    <div>
      <Link to={`/repositories/${id}`} className="mb-4 inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-navy-800">
        <ArrowLeft size={15} /> Retour au repository
      </Link>

      <PageHeader title="Paramètres" description={repo.fullName} />

      <Tabs
        items={[
          { to: `/repositories/${id}`, label: 'Vue d\u2019ensemble', end: true },
          { to: `/repositories/${id}/settings`, label: 'Paramètres' },
        ]}
      />

      {(error || savedMessage) && (
        <div
          className={`mb-5 flex items-center gap-2 rounded-lg px-3.5 py-2.5 text-sm ${
            error ? 'bg-coral-100 text-coral-500' : 'bg-blue-700/10 text-blue-700'
          }`}
        >
          {error ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
          {error || savedMessage}
        </div>
      )}

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <h2 className="font-display text-base font-semibold text-navy-800">Mode de synchronisation</h2>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {[
                { value: 'manual', label: 'Manuel', desc: 'Chaque changement attend votre validation avant d\u2019être appliqué.' },
                { value: 'auto', label: 'Automatique', desc: 'Les changements détectés sont appliqués directement au README.' },
              ].map((option) => (
                <button
                  key={option.value}
                  disabled={isSaving}
                  onClick={() => handleSyncModeChange(option.value)}
                  className={`rounded-lg border p-4 text-left transition-colors disabled:opacity-60 ${
                    settings.syncMode === option.value
                      ? 'border-blue-500 bg-blue-700/5'
                      : 'border-slate-300 hover:border-slate-400'
                  }`}
                >
                  <p className="text-sm font-medium text-navy-800">{option.label}</p>
                  <p className="mt-1 text-xs text-ink-muted">{option.desc}</p>
                </button>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="font-display text-base font-semibold text-navy-800">Branche suivie</h2>
          </CardHeader>
          <CardBody>
            <form onSubmit={handleTrackedBranchSubmit} className="flex items-end gap-3">
              <label className="flex-1">
                <span className="mb-1.5 block text-sm font-medium text-navy-800">Nom de la branche</span>
                <input
                  name="trackedBranch"
                  defaultValue={settings.trackedBranch}
                  className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 font-mono text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
                />
              </label>
              <Button type="submit" variant="secondary" disabled={isSaving}>
                Enregistrer
              </Button>
            </form>
            <p className="mt-2 text-xs text-ink-muted">
              Seuls les push sur cette branche déclenchent une analyse.
            </p>
          </CardBody>
        </Card>

        <Card className="border-coral-500/30">
          <CardHeader>
            <h2 className="font-display text-base font-semibold text-coral-500">Zone de danger</h2>
          </CardHeader>
          <CardBody className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-navy-800">Supprimer ce repository</p>
              <p className="text-xs text-ink-muted">
                Retire le webhook GitHub et supprime toutes les données associées.
              </p>
            </div>
            <Button variant="danger" icon={Trash2} onClick={handleDelete}>
              Supprimer
            </Button>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
