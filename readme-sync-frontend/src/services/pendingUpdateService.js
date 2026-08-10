import { mockPendingUpdates } from './mockData'

// ---------------------------------------------------------------------------
// Miroir de pending_updates.py :
// GET  /api/pending-updates/:id
// POST /api/pending-updates/:id/approve
// POST /api/pending-updates/:id/reject
// La vue globale (nav "Pending Updates") agrège par repo, comme dans le
// vrai backend qui n'expose pas de liste globale — cf. GET
// /api/repositories/:id/pending-updates. Ici, mock unique = déjà agrégé.
// ---------------------------------------------------------------------------

function delay(ms = 400) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function listPendingUpdates() {
  await delay()
  return mockPendingUpdates.filter((u) => u.status !== 'approved' && u.status !== 'rejected')
}

export async function listPendingUpdatesForRepository(repositoryId) {
  await delay()
  return mockPendingUpdates.filter((u) => u.repositoryId === repositoryId)
}

export async function getPendingUpdate(id) {
  await delay()
  const update = mockPendingUpdates.find((u) => u.id === id)
  if (!update) throw new Error('Proposition introuvable.')
  return update
}

export async function approvePendingUpdate(id) {
  await delay(600)
  const update = mockPendingUpdates.find((u) => u.id === id)
  if (!update) throw new Error('Proposition introuvable.')
  if (update.status && update.status !== 'pending') {
    throw new Error("Cette proposition n'est plus en attente.")
  }
  update.status = 'approved'
  return update
}

export async function rejectPendingUpdate(id, reason) {
  await delay(500)
  const update = mockPendingUpdates.find((u) => u.id === id)
  if (!update) throw new Error('Proposition introuvable.')
  if (update.status && update.status !== 'pending') {
    throw new Error("Cette proposition n'est plus en attente.")
  }
  update.status = 'rejected'
  update.rejectionReason = reason || null
  return update
}
