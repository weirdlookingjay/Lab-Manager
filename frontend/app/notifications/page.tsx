"use client"

import React from 'react'
import { Card, Title, Text } from "@tremor/react"
import { BellIcon, CheckCircleIcon, ExclamationCircleIcon, ArchiveBoxIcon } from "@heroicons/react/24/outline"
import { useNotifications } from '@/app/contexts/NotificationContext'
import { formatDistanceToNow, differenceInMinutes, differenceInHours, differenceInDays, format } from 'date-fns'
import { cn } from "@/lib/utils"
import Link from 'next/link'

export default function NotificationsPage() {
  const { notifications, markAsRead, archiveNotification } = useNotifications()
  const activeNotifications = notifications.filter(n => !n.archived)

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon className="h-6 w-6 text-green-500" />
      case 'error':
        return <ExclamationCircleIcon className="h-6 w-6 text-red-500" />
      case 'warning':
        return <ExclamationCircleIcon className="h-6 w-6 text-yellow-500" />
      default:
        return <BellIcon className="h-6 w-6 text-blue-500" />
    }
  }

  const formatDate = (dateString: string | null | undefined): string => {
    if (!dateString) {
      console.error('No date provided to formatDate');
      return 'No date available';
    }

    try {
      const cleanDateString = dateString.split('.')[0];
      const date = new Date(cleanDateString.replace(' ', 'T'));
      
      if (isNaN(date.getTime())) {
        console.error('Invalid date string:', dateString);
        return 'Invalid date';
      }

      const now = new Date();
      const diffInMinutes = differenceInMinutes(now, date);
      const diffInHours = differenceInHours(now, date);
      const diffInDays = differenceInDays(now, date);

      if (diffInMinutes < 1) {
        return 'Just now';
      } else if (diffInMinutes < 60) {
        return `${diffInMinutes} minute${diffInMinutes === 1 ? '' : 's'} ago`;
      } else if (diffInHours < 24) {
        return `${diffInHours} hour${diffInHours === 1 ? '' : 's'} ago`;
      } else if (diffInDays < 7) {
        return `${diffInDays} day${diffInDays === 1 ? '' : 's'} ago`;
      } else {
        return format(date, 'MMM d, yyyy h:mm a');
      }
    } catch (error) {
      console.error('Error formatting date:', error, 'for date string:', dateString);
      return 'Error formatting date';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Notifications</h1>
        <Link 
          href="/archived-notifications" 
          className="text-gray-600 hover:text-gray-800 flex items-center gap-1"
        >
          <ArchiveBoxIcon className="h-4 w-4" />
          View Archived
        </Link>
      </div>

      {activeNotifications.length === 0 ? (
        <div className="text-center py-8">
          <BellIcon className="h-12 w-12 mx-auto text-gray-400" />
          <p className="mt-2 text-gray-500">No notifications</p>
        </div>
      ) : (
        <div className="space-y-4">
          {activeNotifications.map((notification) => (
            <Card key={notification.id} className={cn("p-4", !notification.read && "bg-blue-50")}>
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  {getNotificationIcon(notification.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <Title className="text-base break-words">{notification.title}</Title>
                  <Text className="mt-1 break-words">{notification.message}</Text>
                  <div className="flex items-center justify-between mt-2">
                    <Text className="text-sm text-gray-500">
                      {formatDate(notification.timestamp)}
                    </Text>
                    <div className="flex gap-2">
                      {!notification.read && (
                        <button
                          onClick={() => markAsRead(notification.id)}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          Mark as read
                        </button>
                      )}
                      <button
                        onClick={() => archiveNotification(notification.id)}
                        className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-800"
                      >
                        <ArchiveBoxIcon className="h-4 w-4" />
                        Archive
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
