import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, AlertCircle } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Card, { CardBody } from '../components/ui/Card'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'
import { createRepository } from '../services/repositoryService'

export default function AddRepository() {
  const navigate = useNavigate()
  const [githubUrl, setGithubUrl] = useState('')
  const [syncMode, setSyncMode] = useState('manual')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const deriveFullName = (url) => {
    const match = url.match(/github\.com\/([^/]+\/[^/.]+)/)
    return match ? match[1] : url
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!githubUrl.trim()) {
      setError('Renseignez une URL de repository GitHub.')
      return
    }
    setIsSubmitting(true)
    try {
      const repo = await createRepository({
        githubUrl,
        fullName: deriveFullName(githubUrl),
        syncMode,
      })
      navigate(`/repositories/${repo.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <Link to="/repositories" className="mb-4 inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-navy-800">
        <ArrowLeft size={15} /> Retour aux repositories
      </Link>

      <PageHeader
        title="Ajouter un repository"
        description="Connectez un dépôt GitHub pour démarrer la synchronisation de son README."
      />

      <Card>
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="flex items-start gap-2 rounded-lg bg-coral-100 px-3.5 py-2.5 text-sm text-coral-500">
                <AlertCircle size={16} className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <Input
              id="githubUrl"
              label="URL du repository GitHub"
              placeholder="https://github.com/owner/repo"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
            />

            <div>
              <span className="mb-2 block text-sm font-medium text-navy-800">Mode de synchronisation</span>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { value: 'manual', label: 'Manuel', desc: 'Chaque changement attend votre validation.' },
                  { value: 'auto', label: 'Automatique', desc: 'Les changements sûrs sont appliqués directement.' },
                ].map((option) => (
                  <button
                    type="button"
                    key={option.value}
                    onClick={() => setSyncMode(option.value)}
                    className={`rounded-lg border p-3.5 text-left transition-colors ${
                      syncMode === option.value
                        ? 'border-blue-500 bg-blue-700/5'
                        : 'border-slate-300 hover:border-slate-400'
                    }`}
                  >
                    <p className="text-sm font-medium text-navy-800">{option.label}</p>
                    <p className="mt-0.5 text-xs text-ink-muted">{option.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? <Spinner size={16} className="text-white" /> : 'Connecter le repository'}
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  )
}
