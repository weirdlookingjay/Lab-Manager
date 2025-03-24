'use client'

import { useState, useEffect } from 'react'
import { fetchWithAuth } from '../utils/api'
import { getGravatarUrl } from '../utils/gravatar'
import Image from 'next/image'

interface UserProfile {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  profile_picture?: string
}

export default function ProfilePage() {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      const response = await fetchWithAuth('/profile/')
      setUser(response)
      setError(null)
    } catch (err) {
      setError('Failed to fetch profile')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-md">
        <p>{error}</p>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="p-4">
        <p>No profile data available</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="max-w-2xl mx-auto">
        <div className="space-y-1 mb-8">
          <h2 className="text-2xl font-semibold tracking-tight">Profile</h2>
          <p className="text-sm text-muted-foreground">
            View and manage your profile information
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center space-x-6">
            <div className="relative h-24 w-24">
              <Image
                src={user.profile_picture || getGravatarUrl(user.email)}
                alt={`${user.first_name} ${user.last_name}`}
                className="rounded-full"
                fill
                style={{ objectFit: 'cover' }}
              />
            </div>
            <div>
              <h3 className="text-xl font-semibold">
                {user.first_name} {user.last_name}
              </h3>
              <p className="text-sm text-gray-500">{user.username}</p>
              <p className="text-sm text-gray-500">{user.email}</p>
            </div>
          </div>

          <div className="mt-8 grid grid-cols-1 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-500">Username</h4>
              <p className="mt-1 text-sm">{user.username}</p>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-500">Email</h4>
              <p className="mt-1 text-sm">{user.email}</p>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-500">Full Name</h4>
              <p className="mt-1 text-sm">
                {user.first_name} {user.last_name}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
