import { createContext, useEffect, useState } from 'react'
import * as authService from '../services/authService'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [role, setRole] = useState(() => localStorage.getItem('role'))

  useEffect(() => {
    if (token && role) {
      localStorage.setItem('token', token)
      localStorage.setItem('role', role)
    } else {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
    }
  }, [token, role])

  const login = async (credentials) => {
    const data = await authService.login(credentials)
    setToken(data.access_token)
    setRole(data.role)
    return data
  }

  // JWTs are stateless, so signing out is purely a client-side action:
  // drop the token and every protected route redirects on its own.
  const logout = () => {
    setToken(null)
    setRole(null)
  }

  const value = {
    token,
    role,
    isAuthenticated: Boolean(token),
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
