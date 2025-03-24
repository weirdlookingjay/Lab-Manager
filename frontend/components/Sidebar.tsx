'use client'

import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

interface SidebarProps {
  children?: React.ReactNode
  className?: string
}

export default function Sidebar({ children, className }: SidebarProps) {
  return (
    <div className="hidden w-64 bg-white lg:block border-r">
      <div className="flex h-full flex-col">
        <div className="flex h-16 shrink-0 items-center px-6">
          <h2 className="text-lg font-semibold">Lab Manager</h2>
        </div>
        <div className="flex-1 px-6 py-4">
          {children}
        </div>
      </div>
    </div>
  )
}
