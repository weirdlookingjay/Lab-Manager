'use client'

import { useAuth } from '@/app/contexts/AuthContext'
import { useState } from 'react'
import md5 from 'crypto-js/md5'
import { usePathname } from 'next/navigation'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import { Bell, Settings, LogIn } from 'lucide-react'
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import Link from 'next/link'
import NotificationCenter from './NotificationCenter/NotificationCenter'
import { useNotifications } from '@/app/contexts/NotificationContext'
import { cn } from '@/lib/utils'

export default function Header() {
  const { user, logout, isAuthenticated, isLoading } = useAuth()
  const { unreadCount } = useNotifications()
  const pathname = usePathname()

  const getGravatarUrl = (email: string) => {
    const hash = md5(email.toLowerCase().trim())
    return `https://www.gravatar.com/avatar/${hash}?s=40&d=identicon`
  }

  return (
    <header className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        <Link href="/" className="flex items-center space-x-2">
          <h1 className="text-2xl font-semibold text-gray-900">Lab Scanner</h1>
        </Link>

        <div className="flex items-center space-x-6">
          {!isLoading && pathname !== '/scans' && (
            <div className="relative w-64">
              <input
                type="text"
                placeholder="Search..."
                className="w-full px-4 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}
          {!isLoading && (
            <>
              <DropdownMenu>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <DropdownMenuTrigger asChild>
                      <div className="relative inline-block">
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className={cn(
                            "relative",
                            unreadCount > 0 && "hover:bg-red-100"
                          )}
                        >
                          <Bell 
                            style={{
                              color: unreadCount > 0 ? '#EF4444' : '#6B7280'
                            }}
                            className="h-5 w-5" 
                          />
                        </Button>
                        {unreadCount > 0 && (
                          <div 
                            className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center"
                            style={{
                              animation: 'pulse 2s infinite'
                            }}
                          >
                            {unreadCount}
                          </div>
                        )}
                      </div>
                    </DropdownMenuTrigger>
                  </TooltipTrigger>
                  <TooltipContent>
                    {unreadCount > 0 
                      ? `You have ${unreadCount} unread notification${unreadCount === 1 ? '' : 's'}`
                      : 'No new notifications'
                    }
                  </TooltipContent>
                </Tooltip>
                <DropdownMenuContent align="end" className="w-[400px]">
                  <NotificationCenter />
                </DropdownMenuContent>
              </DropdownMenu>

              {isAuthenticated ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <img
                        src={user?.email ? getGravatarUrl(user.email) : '/default-avatar.png'}
                        alt="User avatar"
                        className="h-8 w-8 rounded-full"
                      />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    {user && user.is_staff && (
                      <>
                        <DropdownMenuItem asChild>
                          <Link href="/admin/dashboard">
                            Dashboard
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild>
                          <Link href="/admin/email">
                            Send Emails
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                      </>
                    )}
                    <DropdownMenuItem>
                      <Settings className="mr-2 h-4 w-4" />
                      Settings
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={logout}>
                      <LogIn className="mr-2 h-4 w-4" />
                      Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <Link href="/login">
                  <Button>Login</Button>
                </Link>
              )}
            </>
          )}
        </div>
      </div>
    </header>
  )
}
