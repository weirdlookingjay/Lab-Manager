'use client'

import { useState, useEffect } from 'react'
import { Computer } from '@/types/computer'
import { formatDistanceToNow } from 'date-fns'
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/20/solid'
import { fetchWithAuth } from '../utils/api'
import { useSearchParams } from 'next/navigation'
import { useRouter } from 'next/navigation'

export default function DevicesPage() {
  const [devices, setDevices] = useState<Computer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const searchParams = useSearchParams()
  const selectedId = searchParams.get('selected')
  const router = useRouter()

  useEffect(() => {
    fetchDevices()
    const interval = setInterval(fetchDevices, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchDevices = async () => {
    try {
      const response = await fetchWithAuth('/api/computers/')
      if (Array.isArray(response)) {
        setDevices(response)
      }
      setLoading(false)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch devices')
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-8 w-1/4 bg-gray-200 rounded mb-8"></div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-white shadow rounded-lg p-6">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="space-y-3 mt-4">
                    <div className="h-4 bg-gray-200 rounded"></div>
                    <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto">
            <h1 className="text-xl font-semibold text-gray-900">Devices</h1>
            <p className="mt-2 text-sm text-gray-700">
              A list of all computers in your network
            </p>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">{error}</h3>
              </div>
            </div>
          </div>
        )}

        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {devices.map((device) => (
            <div
              key={device.id}
              className={`relative bg-white shadow rounded-lg p-6 cursor-pointer hover:shadow-md transition-shadow duration-200 ${
                selectedId === device.id.toString() ? 'ring-2 ring-indigo-500' : ''
              }`}
              onClick={() => router.push(`/devices?selected=${device.id}`)}
            >
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium text-gray-900">{device.label}</h2>
                {device.is_online ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircleIcon className="h-5 w-5 text-red-500" />
                )}
              </div>
              <div className="mt-4 space-y-2">
                <p className="text-sm text-gray-500">IP: {device.ip_address}</p>
                <p className="text-sm text-gray-500">
                  Status: {device.is_online ? 'Online' : 'Offline'}
                </p>
                {device.last_seen && (
                  <p className="text-sm text-gray-500">
                    Last seen: {formatDistanceToNow(new Date(device.last_seen))} ago
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
