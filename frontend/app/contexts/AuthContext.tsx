'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import { login as apiLogin } from "@/app/utils/api"

interface User {
  id?: string
  email: string
  username: string
  is_staff: boolean
  require_password_change?: boolean
  name?: string
  avatar?: string
}

interface AuthContextType {
  isAuthenticated: boolean
  token: string | null
  user: User | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
}

export const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const checkAuthState = () => {
      // Check for token and user data in cookies
      const storedToken = Cookies.get('token')
      const storedUser = Cookies.get('user')
      
      console.log('Checking auth state...')
      console.log('Current path:', window.location.pathname)
      console.log('Stored token:', storedToken ? 'exists' : 'missing')
      console.log('Stored user:', storedUser ? 'exists' : 'missing')
      
      // Clear auth state if missing credentials
      if (!storedToken || !storedUser) {
        console.log('Missing auth credentials')
        setIsAuthenticated(false)
        setToken(null)
        setUser(null)
        return false
      }

      try {
        const userData = JSON.parse(storedUser)
        if (!userData || !userData.email) {
          throw new Error('Invalid user data')
        }
        
        setToken(storedToken)
        setUser(userData)
        setIsAuthenticated(true)
        console.log('Auth state restored successfully')
        return true
      } catch (error) {
        console.error('Error restoring auth state:', error)
        // Invalid stored data, clear it
        Cookies.remove('token')
        Cookies.remove('user')
        setIsAuthenticated(false)
        setToken(null)
        setUser(null)
        return false
      }
    }

    const isAuth = checkAuthState()
    
    // Handle redirects based on auth state
    const currentPath = window.location.pathname
    if (!isAuth && currentPath !== '/login') {
      router.push('/login')
    } else if (isAuth && currentPath === '/login') {
      router.push('/')
    }
    
    setIsLoading(false)
  }, [router])

  const login = async (username: string, password: string) => {
    try {
      const response = await apiLogin(username, password)
      console.log('Login response:', response)

      if (!response.token || !response.user) {
        throw new Error('Invalid response from server')
      }

      // Store in cookies with secure flags
      Cookies.set('token', response.token, {
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        expires: 7 // 7 days
      })
      Cookies.set('user', JSON.stringify(response.user), {
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        expires: 7 // 7 days
      })

      setToken(response.token)
      setUser(response.user)
      setIsAuthenticated(true)

      // Redirect based on user role
      if (response.user.is_staff) {
        router.push('/admin')
      } else {
        router.push('/')
      }
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const logout = () => {
    console.log('Logging out')
    Cookies.remove('token')
    Cookies.remove('user')
    setToken(null)
    setUser(null)
    setIsAuthenticated(false)
    router.push('/login')
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, token, user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
