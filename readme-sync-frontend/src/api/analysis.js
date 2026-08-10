import client from './client'

export const analysisApi = {
  getLatest: (repoId) => client.get(`/repositories/${repoId}/analyses/latest`).then((r) => r.data),
}
