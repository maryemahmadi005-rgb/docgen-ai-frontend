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
