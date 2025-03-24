'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from './contexts/AuthContext'
import { Card } from '@tremor/react'
import { Skeleton } from "@/components/ui/skeleton"

function LoadingSkeleton() {
  return (
    <div className="mt-6">
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="bg-white">
            <div className="flex items-center justify-between">
              <div className="space-y-3">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-8 w-28" />
              </div>
              <Skeleton className="h-12 w-12 rounded-full" />
            </div>
            <Skeleton className="mt-4 h-4 w-32" />
          </Card>
        ))}
      </div>
    </div>
  )
}

export default function Home() {
  const router = useRouter()
  const { isAuthenticated, user, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated) {
        // Redirect admin users to admin dashboard
        if (user?.is_staff) {
          router.replace('/admin')
        } else {
          // Redirect regular users to dashboard
          router.replace('/dashboard')
        }
      } else {
        // Redirect unauthenticated users to login
        router.replace('/login')
      }
    }
  }, [isAuthenticated, isLoading, user, router])

  // Show loading skeleton while checking auth
  return (
    <main className="p-4 md:p-10 mx-auto max-w-7xl">
      <div className="flex justify-between items-center">
        <div>
          <Skeleton className="h-8 w-32 mb-2" />
          <Skeleton className="h-4 w-48" />
        </div>
        <Skeleton className="h-10 w-10" />
      </div>
      <LoadingSkeleton />
    </main>
  )
}
