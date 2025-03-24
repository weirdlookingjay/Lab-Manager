'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { useToast } from '@/hooks/use-toast'
import { Loader2, RefreshCcw } from 'lucide-react'
import { fetchWithAuth } from '../utils/api'

interface Computer {
  id: number
  label: string
  ip_address: string
  is_online: boolean
  last_seen: string
}

export default function SettingsPage() {
  const [computers, setComputers] = useState<Computer[]>([])
  const [selectedComputers, setSelectedComputers] = useState<number[]>([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<{[key: number]: boolean}>({})
  const [refreshing, setRefreshing] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    fetchComputers()
  }, [])

  const fetchComputers = async () => {
    try {
      setRefreshing(true)
      const data = await fetchWithAuth('/api/computers/')
      if (Array.isArray(data)) {
        setComputers(data)
      }
    } catch (error) {
      console.error('Error fetching computers:', error)
      toast({
        title: "Error",
        description: "Failed to fetch computers",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleSelectAll = () => {
    if (selectedComputers.length === computers.length) {
      setSelectedComputers([])
    } else {
      setSelectedComputers(computers.map(c => c.id))
    }
  }

  const handleSelectComputer = (computerId: number) => {
    setSelectedComputers(prev => {
      if (prev.includes(computerId)) {
        return prev.filter(id => id !== computerId)
      } else {
        return [...prev, computerId]
      }
    })
  }

  const updateComputerStatus = async () => {
    if (selectedComputers.length === 0) {
      toast({
        title: "No Computers Selected",
        description: "Please select at least one computer to update.",
        variant: "destructive",
      })
      return
    }

    const newUpdating = { ...updating }
    let successCount = 0
    let failCount = 0

    try {
      const selectedComputerData = computers.filter(c => selectedComputers.includes(c.id))
      
      for (const computer of selectedComputerData) {
        newUpdating[computer.id] = true
        setUpdating(newUpdating)

        try {
          const response = await fetchWithAuth('/api/scans/computer_status/', {
            method: 'POST',
            body: JSON.stringify({
              computer: computer.label,
              ip: computer.ip_address
            }),
          })

          // Update computer status immediately in the UI
          setComputers(prev => prev.map(c => {
            if (c.id === computer.id) {
              return {
                ...c,
                is_online: response.is_online,
                last_seen: response.is_online ? new Date().toISOString() : c.last_seen
              }
            }
            return c
          }))

          successCount++
        } catch (error) {
          console.error(`Error updating computer ${computer.label}:`, error)
          failCount++
        }

        newUpdating[computer.id] = false
        setUpdating(newUpdating)
      }

      // Show final status
      if (successCount > 0) {
        toast({
          title: "Status Updated",
          description: `Successfully updated ${successCount} computer${successCount > 1 ? 's' : ''}${
            failCount > 0 ? `, ${failCount} failed` : ''
          }`,
          variant: failCount > 0 ? "default" : "default",
        })
      } else {
        toast({
          title: "Error",
          description: "Failed to update any computers",
          variant: "destructive",
        })
      }

    } catch (error) {
      console.error('Error in update process:', error)
      toast({
        title: "Error",
        description: "Failed to complete the update process",
        variant: "destructive",
      })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Computer Status Management</CardTitle>
              <CardDescription>Manage and update computer online/offline status</CardDescription>
            </div>
            <Button 
              variant="outline" 
              size="icon"
              onClick={fetchComputers}
              disabled={refreshing}
            >
              <RefreshCcw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={selectedComputers.length === computers.length}
                  onCheckedChange={handleSelectAll}
                />
                <label>Select All ({selectedComputers.length} selected)</label>
              </div>
              <Button 
                onClick={updateComputerStatus}
                disabled={Object.values(updating).some(Boolean) || selectedComputers.length === 0}
              >
                {Object.values(updating).some(Boolean) ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Updating...
                  </>
                ) : (
                  'Update Status'
                )}
              </Button>
            </div>

            <div className="grid gap-4">
              {computers.map((computer) => (
                <div
                  key={computer.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center space-x-4">
                    <Checkbox
                      checked={selectedComputers.includes(computer.id)}
                      onCheckedChange={() => handleSelectComputer(computer.id)}
                      disabled={updating[computer.id]}
                    />
                    <div>
                      <div className="font-medium">{computer.label}</div>
                      <div className="text-sm text-gray-500">{computer.ip_address}</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    {updating[computer.id] ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <div className={`px-2 py-1 rounded-full text-xs ${
                        computer.is_online 
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {computer.is_online ? 'Online' : 'Offline'}
                      </div>
                    )}
                    <div className="text-sm text-gray-500">
                      Last seen: {computer.last_seen ? new Date(computer.last_seen).toLocaleString() : 'Never'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
