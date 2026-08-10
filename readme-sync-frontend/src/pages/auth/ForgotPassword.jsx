import { useState } from 'react'
import { Link } from 'react-router-dom'
import { MailCheck } from 'lucide-react'
import AuthForm from '../../components/AuthForm'
import { useAuth } from '../../hooks/useAuth'

export default function ForgotPassword() {
  const { forgotPassword } = useAuth()
  const [sent, setSent] = useState(false)
  const [message, setMessage] = useState('')

  const handleSubmit = async (values) => {
    const res = await forgotPassword({ email: values.email })
    setMessage(res.message)
    setSent(true)
  }

  if (sent) {
    return (
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-700/10 text-blue-700">
          <MailCheck size={22} />
        </div>
        <h1 className="font-display text-xl font-semibold text-navy-800">Email envoyé</h1>
        <p className="mt-2 text-sm text-ink-muted">{message}</p>
        <Link to="/login" className="mt-6 inline-block text-sm text-blue-700 hover:underline">
          Retour à la connexion
        </Link>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8 space-y-1.5">
        <h1 className="font-display text-2xl font-semibold text-navy-800">Mot de passe oublié</h1>
        <p className="text-sm text-ink-muted">
          Indiquez votre email, nous vous enverrons un lien de réinitialisation.
        </p>
      </div>

      <AuthForm
        fields={[
          { name: 'email', label: 'Email', type: 'email', placeholder: 'vous@exemple.com', autoComplete: 'email' },
        ]}
        submitLabel="Envoyer le lien"
        onSubmit={handleSubmit}
        footer={
          <p className="pt-1 text-center text-sm text-ink-muted">
            <Link to="/login" className="text-blue-700 hover:underline">
              Retour à la connexion
            </Link>
          </p>
        }
      />
    </div>
  )
}
