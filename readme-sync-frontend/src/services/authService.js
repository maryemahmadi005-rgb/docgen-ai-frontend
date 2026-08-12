import { api, saveAccessToken, clearTokens } from './api'

// ---------------------------------------------------------------------------
// Login
// ---------------------------------------------------------------------------

export async function login({ email, password }) {
  const data = await api.post('/auth/login', {
    email,
    password,
  })

  if (!data.access_token) {
    throw new Error('Le serveur n’a pas retourné de access_token.')
  }

  if (!data.refresh_token) {
    throw new Error('Le serveur n’a pas retourné de refresh_token.')
  }

  // Access token utilisé pour les requêtes normales
  saveAccessToken(data.access_token)

  // Refresh token utilisé pour renouveler automatiquement
  localStorage.setItem(
    'readme_sync_refresh_token',
    data.refresh_token,
  )

  return {
    user: data.user,
    access_token: data.access_token,
    refresh_token: data.refresh_token,
  }
}

// ---------------------------------------------------------------------------
// Register
// ---------------------------------------------------------------------------

export async function register({ name, email, password }) {
  const data = await api.post('/auth/register', {
    name,
    email,
    password,
  })

  if (!data.access_token) {
    throw new Error('Le serveur n’a pas retourné de access_token.')
  }

  if (!data.refresh_token) {
    throw new Error('Le serveur n’a pas retourné de refresh_token.')
  }

  saveAccessToken(data.access_token)

  localStorage.setItem(
    'readme_sync_refresh_token',
    data.refresh_token,
  )

  return {
    user: data.user,
    access_token: data.access_token,
    refresh_token: data.refresh_token,
  }
}

// ---------------------------------------------------------------------------
// Current user
// ---------------------------------------------------------------------------

export async function getCurrentUser() {
  return api.get('/auth/me')
}

// ---------------------------------------------------------------------------
// Logout
// ---------------------------------------------------------------------------

export function logout() {
  clearTokens()
}

// ---------------------------------------------------------------------------
// Forgot password
// ---------------------------------------------------------------------------

export async function forgotPassword({ email }) {
  return api.post('/auth/forgot-password', {
    email,
  })
}