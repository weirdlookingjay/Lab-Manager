'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import type { Ticket, TicketCreateRequest, TicketStatus, TicketPriority, RoutingRule, TicketActivityLogEntry } from '@/app/types/ticket'
import type { User } from '@/app/types/user'
import { getTickets, bulkUpdateTickets, mergeTickets, linkTickets, unlinkTickets, updateTicket, 
  getRoutingRules, createRoutingRule, updateRoutingRule, deleteRoutingRule, applyRoutingRules, createTicket } from '@/app/lib/api/tickets'
import { getUsers } from '@/app/lib/api/users'
import { formatDate, formatDateTime, formatTime } from '@/app/utils/date'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/app/hooks/useAuth'
import { toast } from '@/hooks/use-toast'
import { Calendar } from '@/components/ui/calendar'
import { CalendarIcon } from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/utils'
import { format } from 'date-fns'
import { ArrowUpDown, ArrowUp, ArrowDown, ChevronDown, MoreHorizontal, Maximize2, Minimize2, Pencil, Trash2, X } from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { useMemo } from 'react';
import { fetchWithAuth } from '@/app/utils/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

const priorityColors = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-blue-100 text-blue-800',
  high: 'bg-orange-100 text-orange-800',
  urgent: 'bg-red-100 text-red-800'
}

const statusConfig: Record<TicketStatus, {
  label: string;
  description: string;
  color: string;
  icon: React.ReactNode;
}> = {
  'open': {
    label: 'Open',
    description: 'Ticket has been created but work hasn\'t started',
    color: 'bg-blue-100 text-blue-800',
    icon: '🆕'
  },
  'in_progress': {
    label: 'In Progress',
    description: 'Work is actively being done on this ticket',
    color: 'bg-yellow-100 text-yellow-800',
    icon: '⚡'
  },
  'pending': {
    label: 'Pending',
    description: 'Waiting on something before work can continue',
    color: 'bg-orange-100 text-orange-800',
    icon: '⏳'
  },
  'resolved': {
    label: 'Resolved',
    description: 'Work is complete, pending verification',
    color: 'bg-green-100 text-green-800',
    icon: '✅'
  },
  'closed': {
    label: 'Closed',
    description: 'Ticket has been completed and verified',
    color: 'bg-gray-100 text-gray-800',
    icon: '🔒'
  }
}

const statusChangeReasons: Record<TicketStatus, string[]> = {
  'in_progress': [
    'Starting work',
    'Reopening for additional work',
    'Taking over ticket'
  ],
  'pending': [
    'Waiting for customer response',
    'Waiting for third-party',
    'Blocked by another ticket',
    'Need more information'
  ],
  'resolved': [
    'Work completed',
    'Solution implemented',
    'Fix deployed'
  ],
  'closed': [
    'Verified and completed',
    'No longer needed',
    'Duplicate ticket'
  ],
  'open': [
    'Reopening for review',
    'Issue reoccurred',
    'Additional work needed'
  ]
}

const validStatusTransitions: Record<TicketStatus, TicketStatus[]> = {
  'open': ['in_progress', 'pending', 'closed'],
  'in_progress': ['pending', 'resolved', 'closed'],
  'pending': ['in_progress', 'resolved', 'closed'],
  'resolved': ['closed', 'in_progress'],
  'closed': ['open']
}

type SortConfig = {
  column: string;
  direction: 'asc' | 'desc';
} | null;

export default function TicketsPage() {
  const router = useRouter()
  const auth = useAuth()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedTickets, setSelectedTickets] = useState<string[]>([])
  const [showAssignDialog, setShowAssignDialog] = useState(false)
  const [showMergeDialog, setShowMergeDialog] = useState(false)
  const [assignee, setAssignee] = useState('')
  const [mergeTitle, setMergeTitle] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [selectedPriority, setSelectedPriority] = useState<string>('all')
  const [selectedAssignee, setSelectedAssignee] = useState<string>('any')
  const [dateRange, setDateRange] = useState<{ from: Date | undefined; to: Date | undefined }>({
    from: undefined,
    to: undefined,
  })
  const [showRoutingRules, setShowRoutingRules] = useState(false)
  const [showLinkDialog, setShowLinkDialog] = useState(false)
  const [selectedTicketForAction, setSelectedTicketForAction] = useState<string | null>(null)
  const [routingRules, setRoutingRules] = useState<RoutingRule[]>([]);
  const [selectedRule, setSelectedRule] = useState<string | null>(null);
  const [editingRule, setEditingRule] = useState<RoutingRule | undefined>();
  const [showRuleSelectDialog, setShowRuleSelectDialog] = useState(false);
  const [showStatusDialog, setShowStatusDialog] = useState(false);
  const [selectedTicketForStatus, setSelectedTicketForStatus] = useState<string | null>(null)
  const [newStatus, setNewStatus] = useState<TicketStatus | null>(null)
  const [statusNote, setStatusNote] = useState('')
  const [selectedStatusReason, setSelectedStatusReason] = useState('')
  const [sortConfig, setSortConfig] = useState<SortConfig>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showAddTagsDialog, setShowAddTagsDialog] = useState(false)
  const [showRemoveTagsDialog, setShowRemoveTagsDialog] = useState(false)
  const [tagsToAdd, setTagsToAdd] = useState<string[]>([])
  const [tagsToRemove, setTagsToRemove] = useState<string[]>([])
  const [availableTags, setAvailableTags] = useState<string[]>([])
  const [expandedTicket, setExpandedTicket] = useState<string | null>(null)

  // Cache routing rules with timestamp
  const [routingRulesCache, setRoutingRulesCache] = useState<{
    data: RoutingRule[];
    timestamp: number;
  } | null>(null);

  const handleBulkAction = async (action: string) => {
    if (selectedTickets.length === 0) {
      toast({
        title: 'Error',
        description: 'Please select at least one ticket',
        variant: 'destructive',
      })
      return
    }

    try {
      if (action === 'assign') {
        setShowAssignDialog(true)
        return
      }

      if (action === 'merge') {
        setShowMergeDialog(true)
        return
      }

      if (action === 'apply-routing-rules') {
        setShowRuleSelectDialog(true)
        return
      }

      if (action === 'add-tags') {
        setShowAddTagsDialog(true)
        return
      }

      if (action === 'remove-tags') {
        // Get all unique tags from selected tickets
        const uniqueTags = new Set<string>()
        selectedTickets.forEach(ticketId => {
          const ticket = tickets.find(t => t.id === ticketId)
          if (ticket?.tags) {
            ticket.tags.forEach(tag => uniqueTags.add(tag))
          }
        })
        setAvailableTags(Array.from(uniqueTags))
        setShowRemoveTagsDialog(true)
        return
      }

      const [type, value] = action.split(':')
      if (type && value) {
        if (type === 'status') {
          const invalidTransitions: string[] = []
          for (const ticketId of selectedTickets) {
            const ticket = tickets.find(t => t.id === ticketId)
            if (!ticket) continue

            const error = getStatusTransitionError(ticket.status, value as TicketStatus)
            if (error) {
              invalidTransitions.push(`Ticket ${ticketId}: ${error}`)
            }
          }

          if (invalidTransitions.length > 0) {
            toast({
              title: 'Invalid Status Transitions',
              description: `Cannot update some tickets:\n${invalidTransitions.join('\n')}`,
              variant: 'destructive',
            })
            return
          }

          await bulkUpdateTickets(selectedTickets, type, value)
        } else {
          await bulkUpdateTickets(selectedTickets, type, value)
        }
        toast({
          title: 'Success',
          description: 'Tickets updated successfully',
        })
      }

      // Refresh tickets
      const updatedTickets = await getTickets()
      setTickets(updatedTickets)
      setSelectedTickets([])
    } catch (error) {
      console.error('Error performing bulk action:', error)
      toast({
        title: 'Error',
        description: 'Failed to perform bulk action',
        variant: 'destructive',
      })
    }
  }

  const getStatusTransitionError = (currentStatus: TicketStatus, newStatus: TicketStatus): string | null => {
    if (!validStatusTransitions[currentStatus]?.includes(newStatus)) {
      return `Cannot transition ticket from ${statusConfig[currentStatus].label} to ${statusConfig[newStatus].label}. Valid transitions are: ${validStatusTransitions[currentStatus]?.map(s => statusConfig[s].label).join(', ')}`
    }
    return null
  }

  const handleStatusChangeClick = (ticketId: string, status: TicketStatus) => {
    setSelectedTicketForStatus(ticketId)
    setNewStatus(status)
    setShowStatusDialog(true)
  }

  const handleStatusChange = async () => {
    if (!selectedTicketForStatus || !newStatus) return

    const ticket = tickets.find(t => t.id === selectedTicketForStatus)
    if (!ticket) {
      toast({
        title: 'Error',
        description: 'Ticket not found',
        variant: 'destructive',
      })
      return
    }

    const error = getStatusTransitionError(ticket.status, newStatus)
    if (error) {
      toast({
        title: 'Invalid Status Transition',
        description: error,
        variant: 'destructive',
      })
      return
    }

    try {
      const formattedNote = [
        `Status changed from ${statusConfig[ticket.status].label} to ${statusConfig[newStatus].label}`,
        `Reason: ${selectedStatusReason}`,
        statusNote ? `Note: ${statusNote}` : null
      ].filter(Boolean).join('\n')

      await updateTicket(selectedTicketForStatus, {
        status: newStatus,
        statusNote: formattedNote
      })

      const updatedTickets = await getTickets()
      setTickets(updatedTickets)

      toast({
        title: 'Success',
        description: `Ticket status updated to ${statusConfig[newStatus].label}`,
      })

      setShowStatusDialog(false)
      setSelectedTicketForStatus(null)
      setNewStatus(null)
      setStatusNote('')
      setSelectedStatusReason('')
    } catch (error) {
      console.error('Error updating ticket status:', error)
      toast({
        title: 'Error',
        description: 'Failed to update ticket status',
        variant: 'destructive',
      })
    }
  }

  const handleSort = (column: string) => {
    setSortConfig(current => {
      if (!current || current.column !== column) {
        return { column, direction: 'asc' }
      }
      if (current.direction === 'asc') {
        return { column, direction: 'desc' }
      }
      return null
    })
  }

  const getSortedTickets = (tickets: Ticket[]) => {
    if (!sortConfig) return tickets

    return [...tickets].sort((a, b) => {
      let aValue: any
      let bValue: any

      switch (sortConfig.column) {
        case 'title':
          aValue = a.title.toLowerCase()
          bValue = b.title.toLowerCase()
          break
        case 'status':
          aValue = a.status
          bValue = b.status
          break
        case 'priority':
          const priorityOrder = { low: 0, medium: 1, high: 2, urgent: 3 }
          aValue = priorityOrder[a.priority]
          bValue = priorityOrder[b.priority]
          break
        case 'assignedTo':
          aValue = a.assigned_to?.first_name || ''
          bValue = b.assigned_to?.first_name || ''
          break
        case 'createdBy':
          aValue = a.created_by.first_name
          bValue = b.created_by.first_name
          break
        case 'created':
          aValue = new Date(a.created_at).getTime()
          bValue = new Date(b.created_at).getTime()
          break
        case 'sla':
          aValue = a.sla_breach_at ? new Date(a.sla_breach_at).getTime() : Infinity
          bValue = b.sla_breach_at ? new Date(b.sla_breach_at).getTime() : Infinity
          break
        default:
          return 0
      }

      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1
      return 0
    })
  }

  const getSortIcon = (column: string) => {
    if (!sortConfig || sortConfig.column !== column) {
      return <ArrowUpDown className="ml-2 h-4 w-4" />
    }
    return sortConfig.direction === 'asc' ? (
      <ArrowUp className="ml-2 h-4 w-4" />
    ) : (
      <ArrowDown className="ml-2 h-4 w-4" />
    )
  }

  const handleSingleTicketAction = (ticketId: string, action: string) => {
    console.log('Single ticket action:', action, 'for ticket:', ticketId)
    switch (action) {
      case 'routing-rule':
        setSelectedTickets([ticketId])
        setShowRuleSelectDialog(true)
        break
      case 'status':
        setSelectedTickets([ticketId])
        setSelectedTicketForStatus(ticketId)
        setShowStatusDialog(true)
        break
      case 'assign':
        setSelectedTickets([ticketId])
        setShowAssignDialog(true)
        break
      default:
        break
    }
  }

  const renderTicketRow = (ticket: Ticket) => {
    return (
      <TableRow key={ticket.id}>
        <TableCell className="w-[40px]">
          <Checkbox
            checked={selectedTickets.includes(ticket.id)}
            onCheckedChange={(checked) => {
              if (checked) {
                setSelectedTickets([...selectedTickets, ticket.id])
              } else {
                setSelectedTickets(selectedTickets.filter(id => id !== ticket.id))
              }
            }}
          />
        </TableCell>
        <TableCell>
          <div className="flex flex-col space-y-1">
            <Link href={`/tickets/${ticket.id}`} className="font-medium hover:underline">
              {ticket.title}
            </Link>
            <div className="text-sm text-gray-500">
              Created {formatDateTime(ticket.created_at)}
            </div>
          </div>
        </TableCell>
        <TableCell>
          <div className="flex items-center space-x-2">
            <span className={cn("w-2 h-2 rounded-full", priorityColors[ticket.priority])} />
            <Link href={`/tickets/${ticket.id}`} className="hover:underline">
              {ticket.title}
            </Link>
          </div>
        </TableCell>
        <TableCell>
          <div className={cn("inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium", statusConfig[ticket.status].color)}>
            {statusConfig[ticket.status].icon} {statusConfig[ticket.status].label}
          </div>
        </TableCell>
        <TableCell>
          <Badge className={priorityColors[ticket.priority]}>
            {ticket.priority}
          </Badge>
        </TableCell>
        <TableCell>
          {ticket.assigned_to ? (
            <span>{ticket.assigned_to.first_name} {ticket.assigned_to.last_name}</span>
          ) : (
            <span className="text-gray-500">Unassigned</span>
          )}
        </TableCell>
        <TableCell>
          {ticket.created_by.first_name} {ticket.created_by.last_name}
        </TableCell>
        <TableCell>
          {format(new Date(ticket.created_at), 'MMM d, yyyy')}
        </TableCell>
        <TableCell>
          {ticket.sla_breach_at && (
            <Badge variant={new Date(ticket.sla_breach_at) < new Date() ? 'destructive' : 'outline'}>
              {format(new Date(ticket.sla_breach_at), 'MMM d, yyyy')}
            </Badge>
          )}
        </TableCell>
        <TableCell>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="h-8 w-8 p-0"
                onClick={(e) => e.stopPropagation()}
              >
                <span className="sr-only">Open menu</span>
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
              <DropdownMenuItem
                onSelect={(e) => {
                  e.preventDefault()
                  handleSingleTicketAction(ticket.id, 'routing-rule')
                }}
                onClick={(e) => {
                  e.stopPropagation()
                  handleSingleTicketAction(ticket.id, 'routing-rule')
                }}
              >
                Apply Routing Rule
              </DropdownMenuItem>
              <DropdownMenuItem
                onSelect={(e) => {
                  e.preventDefault()
                  handleSingleTicketAction(ticket.id, 'status')
                }}
                onClick={(e) => {
                  e.stopPropagation()
                  handleSingleTicketAction(ticket.id, 'status')
                }}
              >
                Change Status
              </DropdownMenuItem>
              <DropdownMenuItem
                onSelect={(e) => {
                  e.preventDefault()
                  handleSingleTicketAction(ticket.id, 'assign')
                }}
                onClick={(e) => {
                  e.stopPropagation()
                  handleSingleTicketAction(ticket.id, 'assign')
                }}
              >
                Assign
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </TableCell>
      </TableRow>
    )
  }

  // Type guard for User object
  const isUser = (value: any): value is User => {
    return value && typeof value === 'object' && 'first_name' in value && 'last_name' in value;
  };

  const formatUserString = (userStr: string | User): string => {
    if (typeof userStr === 'object' && userStr !== null) {
      return `${userStr.first_name} ${userStr.last_name}`;
    }
    try {
      const user = JSON.parse(userStr);
      if (isUser(user)) {
        return `${user.first_name} ${user.last_name}`;
      }
    } catch {
      // If parsing fails, return the original string
    }
    return String(userStr);
  };

  // Fetch routing rules with caching
  const fetchRoutingRules = async (forceRefresh = false) => {
    try {
      // Use cache if available and less than 5 minutes old
      const now = Date.now();
      if (!forceRefresh && 
          routingRulesCache && 
          (now - routingRulesCache.timestamp < 5 * 60 * 1000)) {
        setRoutingRules(routingRulesCache.data);
        return;
      }

      const rules = await getRoutingRules();
      setRoutingRules(rules);
      setRoutingRulesCache({
        data: rules,
        timestamp: now,
      });
    } catch (error) {
      console.error('Error fetching routing rules:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch routing rules',
        variant: 'destructive',
      });
    }
  };

  // Initial fetch of routing rules
  useEffect(() => {
    fetchRoutingRules();
  }, []); // Empty dependency array as this should only run once on mount

  // Update routing rules cache after modifications
  const updateRoutingRulesCache = (updatedRules: RoutingRule[]) => {
    setRoutingRules(updatedRules);
    setRoutingRulesCache({
      data: updatedRules,
      timestamp: Date.now(),
    });
  };

  const handleToggleRule = async (ruleId: string, isActive: boolean) => {
    try {
      await updateRoutingRule(ruleId, { isActive });
      const updatedRules = routingRules.map(rule =>
        rule.id === ruleId ? { ...rule, isActive } : rule
      );
      updateRoutingRulesCache(updatedRules);
      toast({
        title: 'Success',
        description: `Rule ${isActive ? 'activated' : 'deactivated'} successfully`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update rule status',
        variant: 'destructive',
      });
    }
  };

  const handleSaveRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingRule) return;

    try {
      let updatedRules;
      if (editingRule.id) {
        const updatedRule = await updateRoutingRule(editingRule.id, editingRule);
        updatedRules = routingRules.map(r => 
          r.id === editingRule.id ? updatedRule : r
        );
      } else {
        const newRule = await createRoutingRule(editingRule);
        updatedRules = [...routingRules, newRule];
      }
      updateRoutingRulesCache(updatedRules);
      setEditingRule(undefined);
      toast({
        title: 'Success',
        description: `Rule ${editingRule.id ? 'updated' : 'created'} successfully`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to ${editingRule.id ? 'update' : 'create'} rule`,
        variant: 'destructive',
      });
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    try {
      await deleteRoutingRule(ruleId);
      const updatedRules = routingRules.filter(r => r.id !== ruleId);
      updateRoutingRulesCache(updatedRules);
      toast({
        title: 'Success',
        description: 'Rule deleted successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete rule',
        variant: 'destructive',
      });
    }
  };

  const applyRoutingRule = async (ruleId: string, ticketIds: string[]): Promise<void> => {
    try {
      await fetchWithAuth(`/api/tickets/routing-rules/${ruleId}/apply/`, {
        method: 'POST',
        body: JSON.stringify({ ticket_ids: ticketIds }),
      });
    } catch (error) {
      console.error('Error applying routing rule:', error);
      throw new Error(error instanceof Error ? error.message : 'Failed to apply routing rule. Please check your network connection.');
    }
  };

  const handleApplyRule = async (ruleId: string, ticketIds: string[]) => {
    try {
      await applyRoutingRule(ruleId, ticketIds);
      // Refresh tickets after applying rule
      const updatedTickets = await getTickets();
      setTickets(updatedTickets);
      toast({
        title: 'Success',
        description: 'Routing rule applied successfully',
      });
    } catch (error) {
      console.error('Error applying routing rule:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to apply routing rule',
        variant: 'destructive',
      });
    }
  };

  // Check auth state on component mount
  useEffect(() => {
    if (!auth?.isAuthenticated) {
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true)
        const [ticketsData, usersData] = await Promise.all([
          getTickets(),
          getUsers()
        ])
        setTickets(ticketsData)
        setUsers(usersData)
      } catch (error) {
        console.error('Error fetching data:', error)
        setError('Failed to fetch data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [auth?.isAuthenticated])

  const refreshData = async () => {
    try {
      setLoading(true)
      const [ticketsData] = await Promise.all([
        getTickets()
      ])
      setTickets(ticketsData)
    } catch (error) {
      console.error('Error refreshing data:', error)
      setError('Failed to refresh data')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedTickets(tickets.map(ticket => ticket.id))
    } else {
      setSelectedTickets([])
    }
  }

  const handleSelectTicket = (ticketId: string, checked: boolean) => {
    if (checked) {
      setSelectedTickets([...selectedTickets, ticketId])
    } else {
      setSelectedTickets(selectedTickets.filter(id => id !== ticketId))
    }
  }

  const handleAssign = async () => {
    setLoading(true)
    try {
      await bulkUpdateTickets(selectedTickets, 'assign', assignee)
      setShowAssignDialog(false)
      
      // Refresh tickets
      await refreshData()
      setSelectedTickets([])
      setAssignee('')
    } catch (error) {
      console.error('Assignment failed:', error)
      setError('Failed to assign tickets')
    } finally {
      setLoading(false)
    }
  }

  const handleMerge = async () => {
    setLoading(true)
    try {
      await mergeTickets(selectedTickets, mergeTitle)
      setShowMergeDialog(false)
      
      // Refresh tickets
      await refreshData()
      setSelectedTickets([])
      setMergeTitle('')
    } catch (error) {
      console.error('Merge failed:', error)
      setError('Failed to merge tickets')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateRule = async (rule: Omit<RoutingRule, 'id'>) => {
    try {
      await createRoutingRule(rule)
      const rules = await getRoutingRules()
      setRoutingRules(rules)
      toast({
        title: 'Success',
        description: 'Routing rule created successfully',
      })
    } catch (error) {
      console.error('Error creating routing rule:', error)
      toast({
        title: 'Error',
        description: 'Failed to create routing rule',
        variant: 'destructive',
      })
    }
  }

  const handleUpdateRule = async (id: string, rule: Omit<RoutingRule, 'id'>) => {
    try {
      await updateRoutingRule(id, rule)
      // Refresh both rules and tickets data
      const [rules, tickets] = await Promise.all([
        getRoutingRules(),
        getTickets()
      ])
      setRoutingRules(rules)
      setTickets(tickets)
      setSelectedTickets([]) // Clear selected tickets after successful update
      toast({
        title: 'Success',
        description: 'Routing rule updated successfully',
      })
    } catch (error) {
      console.error('Error updating routing rule:', error)
      toast({
        title: 'Error',
        description: 'Failed to update routing rule',
        variant: 'destructive',
      })
    }
  }

  const handleTicketAction = async (ticketId: string, action: string) => {
    setSelectedTicketForAction(ticketId)
    switch (action) {
      case 'edit':
        router.push(`/tickets/${ticketId}`)
        break
      case 'assign':
        setShowAssignDialog(true)
        break
      case 'link':
        setShowLinkDialog(true)
        break
      case 'close':
        try {
          await updateTicket(ticketId, { status: 'closed' })
          await refreshData()
        } catch (error) {
          console.error('Error closing ticket:', error)
          setError('Failed to close ticket')
        }
        break
    }
  }

  const handleApplyRoutingRules = async (ticketIds: string[]) => {
    if (!selectedRule) {
      toast({
        title: 'Error',
        description: 'Please select a rule to apply',
        variant: 'destructive',
      });
      return;
    }

    try {
      await handleApplyRule(selectedRule, ticketIds);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to apply routing rule',
        variant: 'destructive',
      });
    }
  };

  const handleCreateTicket = async (data: TicketCreateRequest) => {
    try {
      const ticket = await createTicket(data)
      
      // Apply routing rules
      if (routingRules.length > 0) {
        const routingResult = await applyRoutingRules({
          id: ticket.id,
          title: ticket.title,
          description: ticket.description,
          priority: ticket.priority,
          custom_fields: ticket.custom_fields
        }, routingRules)

        if (routingResult.assigneeId) {
          const assignedUser = users.find(u => u.id.toString() === routingResult.assigneeId)
          if (assignedUser) {
            toast({
              title: 'Ticket Assigned',
              description: `Ticket automatically assigned to ${assignedUser.first_name} ${assignedUser.last_name}`,
            })
          }
        }

        if (routingResult.updatedPriority) {
          toast({
            title: 'Priority Updated',
            description: `Ticket priority set to ${routingResult.updatedPriority}`,
          })
        }
      }

      // Refresh tickets list
      const tickets = await getTickets()
      setTickets(tickets)

      toast({
        title: 'Success',
        description: 'Ticket created successfully',
      })
    } catch (error) {
      console.error('Error creating ticket:', error)
      toast({
        title: 'Error',
        description: 'Failed to create ticket',
        variant: 'destructive',
      })
    }
  }

  const handleAddTags = async () => {
    try {
      for (const ticketId of selectedTickets) {
        const ticket = tickets.find(t => t.id === ticketId)
        if (!ticket) continue

        const updatedTags = [...(ticket.tags || []), ...tagsToAdd]
        await updateTicket(ticketId, { tags: updatedTags })
      }

      toast({
        title: 'Success',
        description: `Added tags to ${selectedTickets.length} ticket(s)`,
      })

      // Refresh tickets
      const updatedTickets = await getTickets()
      setTickets(updatedTickets)
      setSelectedTickets([])
      setShowAddTagsDialog(false)
      setTagsToAdd([])
    } catch (error) {
      console.error('Error adding tags:', error)
      toast({
        title: 'Error',
        description: 'Failed to add tags',
        variant: 'destructive',
      })
    }
  }

  const handleRemoveTags = async () => {
    try {
      for (const ticketId of selectedTickets) {
        const ticket = tickets.find(t => t.id === ticketId)
        if (!ticket) continue

        const updatedTags = (ticket.tags || []).filter(tag => !tagsToRemove.includes(tag))
        await updateTicket(ticketId, { tags: updatedTags })
      }

      toast({
        title: 'Success',
        description: `Removed tags from ${selectedTickets.length} ticket(s)`,
      })

      // Refresh tickets
      const updatedTickets = await getTickets()
      setTickets(updatedTickets)
      setSelectedTickets([])
      setShowRemoveTagsDialog(false)
      setTagsToRemove([])
    } catch (error) {
      console.error('Error removing tags:', error)
      toast({
        title: 'Error',
        description: 'Failed to remove tags',
        variant: 'destructive',
      })
    }
  }

  const filteredTickets = useMemo(() => {
    return tickets.filter(ticket => {
      // Search query filter
      if (searchQuery && !ticket.title.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }

      // Status filter
      if (selectedStatus !== 'all' && ticket.status !== selectedStatus) {
        return false
      }

      // Priority filter
      if (selectedPriority !== 'all' && ticket.priority !== selectedPriority) {
        return false
      }

      // Assignee filter
      if (selectedAssignee !== 'any') {
        if (selectedAssignee === 'unassigned' && ticket.assigned_to) {
          return false
        }
        if (selectedAssignee !== 'unassigned' && ticket.assigned_to?.id.toString() !== selectedAssignee) {
          return false
        }
      }

      // Date range filter
      if (dateRange.from || dateRange.to) {
        const ticketDate = new Date(ticket.created_at)
        if (dateRange.from && ticketDate < dateRange.from) {
          return false
        }
        if (dateRange.to) {
          const endDate = new Date(dateRange.to)
          endDate.setHours(23, 59, 59, 999)
          if (ticketDate > endDate) {
            return false
          }
        }
      }

      return true
    })
  }, [tickets, searchQuery, selectedStatus, selectedPriority, selectedAssignee, dateRange])

  const filteredAndSortedTickets = getSortedTickets(filteredTickets)

  const handleAddCondition = () => {
    if (editingRule) {
      setEditingRule({
        ...editingRule,
        conditions: {
          ...editingRule.conditions,
          tags: [...(editingRule.conditions?.tags || []), '']
        }
      });
    }
  };

  const handleUpdateCondition = (index: number, value: string) => {
    if (editingRule) {
      const tags = [...(editingRule.conditions?.tags || [])];
      tags[index] = value;
      setEditingRule({
        ...editingRule,
        conditions: {
          ...editingRule.conditions,
          tags
        }
      });
    }
  };

  const handleRemoveCondition = (index: number) => {
    if (editingRule) {
      const tags = [...(editingRule.conditions?.tags || [])];
      tags.splice(index, 1);
      setEditingRule({
        ...editingRule,
        conditions: {
          ...editingRule.conditions,
          tags
        }
      });
    }
  };

  const getCsrfToken = (): string => {
    const name = 'csrftoken';
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      const csrfToken = parts.pop()?.split(';').shift();
      return csrfToken || '';
    }
    return '';
  };

  const getRoutingRules = async (): Promise<RoutingRule[]> => {
    try {
      return await fetchWithAuth('/api/tickets/routing-rules/');
    } catch (error) {
      console.error('Error fetching routing rules:', error);
      throw new Error(error instanceof Error ? error.message : 'Failed to fetch routing rules. Please check your network connection.');
    }
  };

  const createRoutingRule = async (rule: Omit<RoutingRule, 'id'>): Promise<RoutingRule> => {
    const { assignTo, ...ruleData } = rule;
    const apiData = {
      ...ruleData,
      assign_to_id: assignTo?.id,
    };

    try {
      return await fetchWithAuth('/api/tickets/routing-rules/', {
        method: 'POST',
        body: JSON.stringify(apiData),
      });
    } catch (error) {
      console.error('Error creating routing rule:', error);
      throw new Error(error instanceof Error ? error.message : 'Failed to create routing rule. Please check your network connection.');
    }
  };

  const updateRoutingRule = async (id: string, rule: Partial<RoutingRule>): Promise<RoutingRule> => {
    const { assignTo, ...ruleData } = rule;
    const apiData = {
      ...ruleData,
      assign_to_id: assignTo?.id,
    };

    try {
      return await fetchWithAuth(`/api/tickets/routing-rules/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(apiData),
      });
    } catch (error) {
      console.error('Error updating routing rule:', error);
      throw new Error(error instanceof Error ? error.message : 'Failed to update routing rule. Please check your network connection.');
    }
  };

  const deleteRoutingRule = async (id: string): Promise<void> => {
    try {
      await fetchWithAuth(`/api/tickets/routing-rules/${id}/`, {
        method: 'DELETE',
      });
    } catch (error) {
      console.error('Error deleting routing rule:', error);
      throw new Error(error instanceof Error ? error.message : 'Failed to delete routing rule. Please check your network connection.');
    }
  };

  useEffect(() => {
    const fetchRules = async () => {
      try {
        const rules = await getRoutingRules();
        // Ensure all rules have an id
        const validRules = rules.filter((rule: RoutingRule) => rule.id) as RoutingRule[];
        setRoutingRules(validRules);
      } catch (error) {
        toast({
          title: 'Error',
          description: 'Failed to fetch routing rules',
          variant: 'destructive',
        });
      }
    };
    fetchRules();
  }, [toast]);

  return (
    <div className="container mx-auto py-10">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Tickets</h1>
        <div className="space-x-2">
          <Button onClick={() => setShowRoutingRules(!showRoutingRules)}>
            {showRoutingRules ? 'Hide Routing Rules' : 'Show Routing Rules'}
          </Button>
          <Button asChild>
            <Link href="/tickets/new">Create Ticket</Link>
          </Button>
          {selectedTickets.length > 0 && (
            <Select onValueChange={handleBulkAction}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Bulk Actions" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectLabel>Status</SelectLabel>
                  <SelectItem value="status:open">Set Open</SelectItem>
                  <SelectItem value="status:in_progress">Set In Progress</SelectItem>
                  <SelectItem value="status:pending">Set Pending</SelectItem>
                  <SelectItem value="status:resolved">Set Resolved</SelectItem>
                  <SelectItem value="status:closed">Set Closed</SelectItem>
                </SelectGroup>
                <SelectGroup>
                  <SelectLabel>Priority</SelectLabel>
                  <SelectItem value="priority:low">Set Low Priority</SelectItem>
                  <SelectItem value="priority:medium">Set Medium Priority</SelectItem>
                  <SelectItem value="priority:high">Set High Priority</SelectItem>
                  <SelectItem value="priority:urgent">Set Urgent Priority</SelectItem>
                </SelectGroup>
                <SelectGroup>
                  <SelectLabel>Assignment</SelectLabel>
                  <SelectItem value="assign">Assign Tickets</SelectItem>
                </SelectGroup>
                <SelectGroup>
                  <SelectLabel>Rules</SelectLabel>
                  <SelectItem value="apply-routing-rules">Apply Routing Rules</SelectItem>
                </SelectGroup>
                <SelectGroup>
                  <SelectLabel>Other</SelectLabel>
                  <SelectItem value="merge">Merge Tickets</SelectItem>
                  <SelectItem value="add-tags">Add Tags</SelectItem>
                  <SelectItem value="remove-tags">Remove Tags</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          )}
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40px]">
                <Checkbox
                  checked={selectedTickets.length === filteredAndSortedTickets.length}
                  onCheckedChange={handleSelectAll}
                />
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort('title')}
                  className="flex items-center"
                >
                  Title {getSortIcon('title')}
                </Button>
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort('status')}
                  className="flex items-center"
                >
                  Status {getSortIcon('status')}
                </Button>
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort('priority')}
                  className="flex items-center"
                >
                  Priority {getSortIcon('priority')}
                </Button>
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort('assignedTo')}
                  className="flex items-center"
                >
                  Assigned To {getSortIcon('assignedTo')}
                </Button>
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort('createdBy')}
                  className="flex items-center"
                >
                  Created By {getSortIcon('createdBy')}
                </Button>
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort('created')}
                  className="flex items-center"
                >
                  Created {getSortIcon('created')}
                </Button>
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort('sla')}
                  className="flex items-center"
                >
                  SLA {getSortIcon('sla')}
                </Button>
              </TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredAndSortedTickets.map(renderTicketRow)}
          </TableBody>
        </Table>
      </div>

      {showRoutingRules && (
        <Dialog open={showRoutingRules} onOpenChange={setShowRoutingRules}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Routing Rules</DialogTitle>
            </DialogHeader>

            <div className="space-y-4">
              <div className="flex justify-end">
                <Button onClick={() => setEditingRule({
                  id: '',
                  name: '',
                  conditions: {
                    tags: [], // Ensure tags is initialized as empty array
                    priority: undefined,
                    status: undefined,
                    assignedTo: undefined
                  },
                  actions: {
                    setPriority: undefined,
                    setStatus: undefined,
                    setTags: []
                  },
                  assignTo: null,
                  isActive: true,
                  createdAt: new Date().toISOString(),
                  updatedAt: new Date().toISOString()
                })}>
                  Add Rule
                </Button>
              </div>

              <div className="space-y-4">
                {routingRules.map((rule) => (
                  <div
                    key={rule.id}
                    className="flex items-start justify-between p-4 border rounded-lg hover:bg-gray-50"
                  >
                    <div className="space-y-1">
                      <div className="font-medium">{rule.name}</div>
                      <div className="text-sm">
                        {rule.conditions?.tags && rule.conditions.tags.length > 0 ? (
                          <div className="space-y-1">
                            <div className="font-medium">Conditions:</div>
                            <ul className="list-disc list-inside">
                              {rule.conditions.tags.map((tag, index) => (
                                <li key={index}>
                                  Contains: {tag}
                                </li>
                              ))}
                              {rule.conditions.priority && (
                                <li>Priority: {rule.conditions.priority}</li>
                              )}
                            </ul>
                          </div>
                        ) : null}
                        <div>
                          Assigned to: {rule.assignTo?.first_name || 'Unassigned'}
                        </div>
                        <div>
                          Status: {rule.isActive ? 'Active' : 'Inactive'}
                        </div>
                      </div>
                      <div className="text-sm">
                        <div className="font-medium">Actions:</div>
                        <ul className="list-disc list-inside">
                          {rule.actions?.setPriority && (
                            <li>Set Priority: {rule.actions.setPriority}</li>
                          )}
                          {rule.actions?.setStatus && (
                            <li>Set Status: {rule.actions.setStatus}</li>
                          )}
                          {rule.actions?.setTags && rule.actions.setTags.length > 0 && (
                            <li>Add Tags: {rule.actions.setTags.join(', ')}</li>
                          )}
                          {!rule.actions?.setPriority && !rule.actions?.setStatus && (!rule.actions?.setTags || rule.actions.setTags.length === 0) && (
                            <li className="text-gray-500">No actions configured</li>
                          )}
                        </ul>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={rule.isActive}
                        onCheckedChange={(checked) => {
                          if (rule.id) {
                            handleToggleRule(rule.id, checked)
                          }
                        }}
                      />
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setEditingRule(rule)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => {
                          if (rule.id) {
                            handleDeleteRule(rule.id)
                          }
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Rule Select Dialog */}
      <Dialog open={showRuleSelectDialog} onOpenChange={setShowRuleSelectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Apply Routing Rule</DialogTitle>
            <DialogDescription>
              Select a routing rule to apply to the selected ticket(s)
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="rule">Routing Rule</Label>
              <Select
                value={selectedRule ?? ""}
                onValueChange={(value: string) => setSelectedRule(value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select rule" />
                </SelectTrigger>
                <SelectContent>
                  {routingRules.map((rule) => (
                    <SelectItem key={rule.id} value={rule.id}>
                      {rule.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowRuleSelectDialog(false)
                setSelectedRule(null)
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={() => handleApplyRoutingRules(selectedTickets)}
            >
              Apply Rule
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Status Change Dialog */}
      <Dialog open={showStatusDialog} onOpenChange={setShowStatusDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Status</DialogTitle>
            <DialogDescription>
              Select a new status for the ticket(s)
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select
                value={newStatus || ""}
                onValueChange={(value) => setNewStatus(value as TicketStatus)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="statusNote">Note (Optional)</Label>
              <Textarea
                id="statusNote"
                value={statusNote}
                onChange={(e) => setStatusNote(e.target.value)}
                placeholder="Add a note about this status change..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowStatusDialog(false)
                setNewStatus(null)
                setStatusNote('')
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={async () => {
                try {
                  if (!newStatus) {
                    toast({
                      title: 'Error',
                      description: 'Please select a status',
                      variant: 'destructive',
                    })
                    return
                  }

                  // Check for invalid transitions
                  const invalidTransitions: string[] = []
                  for (const ticketId of selectedTickets) {
                    const ticket = tickets.find(t => t.id === ticketId)
                    if (!ticket) continue

                    const error = getStatusTransitionError(ticket.status, newStatus)
                    if (error) {
                      invalidTransitions.push(`Ticket ${ticketId}: ${error}`)
                    }
                  }

                  if (invalidTransitions.length > 0) {
                    toast({
                      title: 'Invalid Status Transitions',
                      description: invalidTransitions.join('\n'),
                      variant: 'destructive',
                    })
                    return
                  }

                  // Apply status changes
                  for (const ticketId of selectedTickets) {
                    await updateTicket(ticketId, {
                      status: newStatus,
                      statusNote: statusNote || undefined
                    })
                  }

                  const updatedTickets = await getTickets()
                  setTickets(updatedTickets)

                  toast({
                    title: 'Success',
                    description: `Updated status for ${selectedTickets.length} ticket(s)`,
                  })

                  setShowStatusDialog(false)
                  setNewStatus(null)
                  setStatusNote('')
                  setSelectedTickets([])
                  toast({
                    title: 'Success',
                    description: `Updated status for ${selectedTickets.length} ticket(s)`,
                  })
                } catch (error) {
                  console.error('Error updating status:', error)
                  toast({
                    title: 'Error',
                    description: 'Failed to update status',
                    variant: 'destructive',
                  })
                }
              }}
            >
              Update Status
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign Dialog */}
      <Dialog open={showAssignDialog} onOpenChange={setShowAssignDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assign Ticket</DialogTitle>
            <DialogDescription>
              Select a user to assign the ticket to
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="assignee">Assignee</Label>
              <Select
                value={assignee}
                onValueChange={setAssignee}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select assignee" />
                </SelectTrigger>
                <SelectContent>
                  {users.map((user) => (
                    <SelectItem key={user.id} value={user.id}>
                      {user.first_name} {user.last_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowAssignDialog(false)
                setAssignee('')
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={async () => {
                try {
                  for (const ticketId of selectedTickets) {
                    await updateTicket(ticketId, { assigned_to: assignee })
                  }
                  const updatedTickets = await getTickets()
                  setTickets(updatedTickets)
                  setShowAssignDialog(false)
                  setAssignee('')
                  setSelectedTickets([])
                  toast({
                    title: 'Success',
                    description: `Assigned ${selectedTickets.length} ticket(s)`,
                  })
                } catch (error) {
                  console.error('Error assigning tickets:', error)
                  toast({
                    title: 'Error',
                    description: 'Failed to assign tickets',
                    variant: 'destructive',
                  })
                }
              }}
            >
              Assign
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {filteredAndSortedTickets.map(ticket => (
        <div key={ticket.id} className="mt-4">
          <Tabs defaultValue="details">
            <TabsList>
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="history">History</TabsTrigger>
              <TabsTrigger value="notes">Notes</TabsTrigger>
            </TabsList>
            <TabsContent value="details">
              <div className="space-y-4">
                {/* Ticket details content */}
              </div>
            </TabsContent>
            <TabsContent value="history">
              <div className="space-y-2 py-2">
                {ticket.activity_log && ticket.activity_log.map((activity, index) => {
                  let actionText = '';
                  if (activity.action === 'status_change') {
                    actionText = `Status changed from ${activity.old_value} to ${activity.new_value}`;
                  } else if (activity.action === 'assignment') {
                    actionText = `Assigned to ${formatUserString(activity.new_value)}`;
                  } else if (activity.action === 'priority_change') {
                    actionText = `Priority changed from ${activity.old_value} to ${activity.new_value}`;
                  }
                  
                  return (
                    <div key={index} className="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50">
                      <div className="w-32 flex-shrink-0 text-sm text-gray-500">
                        {formatDateTime(activity.timestamp)}
                      </div>
                      <div className="flex-1">
                        <div className="text-sm text-gray-900">{actionText}</div>
                        {activity.note && (
                          <div className="text-sm text-gray-500 mt-1">
                            Note: {activity.note}
                          </div>
                        )}
                        <div className="text-xs text-gray-500 mt-1">
                          by {formatUserString(activity.user)}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </TabsContent>
            <TabsContent value="notes">
              <div className="space-y-4">
                {/* Notes content */}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      ))}
    </div>
  )
}
