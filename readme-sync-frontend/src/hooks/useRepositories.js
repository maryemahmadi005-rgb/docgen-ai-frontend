import { useMemo, useState } from 'react'
import { mockRepositories } from '../services/mockData'

/**
 * Pour l'instant basé sur les données mockées. À terme, remplacera l'appel
 * par GET /api/repositories via services/api.js et gèrera loading/error.
 */
export function useRepositories() {
  const [repositories] = useState(mockRepositories)

  const findById = (id) => repositories.find((r) => r.id === id)

  const summary = useMemo(
    () => ({
      total: repositories.length,
      synced: repositories.filter((r) => r.status === 'synced').length,
      pending: repositories.filter((r) => r.status === 'pending').length,
      error: repositories.filter((r) => r.status === 'error').length,
    }),
    [repositories],
  )

  return { repositories, findById, summary, isLoading: false }
}
