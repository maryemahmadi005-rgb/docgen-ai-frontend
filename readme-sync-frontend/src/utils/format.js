export function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export function formatDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export function timeAgo(iso) {
  if (!iso) return '—'
  const diffMs = Date.now() - new Date(iso).getTime()
  const sec = Math.floor(diffMs / 1000)
  if (sec < 60) return 'just now'
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  const day = Math.floor(hr / 24)
  if (day < 30) return `${day}d ago`
  const month = Math.floor(day / 30)
  if (month < 12) return `${month}mo ago`
  return `${Math.floor(month / 12)}y ago`
}

export function shortSha(sha) {
  if (!sha) return '—'
  return sha.slice(0, 7)
}

export function parseGithubUrl(url) {
  if (!url) return null
  try {
    const cleaned = url.trim().replace(/\.git$/, '').replace(/\/$/, '')
    const match = cleaned.match(/github\.com[/:]([^/]+)\/([^/]+)$/i)
    if (match) return `${match[1]}/${match[2]}`
    // Already in owner/repo form
    if (/^[^/\s]+\/[^/\s]+$/.test(cleaned)) return cleaned
    return null
  } catch {
    return null
  }
}

export function toGithubUrl(fullName) {
  return `https://github.com/${fullName}`
}

export const triggeredByLabels = {
  initial_generation: 'Initial generation',
  manual_edit: 'Manual edit',
  sync_auto: 'Automatic sync',
  sync_manual_approved: 'Manual sync (approved)',
}

export const triggeredByVariants = {
  initial_generation: 'info',
  manual_edit: 'neutral',
  sync_auto: 'success',
  sync_manual_approved: 'success',
}

export const pendingStatusVariants = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  stale: 'neutral',
}

/** Time-of-day greeting — purely presentational, computed from the local clock. */
export function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

/** Display name derived from real user fields only (no hardcoded name). */
export function getDisplayName(user) {
  if (!user) return ''
  if (user.github_username) return user.github_username
  if (user.email) return user.email.split('@')[0]
  return ''
}

/**
 * Derives a repository's sync status label from real backend fields —
 * never invented client-side state. Backed by the same notification state
 * (pending_prompt / latest_version) exposed by /api/notifications/summary.
 */
export function deriveRepoStatus(repoNotifState) {
  if (!repoNotifState) return { key: 'unknown', label: 'No data yet', variant: 'neutral' }
  if (repoNotifState.pending_prompt) {
    return { key: 'review_required', label: 'Review required', variant: 'warning' }
  }
  if (repoNotifState.latest_version) {
    return { key: 'synced', label: 'Synced', variant: 'success' }
  }
  return { key: 'no_readme', label: 'No README yet', variant: 'neutral' }
}
