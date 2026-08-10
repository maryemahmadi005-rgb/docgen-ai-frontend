import client from './client'

export const pendingUpdatesApi = {
  list: (repoId, status = null) =>
    client
      .get(`/repositories/${repoId}/pending-updates`, {
        params: status ? { status } : {},
      })
      .then((r) => r.data),

  get: (repoId, updateId) =>
    client.get(`/repositories/${repoId}/pending-updates/${updateId}`).then((r) => r.data),

  /** No body sent — matches backend contract exactly */
  approve: (repoId, updateId) =>
    client.post(`/repositories/${repoId}/pending-updates/${updateId}/approve`).then((r) => r.data),

  reject: (repoId, updateId, reason) =>
    client
      .post(`/repositories/${repoId}/pending-updates/${updateId}/reject`, reason ? { reason } : {})
      .then((r) => r.data),
}
