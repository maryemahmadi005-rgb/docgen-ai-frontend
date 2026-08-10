import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api'

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// --- Token storage helpers ---
export const tokenStorage = {
  getAccess: () => localStorage.getItem('rs_access_token'),
  getRefresh: () => localStorage.getItem('rs_refresh_token'),
  set: (accessToken, refreshToken) => {
    localStorage.setItem('rs_access_token', accessToken)
    if (refreshToken) localStorage.setItem('rs_refresh_token', refreshToken)
  },
  setAccess: (accessToken) => {
    localStorage.setItem('rs_access_token', accessToken)
  },
  clear: () => {
    localStorage.removeItem('rs_access_token')
    localStorage.removeItem('rs_refresh_token')
  },
}

// --- Request interceptor: attach access token ---
client.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// --- Response interceptor: handle 401 with a single refresh attempt ---
let isRefreshing = false
let refreshQueue = []

function resolveQueue(error, token = null) {
  refreshQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token)
  })
  refreshQueue = []
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status

    const isAuthRoute =
      originalRequest?.url?.includes('/auth/login') ||
      originalRequest?.url?.includes('/auth/register') ||
      originalRequest?.url?.includes('/auth/refresh')

    if (status === 401 && !originalRequest._retry && !isAuthRoute) {
      const refreshToken = tokenStorage.getRefresh()

      if (!refreshToken) {
        tokenStorage.clear()
        window.dispatchEvent(new CustomEvent('auth:logout'))
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          refreshQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return client(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const res = await axios.post(
          `${API_URL}/auth/refresh`,
          {},
          { headers: { Authorization: `Bearer ${refreshToken}` } }
        )
        const newAccessToken = res.data.access_token
        tokenStorage.setAccess(newAccessToken)
        resolveQueue(null, newAccessToken)
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return client(originalRequest)
      } catch (refreshError) {
        resolveQueue(refreshError, null)
        tokenStorage.clear()
        window.dispatchEvent(new CustomEvent('auth:logout'))
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

/**
 * Extracts a human-readable message from an API error.
 * The backend returns { "error": "..." } for known failure cases.
 */
export function getErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  if (error?.response?.data?.error) return error.response.data.error
  if (error?.message === 'Network Error') return 'Cannot reach the server. Check your connection.'
  return fallback
}

export default client
