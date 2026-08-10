import { mockScans, mockScanDetails } from './mockData'

// ---------------------------------------------------------------------------
// Correspond côté backend aux commits/detected_changes exposés en lecture
// (pas de blueprint /scans dédié dans l'architecture finale — ces données
// vivent sous repository_id ; on les garde ici pour la page Scans qui les
// agrège toutes repos confondus, comme Pending Updates le fait).
// ---------------------------------------------------------------------------

function delay(ms = 400) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function listScans() {
  await delay()
  return mockScans
}

export async function getScan(id) {
  await delay()
  const scan = mockScans.find((s) => s.id === id)
  if (!scan) throw new Error('Scan introuvable.')
  const details = mockScanDetails[id] || { sectionsDiff: {}, fileChanges: [] }
  return { ...scan, ...details }
}
