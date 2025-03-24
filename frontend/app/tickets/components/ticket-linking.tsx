'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Badge } from "@/components/ui/badge"
import { ChevronDownIcon, PlusIcon } from "@radix-ui/react-icons"
import type { Ticket } from '@/app/types/ticket'

interface TicketLinkingProps {
  ticketId: string
  linkedTickets: Ticket[]
  availableTickets: Ticket[]
  onLink: (linkedTicketId: string) => void
  onUnlink: (linkedTicketId: string) => void
}

export function TicketLinking({
  ticketId,
  linkedTickets,
  availableTickets,
  onLink,
  onUnlink,
}: TicketLinkingProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Linked Tickets</h3>
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm">
              <PlusIcon className="mr-2 h-4 w-4" />
              Link Ticket
            </Button>
          </PopoverTrigger>
          <PopoverContent className="p-0" side="bottom" align="end">
            <Command>
              <CommandInput
                placeholder="Search tickets..."
                value={search}
                onValueChange={setSearch}
              />
              <CommandEmpty>No tickets found.</CommandEmpty>
              <CommandGroup>
                {availableTickets
                  .filter(ticket => 
                    ticket.id !== ticketId && 
                    !linkedTickets.some(linked => linked.id === ticket.id)
                  )
                  .map(ticket => (
                    <CommandItem
                      key={ticket.id}
                      value={ticket.id}
                      onSelect={() => {
                        onLink(ticket.id)
                        setOpen(false)
                      }}
                    >
                      <span className="truncate">
                        {ticket.title}
                      </span>
                    </CommandItem>
                  ))}
              </CommandGroup>
            </Command>
          </PopoverContent>
        </Popover>
      </div>

      <div className="space-y-2">
        {linkedTickets.length === 0 ? (
          <p className="text-sm text-gray-500">No linked tickets</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {linkedTickets.map(ticket => (
              <Badge
                key={ticket.id}
                variant="secondary"
                className="flex items-center gap-2"
              >
                <span className="truncate max-w-[200px]">{ticket.title}</span>
                <button
                  onClick={() => onUnlink(ticket.id)}
                  className="text-xs hover:text-destructive"
                >
                  ×
                </button>
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
