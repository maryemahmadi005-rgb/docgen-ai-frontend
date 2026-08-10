import { Link, useNavigate } from 'react-router-dom'
import AuthForm from '../../components/AuthForm'
import { useAuth } from '../../hooks/useAuth'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (values) => {
    await register({ name: values.name, email: values.email, password: values.password })
    navigate('/dashboard', { replace: true })
  }

  return (
    <div>
      <div className="mb-8 space-y-1.5">
        <h1 className="font-display text-2xl font-semibold text-navy-800">Créer un compte</h1>
        <p className="text-sm text-ink-muted">
          Connectez vos repositories GitHub en quelques minutes.
        </p>
      </div>

      <AuthForm
        fields={[
          { name: 'name', label: 'Nom', type: 'text', placeholder: 'Votre nom', autoComplete: 'name' },
          { name: 'email', label: 'Email', type: 'email', placeholder: 'vous@exemple.com', autoComplete: 'email' },
          { name: 'password', label: 'Mot de passe', type: 'password', placeholder: '••••••••', autoComplete: 'new-password' },
        ]}
        submitLabel="Créer mon compte"
        onSubmit={handleSubmit}
        footer={
          <p className="pt-1 text-center text-sm text-ink-muted">
            Déjà inscrit ?{' '}
            <Link to="/login" className="text-blue-700 hover:underline">
              Se connecter
            </Link>
          </p>
        }
      />
    </div>
  )
}
