'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { CheckIcon, ChevronDownIcon } from "@radix-ui/react-icons"
import { cn } from "@/lib/utils"
import type { User } from '@/app/types/user'

interface UserAssignmentProps {
  selectedUser: User | null
  onUserSelect: (user: User | null) => void
  suggestedUsers: User[]
  className?: string
}

export function UserAssignment({
  selectedUser,
  onUserSelect,
  suggestedUsers = [],
  className,
}: UserAssignmentProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn("w-[200px] justify-between", className)}
        >
          {selectedUser ? (
            <div className="flex items-center gap-2">
              <Avatar className="h-6 w-6">
                <AvatarImage src={selectedUser.image} />
                <AvatarFallback>{selectedUser.username?.[0]}</AvatarFallback>
              </Avatar>
              <span>{selectedUser.username}</span>
            </div>
          ) : (
            <span>Assign to...</span>
          )}
          <ChevronDownIcon className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[200px] p-0" align="start">
        <div className="flex flex-col">
          <Button
            variant="ghost"
            className="justify-start"
            onClick={() => {
              onUserSelect(null)
              setOpen(false)
            }}
          >
            Unassign
          </Button>
          {suggestedUsers.map((user) => (
            <Button
              key={user.id}
              variant="ghost"
              className="justify-start"
              onClick={() => {
                onUserSelect(user)
                setOpen(false)
              }}
            >
              <div className="flex items-center gap-2">
                <Avatar className="h-6 w-6">
                  <AvatarImage src={user.image} />
                  <AvatarFallback>{user.username?.[0]}</AvatarFallback>
                </Avatar>
                <span>{user.username}</span>
                {selectedUser?.id === user.id && (
                  <CheckIcon className="ml-auto h-4 w-4" />
                )}
              </div>
            </Button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
