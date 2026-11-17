import { createContext } from 'react'

// Kept apart from AuthProvider so that file only exports components (fast refresh).
export const AuthContext = createContext(null)
