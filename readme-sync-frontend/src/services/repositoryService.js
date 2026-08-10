import { mockRepositories, mockReadmeContent, mockReadmeVersions } from './mockData'

// ---------------------------------------------------------------------------
// Miroir des routes réelles définies dans repositories.py / readmes.py.
// Aujourd'hui : lit les données mockées. Demain : chaque fonction devient un
// appel api.get/post/patch vers le même chemin (voir commentaires).
// GET    /api/repositories
// POST   /api/repositories
// GET    /api/repositories/:id
// DELETE /api/repositories/:id
// GET    /api/repositories/:id/settings
// PATCH  /api/repositories/:id/settings
// GET    /api/repositories/:id/analysis
// GET    /api/repositories/:id/readme
// PATCH  /api/repositories/:id/readme
// GET    /api/repositories/:id/readme/versions
// ---------------------------------------------------------------------------

function delay(ms = 400) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function listRepositories() {
  await delay()
  return mockRepositories
  // return api.get('/repositories')
}

export async function getRepository(id) {
  await delay()
  const repo = mockRepositories.find((r) => r.id === id)
  if (!repo) throw new Error('Repository introuvable.')
  return repo
  // return api.get(`/repositories/${id}`)
}

export async function createRepository({ githubUrl, fullName, syncMode }) {
  await delay(900)
  if (!githubUrl || !fullName) throw new Error('URL et nom du repository requis.')
  const newRepo = {
    id: 'repo_' + Math.random().toString(36).slice(2, 8),
    fullName,
    description: '',
    defaultBranch: 'main',
    trackedBranch: 'main',
    syncMode: syncMode || 'manual',
    syncMethod: 'webhook',
    status: 'pending',
    lastSyncAt: null,
    connectedAt: new Date().toISOString(),
    readmeUpdatedCount: 0,
    pendingUpdates: 0,
  }
  mockRepositories.unshift(newRepo)
  return newRepo
  // return api.post('/repositories', { github_url: githubUrl, full_name: fullName, sync_mode: syncMode })
}

export async function deleteRepository(id) {
  await delay()
  const idx = mockRepositories.findIndex((r) => r.id === id)
  if (idx >= 0) mockRepositories.splice(idx, 1)
  // return api.delete(`/repositories/${id}`)
}

export async function getRepositorySettings(id) {
  await delay()
  const repo = mockRepositories.find((r) => r.id === id)
  if (!repo) throw new Error('Repository introuvable.')
  return {
    syncMode: repo.syncMode,
    syncMethod: repo.syncMethod,
    trackedBranch: repo.trackedBranch,
    defaultBranch: repo.defaultBranch,
  }
  // return api.get(`/repositories/${id}/settings`)
}

export async function updateRepositorySettings(id, updates) {
  await delay()
  const repo = mockRepositories.find((r) => r.id === id)
  if (!repo) throw new Error('Repository introuvable.')
  Object.assign(repo, updates)
  return repo
  // return api.patch(`/repositories/${id}/settings`, updates)
}

export async function getRepositoryReadme(id) {
  await delay()
  return {
    contentMd: mockReadmeContent[id] || '# README\n\nAucun contenu généré pour le moment.',
  }
  // return api.get(`/repositories/${id}/readme`)
}

export async function updateRepositoryReadme(id, contentMd) {
  await delay(500)
  mockReadmeContent[id] = contentMd
  return { contentMd }
  // return api.patch(`/repositories/${id}/readme`, { content_md: contentMd })
}

export async function listReadmeVersions(id) {
  await delay()
  return mockReadmeVersions[id] || []
  // return api.get(`/repositories/${id}/readme/versions`)
}
