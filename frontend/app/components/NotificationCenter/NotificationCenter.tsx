'use client'

import { useNotifications } from '@/app/contexts/NotificationContext'
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { formatDistanceToNow } from 'date-fns'
import { Bell, Check, Info, AlertTriangle, AlertCircle } from 'lucide-react'
import { cn } from "@/lib/utils"

const NotificationCenter = () => {
  const { notifications, markAsRead, clearNotifications } = useNotifications()

  const getIcon = (type: string) => {
    switch (type) {
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />
      case 'success':
        return <Check className="h-4 w-4 text-green-500" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Bell className="h-4 w-4 text-gray-500" />
    }
  }

  const getTypeStyles = (type: string) => {
    switch (type) {
      case 'error':
        return 'border-l-4 border-red-500 bg-red-50'
      case 'success':
        return 'border-l-4 border-green-500 bg-green-50'
      case 'warning':
        return 'border-l-4 border-yellow-500 bg-yellow-50'
      default:
        return 'border-l-4 border-blue-500 bg-blue-50'
    }
  }

  const formatDate = (dateString: string) => {
    try {
      // First check if the date string is empty or invalid
      if (!dateString) {
        return 'Just now'
      }

      const date = new Date(dateString)
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        console.error('Invalid date:', dateString)
        return 'Just now'
      }

      // Check if the date is within the last minute
      const now = new Date()
      const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
      
      // Log the time difference for debugging
      console.log('Time difference:', {
        now: now.toISOString(),
        date: date.toISOString(),
        diffInSeconds
      })

      if (diffInSeconds < 60) {
        return 'Just now'
      }

      // Format the date using date-fns
      return formatDistanceToNow(date, { 
        addSuffix: true,
        includeSeconds: true
      })
    } catch (error) {
      console.error('Error formatting date:', error, 'for date string:', dateString)
      return 'Just now'
    }
  }

  if (notifications.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        No notifications
      </div>
    )
  }

  return (
    <div className="w-full">
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-lg font-semibold">Notifications</h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={clearNotifications}
        >
          Clear all
        </Button>
      </div>
      <ScrollArea className="h-[400px]">
        <div className="divide-y">
          {notifications.map((notification) => (
            <div
              key={notification.id}
              className={cn(
                'p-4 hover:bg-gray-50/50 cursor-pointer transition-colors',
                getTypeStyles(notification.type),
                notification.read ? 'opacity-75' : ''
              )}
              onClick={() => markAsRead(notification.id)}
            >
              <div className="flex items-start gap-3">
                <div className="mt-1 flex-shrink-0">
                  {getIcon(notification.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-900 break-words">
                    {notification.title}
                  </h3>
                  <p className="mt-1 text-sm text-gray-500 break-words">
                    {notification.message}
                  </p>
                  <p className="mt-1 text-xs text-gray-400">
                    {formatDate(notification.createdAt)}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}

export default NotificationCenter
