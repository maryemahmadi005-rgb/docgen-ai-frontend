// ---------------------------------------------------------------------------
// API centralisée — connexion avec le backend Flask
// ---------------------------------------------------------------------------

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  'http://localhost:5000/api'

// ---------------------------------------------------------------------------
// Tokens
// ---------------------------------------------------------------------------

function getAccessToken() {
  return localStorage.getItem('readme_sync_token')
}

function getRefreshToken() {
  return localStorage.getItem('readme_sync_refresh_token')
}

function saveAccessToken(token) {
  if (token) {
    localStorage.setItem('readme_sync_token', token)
  }
}

function clearTokens() {
  localStorage.removeItem('readme_sync_token')
  localStorage.removeItem('readme_sync_refresh_token')
}

// ---------------------------------------------------------------------------
// Refresh access token
// ---------------------------------------------------------------------------

let refreshPromise = null

async function refreshAccessToken() {
  const refreshToken = getRefreshToken()

  if (!refreshToken) {
    return null
  }

  if (refreshPromise) {
    return refreshPromise
  }

  refreshPromise = fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${refreshToken}`,
      'Content-Type': 'application/json',
    },
  })
    .then(async (response) => {
      if (!response.ok) {
        clearTokens()
        return null
      }

      const data = await response.json()

      if (!data.access_token) {
        clearTokens()
        return null
      }

      saveAccessToken(data.access_token)

      return data.access_token
    })
    .catch(() => {
      clearTokens()
      return null
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

// ---------------------------------------------------------------------------
// Request principale
// ---------------------------------------------------------------------------

async function request(
  path,
  {
    method = 'GET',
    body,
    headers = {},
    retry = true,
  } = {},
) {
  const token = getAccessToken()

  const requestHeaders = {
    'Content-Type': 'application/json',
    ...headers,
  }

  if (token) {
    requestHeaders.Authorization = `Bearer ${token}`
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: requestHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  // -------------------------------------------------------------------------
  // Access token expiré
  // -------------------------------------------------------------------------

  if (res.status === 401 && retry) {
    const newToken = await refreshAccessToken()

    if (newToken) {
      return request(path, {
        method,
        body,
        headers,
        retry: false,
      })
    }

    clearTokens()
  }

  // -------------------------------------------------------------------------
  // Erreur API
  // -------------------------------------------------------------------------

  if (!res.ok) {
    const errorBody = await res
      .json()
      .catch(() => ({}))

    throw new Error(
      errorBody.message ||
      errorBody.error ||
      `Erreur API (${res.status})`,
    )
  }

  // -------------------------------------------------------------------------
  // No Content
  // -------------------------------------------------------------------------

  if (res.status === 204) {
    return null
  }

  return res.json()
}

// ---------------------------------------------------------------------------
// API publique
// ---------------------------------------------------------------------------

export const api = {
  get: (path) =>
    request(path),

  post: (path, body) =>
    request(path, {
      method: 'POST',
      body,
    }),

  patch: (path, body) =>
    request(path, {
      method: 'PATCH',
      body,
    }),

  put: (path, body) =>
    request(path, {
      method: 'PUT',
      body,
    }),

  delete: (path) =>
    request(path, {
      method: 'DELETE',
    }),
}

// ---------------------------------------------------------------------------
// Helpers exportés pour l'authentification
// ---------------------------------------------------------------------------

export {
  getAccessToken,
  getRefreshToken,
  saveAccessToken,
  clearTokens,
}