import { useCallback, useEffect, useState } from 'react'

// Generic "fetch on mount, track loading/error" hook shared by any page
// that loads data from the API (dashboards, lists, detail views).
export function useFetch(fetcher, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const load = useCallback(() => {
    setLoading(true)
    setError('')
    fetcher()
      .then(setData)
      .catch((err) => setError(err?.response?.data?.detail || 'Failed to load data.'))
      .finally(() => setLoading(false))
  }, deps)

  useEffect(() => {
    load()
  }, [load])

  return { data, loading, error, reload: load }
}
