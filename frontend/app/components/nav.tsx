"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ScanLine, FileText, Home, ScrollText, Ticket } from "lucide-react"

export function MainNav() {
  const pathname = usePathname()

  const routes = [
    {
      href: "/",
      label: "Home",
      icon: Home,
      active: pathname === "/",
    },
    {
      href: "/scans",
      label: "Scans",
      icon: ScanLine,
      active: pathname === "/scans",
    },
    {
      href: "/tickets",
      label: "Tickets",
      icon: Ticket,
      active: pathname === "/tickets",
    },
    {
      href: "/documents",
      label: "Documents",
      icon: FileText,
      active: pathname === "/documents",
    },
    {
      href: "/logs",
      label: "Logs",
      icon: ScrollText,
      active: pathname === "/logs",
    },
  ]

  return (
    <nav className="flex items-center space-x-4 lg:space-x-6 mx-6">
      {routes.map((route) => {
        const Icon = route.icon
        return (
          <Button
            key={route.href}
            variant={route.active ? "default" : "ghost"}
            asChild
          >
            <Link
              href={route.href}
              className="flex items-center gap-2"
            >
              <Icon className="h-4 w-4" />
              {route.label}
            </Link>
          </Button>
        )
      })}
    </nav>
  )
}
