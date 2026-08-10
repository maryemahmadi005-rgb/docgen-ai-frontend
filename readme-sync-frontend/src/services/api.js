// ---------------------------------------------------------------------------
// Couche API centrale — pour l'instant un wrapper fetch prêt à brancher sur
// le backend Flask (voir README-Sync-Platform: POST /api/webhooks/github,
// etc.). Tous les services (authService, repositoryService, ...) doivent
// passer par ici plutôt que d'appeler fetch() directement, pour garder un
// seul endroit à modifier quand le backend sera connecté.
// ---------------------------------------------------------------------------

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'

function getToken() {
  return localStorage.getItem('readme_sync_token')
}

async function request(path, { method = 'GET', body, headers = {} } = {}) {
  const token = getToken()

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}))
    throw new Error(errorBody.message || `Erreur API (${res.status})`)
  }

  if (res.status === 204) return null
  return res.json()
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  delete: (path) => request(path, { method: 'DELETE' }),
}
