"use client"

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from "@/lib/utils"
import { Scan, FileText, ScrollText, Ticket, Bell } from 'lucide-react'
import Header from "@/components/Header"
import { AuthProvider, useAuth } from '@/app/contexts/AuthContext'
import { NotificationProvider } from '@/app/contexts/NotificationContext'
import { useState } from "react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";
import { Menu } from "lucide-react";

const sidebarLinks = [
  { href: '/scans', label: 'Scans', icon: Scan },
  { href: '/tickets', label: 'Tickets', icon: Ticket },
  { href: '/documents', label: 'Documents', icon: FileText },
  { href: '/notifications', label: 'Notifications', icon: Bell },
  { href: '/logs', label: 'Logs', icon: ScrollText },
];

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();
  const { isAuthenticated, isLoading } = useAuth();

  // Show a minimal layout when loading or not authenticated
  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-background">
        <main className="flex-1">
          {children}
        </main>
      </div>
    );
  }

  return (
    <AuthProvider>
      <NotificationProvider>
        <div className="relative h-screen flex overflow-hidden bg-background">
          {/* Sidebar */}
          <div
            className={cn(
              "fixed inset-y-0 left-0 transform bg-card w-64 transition-transform duration-300 ease-in-out z-30 md:relative md:translate-x-0",
              sidebarOpen ? "translate-x-0" : "-translate-x-full"
            )}
          >
            <div className="h-full flex flex-col border-r">
              <div className="flex items-center justify-between h-14 px-4 border-b">
                <h1 className="text-lg font-bold text-primary">Lab V2</h1>
              </div>
              <nav className="flex-1 px-2 py-4 space-y-1">
                {sidebarLinks.map(({ href, label, icon: Icon }) => (
                  <Link
                    key={href}
                    href={href}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                      pathname === href
                        ? "bg-primary text-primary-foreground"
                        : "text-foreground/60 hover:bg-primary/10 hover:text-foreground"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {label}
                  </Link>
                ))}
              </nav>
            </div>
          </div>

          {/* Main content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <Header>
              <div className="flex items-center gap-4">
                <Button
                  variant="ghost"
                  size="icon"
                  className="md:hidden"
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                >
                  <Menu className="h-4 w-4" />
                </Button>
                <ThemeToggle />
              </div>
            </Header>

            <main className="flex-1 overflow-x-hidden overflow-y-auto bg-background p-6">
              {children}
            </main>
          </div>

          {/* Overlay */}
          {sidebarOpen && (
            <div
              className="fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}
        </div>
      </NotificationProvider>
    </AuthProvider>
  );
}
