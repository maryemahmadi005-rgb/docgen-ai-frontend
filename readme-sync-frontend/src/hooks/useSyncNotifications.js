import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { repositoriesApi } from '../api/repositories'
import { notificationsApi } from '../api/notifications'
import { pendingUpdatesApi } from '../api/pendingUpdates'
import { getErrorMessage } from '../api/client'

const POLL_INTERVAL_MS = 15000
const STORAGE_PREFIX = 'docgen_sync_notif_'

function readState(repoId) {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_PREFIX + repoId) || '{}')
  } catch {
    return {}
  }
}

function writeState(repoId, state) {
  localStorage.setItem(STORAGE_PREFIX + repoId, JSON.stringify(state))
}

/**
 * Notifications de synchronisation README.
 *
 * Ne réimplémente aucune logique métier : lit GET /repositories/:id/notifications/latest
 * (lui-même une simple lecture de readme_versions / pending_updates, déjà tenus à jour
 * par SyncOrchestrator) et, pour "Oui", appelle l'endpoint d'approbation existant
 * (POST /pending-updates/:id/approve). "Non" ne fait aucun appel — la proposition reste
 * pending côté backend, exactement comme demandé.
 */
export function useSyncNotifications() {
  const { isAuthenticated } = useAuth()
  const toast = useToast()

  // Prompts MANUAL en attente de décision utilisateur (Oui/Non)
  const [prompts, setPrompts] = useState([])
  // Dernière version affichable après un sync AUTOMATIC ou une approbation MANUAL
  const [readmePreview, setReadmePreview] = useState(null)
  const [busyPromptId, setBusyPromptId] = useState(null)

  const pollingRef = useRef(false)

  const poll = useCallback(async () => {
    if (pollingRef.current) return
    pollingRef.current = true
    try {
      const repos = await repositoriesApi.list()

      for (const repo of repos) {
        let data
        try {
          data = await notificationsApi.latest(repo.id)
        } catch {
          continue // repo pas encore prêt (pas de README, etc.) — on ignore silencieusement
        }

        const stored = readState(repo.id)

        // --- AUTOMATIC : nouvelle version publiée toute seule ---
        if (data.latest_version) {
          const versionNumber = data.latest_version.version_number
          if (stored.lastVersion === undefined) {
            // Première fois qu'on voit ce repo : on prend juste une référence,
            // pas de notification rétroactive sur l'historique déjà existant.
            stored.lastVersion = versionNumber
          } else if (versionNumber > stored.lastVersion) {
            if (data.latest_version.triggered_by === 'sync_auto') {
              toast.success(
                `✅ README mis à jour automatiquement — nouvelle version v${versionNumber} créée.`
              )
              setReadmePreview({
                repoId: repo.id,
                repoName: repo.full_name,
                versionNumber,
                contentMd: data.latest_version.content_md,
              })
            }
            stored.lastVersion = versionNumber
          }
        }

        // --- MANUAL : changement détecté, décision utilisateur requise ---
        if (data.pending_prompt) {
          const pendingUpdateId = data.pending_prompt.pending_update_id
          if (stored.dismissedPendingId !== pendingUpdateId) {
            setPrompts((prev) =>
              prev.some((p) => p.pendingUpdateId === pendingUpdateId)
                ? prev
                : [
                    ...prev,
                    {
                      repoId: repo.id,
                      repoName: repo.full_name,
                      pendingUpdateId,
                      affectedSections: data.pending_prompt.affected_sections || [],
                    },
                  ]
            )
          }
        } else {
          stored.dismissedPendingId = null
          setPrompts((prev) => prev.filter((p) => p.repoId !== repo.id))
        }

        writeState(repo.id, stored)
      }
    } catch {
      // silencieux : la notification est un enrichissement, pas un flux critique
    } finally {
      pollingRef.current = false
    }
  }, [toast])

  useEffect(() => {
    if (!isAuthenticated) return
    poll()
    const interval = setInterval(poll, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [isAuthenticated, poll])

  const approvePrompt = useCallback(
    async (prompt) => {
      setBusyPromptId(prompt.pendingUpdateId)
      try {
        await pendingUpdatesApi.approve(prompt.repoId, prompt.pendingUpdateId)
        const fresh = await notificationsApi.latest(prompt.repoId)
        const versionNumber = fresh.latest_version?.version_number

        toast.success(
          versionNumber
            ? `✅ README mis à jour — nouvelle version v${versionNumber} créée.`
            : '✅ README mis à jour.'
        )

        if (fresh.latest_version) {
          setReadmePreview({
            repoId: prompt.repoId,
            repoName: prompt.repoName,
            versionNumber,
            contentMd: fresh.latest_version.content_md,
          })
          writeState(prompt.repoId, { lastVersion: versionNumber, dismissedPendingId: null })
        }

        setPrompts((prev) => prev.filter((p) => p.pendingUpdateId !== prompt.pendingUpdateId))
      } catch (err) {
        toast.error(getErrorMessage(err, "Échec de la mise à jour du README."))
      } finally {
        setBusyPromptId(null)
      }
    },
    [toast]
  )

  const declinePrompt = useCallback((prompt) => {
    // "Non" : on ne modifie rien côté backend, on arrête juste de re-proposer
    // cette même proposition (elle reste 'pending' et reste visible dans
    // l'onglet Pending Updates si l'utilisateur veut y revenir plus tard).
    const stored = readState(prompt.repoId)
    stored.dismissedPendingId = prompt.pendingUpdateId
    writeState(prompt.repoId, stored)
    setPrompts((prev) => prev.filter((p) => p.pendingUpdateId !== prompt.pendingUpdateId))
  }, [])

  const closeReadmePreview = useCallback(() => setReadmePreview(null), [])

  return {
    prompts,
    readmePreview,
    busyPromptId,
    approvePrompt,
    declinePrompt,
    closeReadmePreview,
  }
}
