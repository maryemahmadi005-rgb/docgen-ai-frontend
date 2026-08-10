import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Check, X, AlertCircle } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Card, { CardBody, CardHeader } from '../components/ui/Card'
import Button from '../components/ui/Button'
import SectionCode from '../components/ui/SectionCode'
import Spinner from '../components/ui/Spinner'
import {
  getPendingUpdate,
  approvePendingUpdate,
  rejectPendingUpdate,
} from '../services/pendingUpdateService'
import { formatDateTime } from '../utils/formatDate'

export default function PendingUpdateDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [update, setUpdate] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [showRejectForm, setShowRejectForm] = useState(false)
  const [reason, setReason] = useState('')

  useEffect(() => {
    getPendingUpdate(id)
      .then(setUpdate)
      .catch((err) => setError(err.message))
      .finally(() => setIsLoading(false))
  }, [id])

  const handleApprove = async () => {
    setError('')
    setIsProcessing(true)
    try {
      // Aucun body envoyé : le patch a déjà été calculé et figé à la
      // création de la pending_update — pas de second appel IA ici.
      await approvePendingUpdate(id)
      navigate('/pending-updates')
    } catch (err) {
      // 409 côté backend si l'update n'est plus 'pending' (déjà résolue ou stale)
      setError(err.message)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleReject = async () => {
    setError('')
    setIsProcessing(true)
    try {
      await rejectPendingUpdate(id, reason)
      navigate('/pending-updates')
    } catch (err) {
      setError(err.message)
    } finally {
      setIsProcessing(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size={26} />
      </div>
    )
  }

  if (!update) {
    return (
      <div className="text-center text-sm text-ink-muted">Proposition introuvable.</div>
    )
  }

  const sectionEntries = Object.entries(update.sectionsDiff || {})

  return (
    <div>
      <Link to="/pending-updates" className="mb-4 inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-navy-800">
        <ArrowLeft size={15} /> Retour aux propositions
      </Link>

      <PageHeader
        title={update.repositoryName}
        description={`Proposée ${formatDateTime(update.createdAt)}`}
      />

      {error && (
        <div className="mb-5 flex items-center gap-2 rounded-lg bg-coral-100 px-3.5 py-2.5 text-sm text-coral-500">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      <div className="space-y-5">
        {sectionEntries.map(([section, diff]) => (
          <Card key={section}>
            <CardHeader>
              <h3 className="font-mono text-sm font-medium text-navy-800">## {section}</h3>
            </CardHeader>
            <CardBody>
              <SectionCode before={diff.before} after={diff.after} />
            </CardBody>
          </Card>
        ))}
      </div>

      <Card className="mt-6">
        <CardBody>
          {!showRejectForm ? (
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button icon={Check} onClick={handleApprove} disabled={isProcessing}>
                {isProcessing ? <Spinner size={16} className="text-white" /> : 'Approuver et appliquer'}
              </Button>
              <Button
                variant="secondary"
                icon={X}
                onClick={() => setShowRejectForm(true)}
                disabled={isProcessing}
              >
                Rejeter
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              <label className="block">
                <span className="mb-1.5 block text-sm font-medium text-navy-800">
                  Raison du rejet (optionnel)
                </span>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
                  placeholder="Pourquoi ce changement n'est pas pertinent..."
                />
              </label>
              <div className="flex gap-3">
                <Button variant="danger" onClick={handleReject} disabled={isProcessing}>
                  {isProcessing ? <Spinner size={16} className="text-white" /> : 'Confirmer le rejet'}
                </Button>
                <Button variant="ghost" onClick={() => setShowRejectForm(false)} disabled={isProcessing}>
                  Annuler
                </Button>
              </div>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
