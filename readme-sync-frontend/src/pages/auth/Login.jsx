import { Link, useNavigate, useLocation } from 'react-router-dom'
import AuthForm from '../../components/AuthForm'
import { useAuth } from '../../hooks/useAuth'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleSubmit = async (values) => {
    await login({ email: values.email, password: values.password })
    const redirectTo = location.state?.from || '/dashboard'
    navigate(redirectTo, { replace: true })
  }

  return (
    <div>
      <div className="mb-8 space-y-1.5">
        <h1 className="font-display text-2xl font-semibold text-navy-800">Connexion</h1>
        <p className="text-sm text-ink-muted">
          Accédez à vos repositories et à leurs propositions de synchronisation.
        </p>
      </div>

      <AuthForm
        fields={[
          { name: 'email', label: 'Email', type: 'email', placeholder: 'vous@exemple.com', autoComplete: 'email' },
          { name: 'password', label: 'Mot de passe', type: 'password', placeholder: '••••••••', autoComplete: 'current-password' },
        ]}
        submitLabel="Se connecter"
        onSubmit={handleSubmit}
        footer={
          <div className="flex items-center justify-between pt-1 text-sm">
            <Link to="/forgot-password" className="text-blue-700 hover:underline">
              Mot de passe oublié ?
            </Link>
            <Link to="/register" className="text-ink-muted hover:text-navy-800">
              Créer un compte
            </Link>
          </div>
        }
      />

      <p className="mt-6 text-center text-xs text-ink-muted">
        Démo : n'importe quel email + mot de passe (4 caractères min).
      </p>
    </div>
  )
}
