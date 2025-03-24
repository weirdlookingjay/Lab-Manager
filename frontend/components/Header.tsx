'use client';

import { useAuth } from '@/app/contexts/AuthContext';
import { useNotifications } from '@/app/contexts/NotificationContext';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Bell, LogOut, User } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { DarkModeToggle } from "@/components/DarkModeToggle";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface HeaderProps {
  children?: React.ReactNode;
}

export default function Header({ children }: HeaderProps) {
  const auth = useAuth();
  const { unreadCount } = useNotifications();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="mr-4 flex">
          <Link href="/" className="mr-6 flex items-center space-x-2">
            <span className="font-bold text-primary">Lab Manager</span>
          </Link>
        </div>

        <div className="flex flex-1 items-center justify-end space-x-2">
          <div className="flex items-center gap-4">
            {children}
            {/* <DarkModeToggle /> */}
            
            {auth.isAuthenticated && (
              <>
                <Link href="/notifications">
                  <Button variant="ghost" size="icon" className="relative">
                    <Bell className="h-4 w-4" />
                    {unreadCount > 0 && (
                      <Badge
                        variant="secondary"
                        className={cn(
                          "absolute -right-1 -top-1 h-4 w-4 rounded-full p-0 text-[10px] font-medium bg-primary text-primary-foreground"
                        )}
                      >
                        {unreadCount}
                      </Badge>
                    )}
                  </Button>
                </Link>
                
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                      <Avatar className="h-8 w-8">
                        <AvatarImage src={auth.user?.avatar || ''} alt={auth.user?.name || ''} />
                        <AvatarFallback className="bg-primary/10">
                          <User className="h-4 w-4 text-primary" />
                        </AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-56" align="end" forceMount>
                    <DropdownMenuLabel className="font-normal">
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none">{auth.user?.name}</p>
                        <p className="text-xs leading-none text-muted-foreground">
                          {auth.user?.email}
                        </p>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={auth.logout} className="text-destructive">
                      <LogOut className="mr-2 h-4 w-4" />
                      Log out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
