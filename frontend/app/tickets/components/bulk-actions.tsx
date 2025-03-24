'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ChevronDownIcon } from "@radix-ui/react-icons"

interface BulkActionsProps {
  selectedCount: number
  selectedTickets: string[]
  onAction: (action: string, value?: string) => void
  onMerge: (ticketIds: string[], title: string) => void
  disabled?: boolean
}

export function BulkActions({ selectedCount, selectedTickets, onAction, onMerge, disabled }: BulkActionsProps) {
  const [showMergeDialog, setShowMergeDialog] = useState(false)
  const [mergeTitle, setMergeTitle] = useState('')

  const handleMerge = () => {
    if (mergeTitle) {
      onMerge(selectedTickets, mergeTitle)
      setShowMergeDialog(false)
      setMergeTitle('')
    }
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" disabled={disabled}>
            Bulk Actions ({selectedCount}) <ChevronDownIcon className="ml-2 h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuItem onClick={() => onAction('status:in_progress')}>
            Set Status: In Progress
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => onAction('status:resolved')}>
            Set Status: Resolved
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => onAction('status:closed')}>
            Set Status: Closed
          </DropdownMenuItem>
          
          <DropdownMenuSeparator />
          
          <DropdownMenuItem onClick={() => onAction('priority:low')}>
            Set Priority: Low
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => onAction('priority:medium')}>
            Set Priority: Medium
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => onAction('priority:high')}>
            Set Priority: High
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => onAction('priority:urgent')}>
            Set Priority: Urgent
          </DropdownMenuItem>

          <DropdownMenuSeparator />

          {selectedCount >= 2 && (
            <DropdownMenuItem onClick={() => setShowMergeDialog(true)}>
              Merge Tickets
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={showMergeDialog} onOpenChange={setShowMergeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Merge {selectedCount} Tickets</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="title">New Ticket Title</Label>
              <Input
                id="title"
                placeholder="Enter title for merged ticket"
                value={mergeTitle}
                onChange={(e) => setMergeTitle(e.target.value)}
              />
            </div>
            <div className="pt-4 flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowMergeDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleMerge} disabled={!mergeTitle}>
                Merge Tickets
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
