'use client'

import { toast } from '@/hooks/use-toast'
import React, { createContext, useContext, useState, useEffect } from 'react'


export interface Notification {
  id: string
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  createdAt: string
  read: boolean
}

interface NotificationContextType {
  notifications: Notification[]
  addNotification: (notification: Omit<Notification, 'id' | 'createdAt' | 'read'>) => void
  markAsRead: (id: string) => void
  clearNotifications: () => void
  unreadCount: number
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    // Update unread count whenever notifications change
    setUnreadCount(notifications.filter(n => !n.read).length)
  }, [notifications])

  // WebSocket connection for real-time notifications
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/notifications/')

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'notification') {
        addNotification({
          title: data.title,
          message: data.message,
          type: data.notification_type || 'info'
        })
      }
    }

    return () => {
      ws.close()
    }
  }, [])

  const addNotification = (notification: Omit<Notification, 'id' | 'createdAt' | 'read'>) => {
    const newNotification = {
      ...notification,
      id: Math.random().toString(36).substr(2, 9),
      createdAt: new Date().toISOString(),
      read: false
    }

    setNotifications(prev => [newNotification, ...prev])

    // Show toast for new notifications
    toast({
      title: notification.title,
      description: notification.message,
      variant: notification.type === 'error' ? 'destructive' : 'default'
    })
  }

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === id ? { ...notification, read: true } : notification
      )
    )
  }

  const clearNotifications = () => {
    setNotifications([])
  }

  return (
    <NotificationContext.Provider value={{
      notifications,
      addNotification,
      markAsRead,
      clearNotifications,
      unreadCount
    }}>
      {children}
    </NotificationContext.Provider>
  )
}

export function useNotifications() {
  const context = useContext(NotificationContext)
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider')
  }
  return context
}
