'use client'

import { Fragment, useState, useCallback } from 'react'
import { Menu, Transition, Dialog, Combobox } from '@headlessui/react'
import { MagnifyingGlassIcon } from '@heroicons/react/20/solid'
import { 
  BellIcon, 
  Cog6ToothIcon,
  ComputerDesktopIcon
} from '@heroicons/react/24/outline'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { usePathname } from 'next/navigation'
import debounce from 'lodash/debounce'
import md5 from 'crypto-js/md5'
import { useAuth } from '@/app/contexts/AuthContext'
import { useNotifications } from '@/app/contexts/NotificationContext'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/components/ui/tooltip"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Bell } from 'lucide-react'
import { ThemeToggle } from "@/components/ThemeToggle";
import { LogOut } from "lucide-react";
import { cn } from '@/lib/utils'

interface HeaderProps {
  children?: React.ReactNode;
}

interface SearchResult {
  id: string
  type: 'computer' | 'document' | 'scan'
  title: string
  url: string
}

export default function Header({ children }: HeaderProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const router = useRouter()
  const pathname = usePathname()
  const auth = useAuth()
  const { unreadCount } = useNotifications()

  const gravatarUrl = auth.user?.email 
    ? `https://gravatar.com/avatar/${md5(auth.user.email.trim().toLowerCase()).toString()}?s=32&d=mp` 
    : 'https://gravatar.com/avatar/00000000000000000000000000000000?s=32&d=mp'

  const performSearch = useCallback(
    debounce(async (searchQuery: string) => {
      if (!searchQuery.trim()) {
        setResults([])
        return
      }

      setIsSearching(true)
      try {
        const response = await fetch('/search/', {
          method: 'POST',
          body: JSON.stringify({ query: searchQuery }),
        })
        const data = await response.json()
        setResults(data.results || [])
      } catch (error) {
        console.error('Search failed:', error)
      } finally {
        setIsSearching(false)
      }
    }, 300),
    []
  )

  const handleSearch = (value: string) => {
    setQuery(value)
    performSearch(value)
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="mr-4 flex">
          <Link href="/" className="mr-6 flex items-center space-x-2">
            <span className="hidden font-bold sm:inline-block">
              Lab Manager
            </span>
          </Link>
        </div>

        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <nav className="flex items-center space-x-2">
            {children}
            
            <TooltipProvider>
              {auth.isAuthenticated && (
                <>
                  <Link href="/notifications">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" className="relative h-8 w-8">
                          <BellIcon 
                            className={cn(
                              "h-5 w-5",
                              unreadCount > 0 ? "text-red-500" : "text-gray-500"
                            )}
                          />
                          {unreadCount > 0 && (
                            <Badge
                              variant="secondary"
                              className={cn(
                                "absolute -right-1 -top-1 h-4 w-4 rounded-full p-0 text-[10px] font-medium",
                                unreadCount > 0 ? "animate-bounce" : ""
                              )}
                            >
                              {unreadCount}
                            </Badge>
                          )}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Notifications</p>
                      </TooltipContent>
                    </Tooltip>
                  </Link>
                  <Link 
                    href="/notifications" 
                    className="w-16 flex items-center justify-center text-gray-600 hover:text-gray-900 border-l border-r border-gray-200"
                  >
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="relative"
                        >
                          <BellIcon 
                            className={cn(
                              "h-5 w-5",
                              unreadCount > 0 ? "text-red-500" : "text-gray-500"
                            )}
                          />
                          {unreadCount > 0 && (
                            <div 
                              className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center animate-pulse"
                            >
                              {unreadCount}
                            </div>
                          )}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        Notifications
                      </TooltipContent>
                    </Tooltip>
                  </Link>
                  <Menu as="div">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Menu.Button 
                          className="w-16 h-full flex items-center justify-center text-gray-600 hover:text-gray-900"
                        >
                          <img
                            src={gravatarUrl}
                            alt={auth.user?.username || 'Profile'}
                            className="h-5 w-5 rounded-full"
                          />
                        </Menu.Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        {auth.user?.username || 'Profile'}
                      </TooltipContent>
                    </Tooltip>
                    <Transition
                      as={Fragment}
                      enter="transition ease-out duration-100"
                      enterFrom="transform opacity-0 scale-95"
                      enterTo="transform opacity-100 scale-100"
                      leave="transition ease-in duration-75"
                      leaveFrom="transform opacity-100 scale-100"
                      leaveTo="transform opacity-0 scale-95"
                    >
                      <Menu.Items className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                        <Menu.Item>
                          {({ active }) => (
                            <Link
                              href="/profile"
                              className={classNames(
                                active ? 'bg-gray-100' : '',
                                'block px-4 py-2 text-sm text-gray-700'
                              )}
                            >
                              Your Profile
                            </Link>
                          )}
                        </Menu.Item>
                        <Menu.Item>
                          {({ active }) => (
                            <Link
                              href="/settings"
                              className={classNames(
                                active ? 'bg-gray-100' : '',
                                'block px-4 py-2 text-sm text-gray-700'
                              )}
                            >
                              Settings
                            </Link>
                          )}
                        </Menu.Item>
                        {auth.user?.is_staff && (
                          <>
                            <Menu.Item>
                              {({ active }) => (
                                <Link
                                  href="/admin/dashboard"
                                  className={classNames(
                                    active ? 'bg-gray-100' : '',
                                    'block px-4 py-2 text-sm text-gray-700'
                                  )}
                                >
                                  Dashboard
                                </Link>
                              )}
                            </Menu.Item>
                            <Menu.Item>
                              {({ active }) => (
                                <Link
                                  href="/admin/email"
                                  className={classNames(
                                    active ? 'bg-gray-100' : '',
                                    'block px-4 py-2 text-sm text-gray-700'
                                  )}
                                >
                                  Send Emails
                                </Link>
                              )}
                            </Menu.Item>
                          </>
                        )}
                        <Menu.Item>
                          {({ active }) => (
                            <button
                              onClick={() => {
                                auth.logout()
                              }}
                              className={classNames(
                                active ? 'bg-gray-100' : '',
                                'block w-full text-left px-4 py-2 text-sm text-red-700'
                              )}
                            >
                              Logout
                            </button>
                          )}
                        </Menu.Item>
                      </Menu.Items>
                    </Transition>
                  </Menu>
                  <Button variant="ghost" size="icon" onClick={auth.logout}>
                    <LogOut className="h-4 w-4" />
                  </Button>
                </>
              )}
            </TooltipProvider>
            <div className="flex items-center gap-2">
              <ThemeToggle />
            </div>
          </nav>
        </div>
      </div>
      <div className="border-b border-gray-200">
        <div className="max-w-7xl mx-auto">
          <div className="flex h-16">
            <div className="flex-1 px-4 sm:px-6 flex items-center">
              <Combobox
                as="div"
                value={null}
                onChange={(result: SearchResult | null) => {
                  if (result) {
                    router.push(result.url)
                    setQuery('')
                    setResults([])
                  }
                }}
                className="max-w-xl"
              >
                <div className="relative">
                  <MagnifyingGlassIcon
                    className="pointer-events-none absolute left-4 top-3.5 h-5 w-5 text-gray-400"
                    aria-hidden="true"
                  />
                  <Combobox.Input
                    className="h-12 w-full border-0 bg-transparent pl-11 pr-4 text-gray-900 placeholder:text-gray-400 focus:ring-0 sm:text-sm"
                    placeholder="Search..."
                    onChange={(event) => handleSearch(event.target.value)}
                    value={query}
                  />
                </div>

                {results.length > 0 && (
                  <Combobox.Options className="absolute z-10 mt-2 max-h-96 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                    {results.map((result) => (
                      <Combobox.Option
                        key={result.id}
                        value={result}
                        className={({ active }) =>
                          classNames(
                            'relative cursor-default select-none py-2 pl-3 pr-9',
                            active ? 'bg-indigo-600 text-white' : 'text-gray-900'
                          )
                        }
                      >
                        {({ active }) => (
                          <>
                            <div className="flex items-center">
                              {result.type === 'computer' && (
                                <ComputerDesktopIcon
                                  className={classNames(
                                    'h-5 w-5 flex-shrink-0',
                                    active ? 'text-white' : 'text-gray-400'
                                  )}
                                />
                              )}
                              <span className="ml-3 truncate">{result.title}</span>
                            </div>
                          </>
                        )}
                      </Combobox.Option>
                    ))}
                  </Combobox.Options>
                )}

                {isSearching && (
                  <div className="absolute z-10 mt-2 w-full rounded-md bg-white shadow-lg">
                    <div className="py-4 text-center text-sm text-gray-500">
                      Searching...
                    </div>
                  </div>
                )}
              </Combobox>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}
