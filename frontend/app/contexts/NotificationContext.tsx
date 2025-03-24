'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'
import { fetchWithAuth } from '../utils/api'
import { toast } from '@/hooks/use-toast'

export interface Notification {
  id: string
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  timestamp: string
  read: boolean
  archived: boolean
}

interface NotificationContextType {
  notifications: Notification[]
  unreadCount: number
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read' | 'archived'>) => void
  markAsRead: (id: string) => void
  archiveNotification: (id: string) => void
  unarchiveNotification: (id: string) => void
  clearNotifications: () => void
  updateUnreadCount: () => void
}

const NotificationContext = createContext<NotificationContextType | null>(null)

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [socket, setSocket] = useState<WebSocket | null>(null)

  const updateUnreadCount = () => {
    // Only count unread and unarchived notifications
    setUnreadCount(notifications.filter(n => !n.read && !n.archived).length);
  }

  // Update unread count whenever notifications change
  useEffect(() => {
    updateUnreadCount();
  }, [notifications]);

  // Fetch initial notifications
  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        // Check if we have both token and user in cookies before fetching
        const token = document.cookie.includes('token=')
        const user = document.cookie.includes('user=')
        if (!token || !user) {
          console.log('Not authenticated, skipping notification fetch')
          return
        }

        // Check if we're on the login page
        if (window.location.pathname === '/login') {
          console.log('On login page, skipping notification fetch')
          return
        }
        
        const data = await fetchWithAuth('/api/notifications/')
        console.log('Raw API response:', data);
        
        if (Array.isArray(data)) {
          const formattedNotifications = data.map(n => ({
            id: n.id,
            title: n.title,
            message: n.message,
            type: n.type,
            timestamp: n.timestamp,
            read: n.read,
            archived: n.archived
          }));
          
          console.log('Formatted notifications:', formattedNotifications);
          setNotifications(formattedNotifications);
        }
      } catch (error: any) {
        // Only log error if it's not an auth error
        if (!error.type || error.type !== 'AuthError') {
          console.error('Failed to fetch notifications:', error)
        }
      }
    }

    fetchNotifications()

    // Only set up WebSocket if authenticated
    const token = document.cookie.includes('token=')
    const user = document.cookie.includes('user=')
    if (token && user && window.location.pathname !== '/login') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = process.env.NEXT_PUBLIC_WS_URL || window.location.host
      const ws = new WebSocket(`${protocol}//${host}/ws/notifications/`)
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        setSocket(ws)
      }

      const handleWebSocketMessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data)
          console.log('WebSocket message received:', data)
          
          if (data.type === 'notification.message') {
            const newNotification = {
              id: data.message.id,
              title: data.message.title,
              message: data.message.message,
              type: data.message.type || 'info',
              timestamp: data.message.timestamp,
              read: false,
              archived: false
            }
            
            setNotifications(prev => [newNotification, ...prev])
            
            // Show toast for new notification
            toast({
              title: newNotification.title,
              description: newNotification.message,
              variant: newNotification.type === 'error' ? 'destructive' : 'default'
            })
          }
        } catch (error) {
          console.error('Error handling WebSocket message:', error)
        }
      }

      ws.addEventListener('message', handleWebSocketMessage)

      return () => {
        ws.removeEventListener('message', handleWebSocketMessage)
        ws.close()
      }
    }
  }, [])

  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp' | 'read' | 'archived'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date().toISOString(),
      read: false,
      archived: false
    }
    setNotifications(prev => [newNotification, ...prev])
  }

  const archiveNotification = async (id: string) => {
    try {
      await fetchWithAuth(`/api/notifications/${id}/archive/`, {
        method: 'POST'
      })
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, archived: true } : n)
      )
    } catch (error) {
      console.error('Failed to archive notification:', error)
    }
  }

  const unarchiveNotification = async (id: string) => {
    try {
      await fetchWithAuth(`/api/notifications/${id}/unarchive/`, {
        method: 'POST'
      })
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, archived: false } : n)
      )
    } catch (error) {
      console.error('Failed to unarchive notification:', error)
    }
  }

  const markAsRead = async (id: string) => {
    try {
      await fetchWithAuth(`/api/notifications/${id}/mark_read/`, {
        method: 'POST'
      })
      setNotifications(prev =>
        prev.map(n => n.id === id ? { ...n, read: true } : n)
      )
    } catch (error) {
      console.error('Failed to mark notification as read:', error)
    }
  }

  const clearNotifications = async () => {
    try {
      await fetchWithAuth('/api/notifications/clear/', {
        method: 'POST'
      })
      setNotifications([])
      setUnreadCount(0)
    } catch (error) {
      console.error('Failed to clear notifications:', error)
    }
  }

  return (
    <NotificationContext.Provider value={{
      notifications,
      unreadCount,
      addNotification,
      markAsRead,
      archiveNotification,
      unarchiveNotification,
      clearNotifications,
      updateUnreadCount
    }}>
      {children}
    </NotificationContext.Provider>
  )
}

export function useNotifications() {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider')
  }
  return context
}
