import { CheckCircle2, Clock, AlertTriangle } from 'lucide-react'
import Badge from './Badge'

// Statut d'un repository ou d'un scan — vocabulaire cohérent dans toute l'app.
const CONFIG = {
  synced: { label: 'Synchronisé', tone: 'blue', Icon: CheckCircle2 },
  applied: { label: 'Appliqué', tone: 'blue', Icon: CheckCircle2 },
  pending: { label: 'En attente', tone: 'indigo', Icon: Clock },
  pending_review: { label: 'À valider', tone: 'indigo', Icon: Clock },
  error: { label: 'Erreur', tone: 'coral', Icon: AlertTriangle },
}

export default function StatusBadge({ status }) {
  const config = CONFIG[status] || CONFIG.pending
  const { label, tone, Icon } = config
  return (
    <Badge tone={tone}>
      <Icon size={12} strokeWidth={2.5} />
      {label}
    </Badge>
  )
}
