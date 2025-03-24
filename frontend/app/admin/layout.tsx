'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/app/contexts/AuthContext'

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push('/login')
        return
      }

      if (!user?.is_staff) {
        router.push('/')
        return
      }
    }
  }, [isAuthenticated, user, isLoading, router])

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (!isAuthenticated || !user?.is_staff) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {children}
    </div>
  )
}
