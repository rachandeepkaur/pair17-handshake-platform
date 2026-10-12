import { useCallback, useEffect, useState } from 'react'
import { errorMessage } from '../services/api'

// Fetch on mount (and whenever `deps` change), tracking loading/error.
// `setData` lets callers patch the result locally after a mutation instead
// of refetching; `reload` refetches.
export function useFetch(fetcher, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const load = useCallback(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    fetcher()
      .then((result) => !cancelled && setData(result))
      .catch((err) => !cancelled && setError(errorMessage(err, 'Failed to load data.')))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, deps)

  // Cancelling on cleanup stops a slow earlier request from overwriting a
  // newer one when deps change quickly (e.g. typing in a search box).
  useEffect(() => load(), [load])

  return { data, loading, error, reload: load, setData }
}
