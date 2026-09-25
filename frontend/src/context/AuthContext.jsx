import { createContext, useContext, useEffect, useState } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = localStorage.getItem('safewatch_user')
    if (stored) setUser(JSON.parse(stored))
    if (localStorage.getItem('safewatch_token')) {
      api
        .me()
        .then((data) => {
          setUser(data.user)
          localStorage.setItem('safewatch_user', JSON.stringify(data.user))
        })
        .catch(() => logout())
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  async function login(email, password) {
    const data = await api.login({ email, password })
    localStorage.setItem('safewatch_token', data.token)
    localStorage.setItem('safewatch_user', JSON.stringify(data.user))
    setUser(data.user)
    return data.user
  }

  async function register(payload) {
    await api.register(payload)
    return login(payload.email, payload.password)
  }

  function logout() {
    localStorage.removeItem('safewatch_token')
    localStorage.removeItem('safewatch_user')
    setUser(null)
  }

  async function refreshUser() {
    const data = await api.me()
    setUser(data.user)
    localStorage.setItem('safewatch_user', JSON.stringify(data.user))
    return data.user
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
