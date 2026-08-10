import { useState } from 'react'
import { AlertCircle } from 'lucide-react'
import Input from './ui/Input'
import Button from './ui/Button'
import Spinner from './ui/Spinner'

/**
 * Formulaire d'authentification générique (Login / Register / Forgot).
 * `fields` décrit les champs affichés, `onSubmit` reçoit les valeurs saisies.
 */
export default function AuthForm({ fields, submitLabel, onSubmit, footer }) {
  const [values, setValues] = useState(() =>
    Object.fromEntries(fields.map((f) => [f.name, ''])),
  )
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleChange = (name) => (e) => {
    setValues((prev) => ({ ...prev, [name]: e.target.value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      await onSubmit(values)
    } catch (err) {
      setError(err.message || 'Une erreur est survenue.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="flex items-start gap-2 rounded-lg bg-coral-100 px-3.5 py-2.5 text-sm text-coral-500">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {fields.map((field) => (
        <Input
          key={field.name}
          id={field.name}
          label={field.label}
          type={field.type || 'text'}
          placeholder={field.placeholder}
          value={values[field.name]}
          onChange={handleChange(field.name)}
          autoComplete={field.autoComplete}
          required
        />
      ))}

      <Button type="submit" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? <Spinner size={16} className="text-white" /> : submitLabel}
      </Button>

      {footer}
    </form>
  )
}
