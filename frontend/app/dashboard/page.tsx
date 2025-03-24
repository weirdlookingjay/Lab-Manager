'use client'

import { useState, useEffect } from 'react'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/20/solid'
import { ClockIcon } from '@heroicons/react/20/solid'
import { 
  Card,
  Title,
  Flex,
  Text
} from '@tremor/react'
import { Skeleton } from "@/components/ui/skeleton"
import { fetchWithAuth } from '../utils/api'
import NotificationCenter from '../components/NotificationCenter/NotificationCenter'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import { useAuth } from '../contexts/AuthContext'

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function LoadingSkeleton() {
  return (
    <div className="mt-6">
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
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

export default function Dashboard() {
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const [stats, setStats] = useState({
    onlineComputers: 0,
    totalComputers: 0,
    totalTransfers: 0,
    failedTransfers: 0,
    totalData: 0,
  })

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await fetchWithAuth('/api/computers/')
        const scanData = await fetchWithAuth('/api/scans/status/')
        
        if (Array.isArray(data)) {
          const onlineCount = data.filter(c => c.is_online).length
          setStats(prevStats => ({
            ...prevStats,
            onlineComputers: onlineCount,
            totalComputers: data.length,
          }))
        }

        if (scanData && typeof scanData === 'object') {
          setStats(prevStats => ({
            ...prevStats,
            totalTransfers: scanData.total_transfers || 0,
            failedTransfers: scanData.failed_transfers || 0,
            totalData: scanData.total_bytes || 0,
          }))
        }
      } catch (err) {
        console.error('Failed to fetch data:', err)
        setError('Failed to fetch data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  // Show loading skeleton while auth is loading or data is loading
  if (authLoading || loading) {
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

  return (
    <main className="p-4 md:p-10 mx-auto max-w-7xl">
      <div className="flex justify-between items-center">
        <div>
          <Title>Dashboard</Title>
          <Text>Welcome to your dashboard</Text>
        </div>
        <NotificationCenter />
      </div>
      <ToastContainer />
      <div className="mt-6">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {/* Computer Status Card */}
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <Text>Computers</Text>
                <Title>{stats.onlineComputers} / {stats.totalComputers}</Title>
              </div>
              <div className={classNames(
                stats.onlineComputers === stats.totalComputers ? 'bg-green-100' : 'bg-yellow-100',
                'rounded-full p-3'
              )}>
                <ArrowUpIcon className={classNames(
                  stats.onlineComputers === stats.totalComputers ? 'text-green-600' : 'text-yellow-600',
                  'h-6 w-6'
                )} />
              </div>
            </div>
            <Text className="mt-4">Online computers</Text>
          </Card>

          {/* Transfer Status Card */}
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <Text>Transfers</Text>
                <Title>{stats.totalTransfers}</Title>
              </div>
              <div className={classNames(
                stats.failedTransfers === 0 ? 'bg-green-100' : 'bg-red-100',
                'rounded-full p-3'
              )}>
                {stats.failedTransfers === 0 ? (
                  <ArrowUpIcon className="h-6 w-6 text-green-600" />
                ) : (
                  <ArrowDownIcon className="h-6 w-6 text-red-600" />
                )}
              </div>
            </div>
            <Text className="mt-4">{stats.failedTransfers} failed transfers</Text>
          </Card>

          {/* Data Transfer Card */}
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <Text>Data Transferred</Text>
                <Title>{formatBytes(stats.totalData)}</Title>
              </div>
              <div className="bg-blue-100 rounded-full p-3">
                <ClockIcon className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <Text className="mt-4">Total data processed</Text>
          </Card>
        </div>
      </div>
    </main>
  )
}
