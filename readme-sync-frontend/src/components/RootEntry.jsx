import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Spinner } from './ui/Primitives'
import IntroPage from '../pages/IntroPage'

/**
 * Entry point at "/".
 * - Authenticated users skip straight to the dashboard.
 * - Once the cinematic intro has been seen this session, later visits to "/"
 *   go straight to login instead of replaying the animation.
 * - Otherwise, the intro plays.
 */
export default function RootEntry() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <Spinner size={26} />
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  const introSeen = sessionStorage.getItem('rs_intro_seen') === '1'
  if (introSeen) {
    return <Navigate to="/login" replace />
  }

  return <IntroPage />
}
