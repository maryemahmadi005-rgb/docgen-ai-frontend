import { Link } from 'react-router-dom'
import { FileQuestion } from 'lucide-react'
import Button from '../components/ui/Button'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-bg px-6 text-center">
      <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-indigo-400">
        <FileQuestion size={26} strokeWidth={1.75} />
      </div>
      <h1 className="font-display text-2xl font-semibold text-navy-800">Page introuvable</h1>
      <p className="mt-2 max-w-sm text-sm text-ink-muted">
        Cette page n'existe pas ou a été déplacée. Vérifiez l'adresse ou retournez à l'accueil.
      </p>
      <Button as={Link} to="/dashboard" className="mt-6">
        Retour au dashboard
      </Button>
    </div>
  )
}
