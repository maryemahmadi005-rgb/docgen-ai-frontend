import { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'
import { notificationsApi } from '../api/notifications'
import { useAuth } from './AuthContext'
import { useToast } from './ToastContext'

const NotificationsContext = createContext(null)

const POLL_INTERVAL_MS = 20000
const READ_KEYS_STORAGE_PREFIX = 'rs_notif_read_'

/**
 * Turns one repository's notification state (as returned by the backend —
 * see app/api/notifications.py::_compose_notification_state) into zero,
 * one, or two discrete notification events. No event is ever invented:
 * every field used here (version_number, triggered_by, affected_sections,
 * created_at, ids) comes straight from the backend response.
 */
function deriveEvents(repoState) {
  const events = []

  const { repository_id, repository_full_name, latest_version, pending_prompt } = repoState

  if (latest_version && latest_version.triggered_by !== 'initial_generation') {
    const isAuto = latest_version.triggered_by === 'sync_auto'
    events.push({
      key: `${repository_id}:version:${latest_version.version_number}`,
      type: isAuto ? 'README_UPDATED_AUTO' : 'README_UPDATED_MANUAL',
      repositoryId: repository_id,
      repositoryName: repository_full_name,
      versionNumber: latest_version.version_number,
      createdAt: latest_version.created_at,
      title: isAuto
        ? `✅ README mis à jour automatiquement — nouvelle version v${latest_version.version_number} créée.`
        : `✅ README mis à jour — nouvelle version v${latest_version.version_number} créée.`,
    })
  }

  if (pending_prompt) {
    events.push({
      key: `${repository_id}:pending:${pending_prompt.pending_update_id}`,
      type: 'PENDING_UPDATE_CREATED',
      repositoryId: repository_id,
      repositoryName: repository_full_name,
      pendingUpdateId: pending_prompt.pending_update_id,
      affectedSections: pending_prompt.affected_sections || [],
      createdAt: pending_prompt.created_at,
      title: `🔔 Changements détectés : ${(pending_prompt.affected_sections || []).join(', ') || '—'}.`,
    })
  }

  return events
}

export function NotificationsProvider({ children }) {
  const { isAuthenticated, user } = useAuth()
  const toast = useToast()

  const [repoStates, setRepoStates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [readKeys, setReadKeys] = useState(() => new Set())

  const seenKeysRef = useRef(null) // null until first successful poll (avoids toast spam on load)
  const storageKeyRef = useRef(null)

  useEffect(() => {
    storageKeyRef.current = user?.id ? `${READ_KEYS_STORAGE_PREFIX}${user.id}` : null
    if (storageKeyRef.current) {
      try {
        const raw = localStorage.getItem(storageKeyRef.current)
        setReadKeys(new Set(raw ? JSON.parse(raw) : []))
      } catch {
        setReadKeys(new Set())
      }
    } else {
      setReadKeys(new Set())
    }
    seenKeysRef.current = null
  }, [user?.id])

  const persistReadKeys = useCallback((next) => {
    setReadKeys(next)
    if (storageKeyRef.current) {
      try {
        localStorage.setItem(storageKeyRef.current, JSON.stringify(Array.from(next)))
      } catch {
        // localStorage indisponible (mode privé, quota…) — état encore correct en mémoire
      }
    }
  }, [])

  const poll = useCallback(async () => {
    try {
      const data = await notificationsApi.summary()
      const states = data.repositories || []
      setRepoStates(states)
      setError(null)

      const allEvents = states.flatMap(deriveEvents)
      const currentKeys = new Set(allEvents.map((e) => e.key))

      if (seenKeysRef.current) {
        const newEvents = allEvents.filter((e) => !seenKeysRef.current.has(e.key))
        newEvents.forEach((e) => {
          toast.success(e.title)
        })
      }
      seenKeysRef.current = currentKeys
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    if (!isAuthenticated) {
      setRepoStates([])
      setLoading(false)
      seenKeysRef.current = null
      return
    }

    setLoading(true)
    poll()
    const id = setInterval(poll, POLL_INTERVAL_MS)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated])

  const events = repoStates
    .flatMap(deriveEvents)
    .sort((a, b) => new Date(b.createdAt || 0) - new Date(a.createdAt || 0))

  const unreadCount = events.filter((e) => !readKeys.has(e.key)).length

  const markAllRead = useCallback(() => {
    const next = new Set(readKeys)
    events.forEach((e) => next.add(e.key))
    persistReadKeys(next)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events, readKeys, persistReadKeys])

  const pendingReviewCount = repoStates.filter((r) => r.pending_prompt).length
  const totalRepositories = repoStates.length

  return (
    <NotificationsContext.Provider
      value={{
        repoStates,
        events,
        unreadCount,
        markAllRead,
        loading,
        error,
        refresh: poll,
        pendingReviewCount,
        totalRepositories,
      }}
    >
      {children}
    </NotificationsContext.Provider>
  )
}

export function useNotifications() {
  const ctx = useContext(NotificationsContext)
  if (!ctx) throw new Error('useNotifications must be used within NotificationsProvider')
  return ctx
}
