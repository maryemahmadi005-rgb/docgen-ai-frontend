import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from 'react'

import { authApi } from '../api/auth'
import {
  tokenStorage,
  getErrorMessage,
} from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [authError, setAuthError] = useState(null)

  // --------------------------------------------------------
  // Restore session
  // --------------------------------------------------------

  const restoreSession = useCallback(async () => {
    const token = tokenStorage.getAccess()

    if (!token) {
      setIsLoading(false)
      return
    }

    try {
      const me = await authApi.me()
      setUser(me)
    } catch {
      tokenStorage.clear()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    restoreSession()
  }, [restoreSession])

  // --------------------------------------------------------
  // Refresh current user
  // --------------------------------------------------------

  const refreshUser = useCallback(async () => {
    const token = tokenStorage.getAccess()

    if (!token) {
      setUser(null)
      return null
    }

    const me = await authApi.me()

    setUser(me)

    return me
  }, [])

  // --------------------------------------------------------
  // Forced logout
  // --------------------------------------------------------

  useEffect(() => {
    const handleForcedLogout = () => {
      setUser(null)
    }

    window.addEventListener(
      'auth:logout',
      handleForcedLogout
    )

    return () => {
      window.removeEventListener(
        'auth:logout',
        handleForcedLogout
      )
    }
  }, [])

  // --------------------------------------------------------
  // Login
  // --------------------------------------------------------

  const login = useCallback(
    async (email, password) => {
      setAuthError(null)

      try {
        const data = await authApi.login(
          email,
          password
        )

        tokenStorage.set(
          data.access_token,
          data.refresh_token
        )

        setUser(data.user)

        return {
          success: true,
        }
      } catch (err) {
        const message = getErrorMessage(
          err,
          'Unable to sign in.'
        )

        setAuthError(message)

        return {
          success: false,
          error: message,
        }
      }
    },
    []
  )

  // --------------------------------------------------------
  // Register
  // --------------------------------------------------------

  const register = useCallback(
    async (email, password) => {
      setAuthError(null)

      try {
        const data = await authApi.register(
          email,
          password
        )

        tokenStorage.set(
          data.access_token,
          data.refresh_token
        )

        setUser(data.user)

        return {
          success: true,
        }
      } catch (err) {
        const message = getErrorMessage(
          err,
          'Unable to create your account.'
        )

        setAuthError(message)

        return {
          success: false,
          error: message,
        }
      }
    },
    []
  )

  // --------------------------------------------------------
  // Logout
  // --------------------------------------------------------

  const logout = useCallback(() => {
    tokenStorage.clear()
    setUser(null)
    setAuthError(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        authError,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)

  if (!ctx) {
    throw new Error(
      'useAuth must be used within AuthProvider'
    )
  }

  return ctx
}