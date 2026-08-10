import client from './client'

export const repositoriesApi = {
  list: () => client.get('/repositories').then((r) => r.data),

  get: (repoId) => client.get(`/repositories/${repoId}`).then((r) => r.data),

  /**
   * Backend requires github_url AND full_name (owner/repo).
   * Optional: default_branch, sync_mode ('manual'|'automatic'), sync_method ('webhook'|'polling').
   */
  create: ({ github_url, full_name, default_branch, sync_mode, sync_method }) =>
    client
      .post('/repositories', { github_url, full_name, default_branch, sync_mode, sync_method })
      .then((r) => r.data),

  updateSyncMode: (repoId, syncMode) =>
    client
      .patch(`/repositories/${repoId}/sync-mode`, { sync_mode: syncMode })
      .then((r) => r.data),

  delete: (repoId) => client.delete(`/repositories/${repoId}`).then((r) => r.data),

  listCommits: (repoId, { limit = 50, offset = 0 } = {}) =>
    client
      .get(`/repositories/${repoId}/commits`, { params: { limit, offset } })
      .then((r) => r.data),

  getLatestAnalysis: (repoId) =>
    client.get(`/repositories/${repoId}/analyses/latest`).then((r) => r.data),

  /** Manual trigger — initial README generation (clone + analyze + Ollama). */
  generate: (repoId) =>
    client.post(`/repositories/${repoId}/generate`).then((r) => r.data),
}