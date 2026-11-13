import { createContext, useState } from 'react'
import * as authService from '../services/authService'

export const AuthContext = createContext(null)

// Storage is written synchronously (not in an effect) so the very first API
// call made by the page we navigate to already carries the new token.
function persist(token, role) {
  // A new session (sign-in or sign-out) never inherits another user's chat.
  sessionStorage.removeItem('assistant-conversation')
  if (token && role) {
    localStorage.setItem('token', token)
    localStorage.setItem('role', role)
  } else {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [role, setRole] = useState(() => localStorage.getItem('role'))

  const startSession = ({ access_token: accessToken, role: nextRole }) => {
    persist(accessToken, nextRole)
    setToken(accessToken)
    setRole(nextRole)
  }

  const login = async (credentials) => {
    const data = await authService.login(credentials)
    startSession(data)
    return data
  }

  // Sessions live on the server (MongoDB): end it there so the token stops
  // working and the assistant compacts this session's conversation. The local
  // sign-out happens regardless of whether that request succeeds.
  const logout = () => {
    authService.logout().catch(() => {})
    persist(null, null)
    setToken(null)
    setRole(null)
  }

  const value = {
    token,
    role,
    isAuthenticated: Boolean(token),
    login,
    logout,
    startSession,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
