import client from './client'

export const readmesApi = {
  get: (repoId) => client.get(`/repositories/${repoId}/readme`).then((r) => r.data),

  /** Manual edit -> creates a new version (triggered_by='manual_edit') */
  update: (repoId, { content_md, sections_json }) =>
    client
      .put(`/repositories/${repoId}/readme`, { content_md, sections_json })
      .then((r) => r.data),

  listVersions: (repoId) =>
    client.get(`/repositories/${repoId}/readme/versions`).then((r) => r.data),

  getVersion: (repoId, versionNumber) =>
    client
      .get(`/repositories/${repoId}/readme/versions/${versionNumber}`)
      .then((r) => r.data),

  rollbackToVersion: (repoId, versionNumber) =>
    client
      .post(`/repositories/${repoId}/readme/versions/${versionNumber}/rollback`)
      .then((r) => r.data),
}
