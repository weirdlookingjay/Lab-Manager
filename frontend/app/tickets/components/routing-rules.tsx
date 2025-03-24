'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import type { RoutingRule, TicketPriority } from '@/app/types/ticket'
import type { User } from '@/app/types/user'

const validPriorities = ['low', 'medium', 'high', 'urgent'] as const
type ValidPriority = typeof validPriorities[number]

const isValidPriority = (priority: string | undefined): priority is ValidPriority => {
  return !!priority && validPriorities.includes(priority as ValidPriority)
}

const formSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  conditions: z.object({
    keywords: z.array(z.string()).default([]),
    customFields: z.record(z.any()).optional()
  }),
  actions: z.object({
    setPriority: z.enum(validPriorities).optional(),
    setAssignee: z.union([z.literal('no_change'), z.string()]).optional()
  }).optional(),
  assignTo: z.string().min(1, 'Assignee is required'),
  isActive: z.boolean()
})

type FormData = z.infer<typeof formSchema>

interface RoutingRulesProps {
  users: User[]
  rules: RoutingRule[]
  onCreateRule: (rule: Omit<RoutingRule, 'id'>) => Promise<void>
  onUpdateRule: (id: string, rule: Omit<RoutingRule, 'id'>) => Promise<void>
  onDeleteRule: (id: string) => Promise<void>
  editingRule?: RoutingRule
  onClose: () => void
  setEditingRule: (rule: RoutingRule | undefined) => void
}

export function RoutingRules({ users, rules, onCreateRule, onUpdateRule, onDeleteRule, editingRule, onClose, setEditingRule }: RoutingRulesProps) {
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: editingRule?.name || '',
      conditions: {
        keywords: editingRule?.conditions?.keywords || [],
        customFields: editingRule?.conditions?.customFields || {}
      },
      actions: {
        setPriority: editingRule?.actions?.setPriority as ValidPriority | undefined,
        setAssignee: editingRule?.actions?.setAssignee
      },
      assignTo: editingRule?.assignTo || '',
      isActive: editingRule?.isActive ?? true
    }
  })

  // Reset form when editingRule changes
  useEffect(() => {
    if (editingRule) {
      form.reset({
        name: editingRule.name,
        conditions: {
          keywords: editingRule.conditions?.keywords || [],
          customFields: editingRule.conditions?.customFields || {}
        },
        actions: {
          setPriority: editingRule.actions?.setPriority as ValidPriority | undefined,
          setAssignee: editingRule.actions?.setAssignee
        },
        assignTo: editingRule.assignTo,
        isActive: editingRule.isActive
      })
    } else {
      form.reset({
        name: '',
        conditions: {
          keywords: [],
          customFields: {}
        },
        actions: {
          setPriority: undefined,
          setAssignee: undefined
        },
        assignTo: '',
        isActive: true
      })
    }
  }, [editingRule, form])

  const handleSubmit = async (values: FormData) => {
    try {
      const ruleData: Omit<RoutingRule, 'id'> = {
        name: values.name,
        conditions: {
          keywords: values.conditions.keywords || [],
          customFields: values.conditions.customFields || {}
        },
        actions: values.actions ? {
          setPriority: values.actions.setPriority || undefined,
          setAssignee: values.actions.setAssignee === 'no_change' ? undefined : values.actions.setAssignee
        } : undefined,
        assignTo: values.assignTo,
        isActive: values.isActive
      }
      
      if (editingRule?.id) {
        await onUpdateRule(editingRule.id, ruleData)
      } else {
        await onCreateRule(ruleData)
      }
      
      onClose()
    } catch (error) {
      console.error('Error submitting routing rule:', error)
      setError('Failed to save routing rule')
    } finally {
      setIsSubmitting(false)
    }
  }

  const renderAssignedUser = (input: RoutingRule | { assignTo: string; assignToUser?: User }) => {
    // Use the full user object if available
    if (input.assignToUser) {
      return input.assignToUser.username
    }
    // Fallback to looking up by ID
    const user = users.find(u => u.id.toString() === input.assignTo)
    return user ? user.username : 'Unknown user'
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-medium">Ticket Routing Rules</h2>
        <Button onClick={() => {
          setShowAddDialog(true)
        }}>
          Add Rule
        </Button>
      </div>

      <div className="space-y-4">
        {editingRule ? null : (
          <div className="space-y-4">
            {rules?.map((rule) => (
              <div
                key={rule.id}
                className="p-4 border rounded-lg flex justify-between items-center"
              >
                <div className="space-y-2">
                  <h3 className="font-medium">{rule.name}</h3>
                  <div className="text-sm text-gray-500">
                    {rule.conditions?.keywords && rule.conditions.keywords.length > 0 && (
                      <div>Keywords: {rule.conditions.keywords.join(', ')}</div>
                    )}
                    {rule.actions?.setPriority && (
                      <div>Priority: {rule.actions.setPriority}</div>
                    )}
                    {rule.actions?.setAssignee && (
                      <div>Assignee: {users.find(u => u.id.toString() === rule.actions?.setAssignee)?.username || 'Unknown'}</div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setEditingRule(rule);
                      setShowAddDialog(true);
                    }}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => rule.id && onDeleteRule(rule.id)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Dialog open={showAddDialog} onOpenChange={(open) => {
        setShowAddDialog(open)
        if (!open) {
          onClose()
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingRule ? 'Edit Routing Rule' : 'Add Routing Rule'}
            </DialogTitle>
          </DialogHeader>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Rule Name</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="Enter rule name" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="conditions.keywords"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Keywords</FormLabel>
                    <FormControl>
                      <Input 
                        placeholder="Enter keywords separated by commas" 
                        value={field.value?.join(', ') || ''}
                        onChange={(e) => {
                          const keywords = e.target.value.split(',').map(k => k.trim()).filter(Boolean)
                          field.onChange(keywords)
                        }}
                      />
                    </FormControl>
                    <FormDescription>
                      Keywords to match in ticket title and description
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="actions.setPriority"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Set Priority</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select priority to set" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {validPriorities.map((priority) => (
                          <SelectItem key={priority} value={priority}>
                            {priority.charAt(0).toUpperCase() + priority.slice(1)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Priority to set when keywords match
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="actions.setAssignee"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Set Assignee To (optional)</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a user" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="no_change">Don't Change Assignee</SelectItem>
                        {users.map((user) => (
                          <SelectItem key={user.id} value={user.id.toString()}>
                            {user.first_name} {user.last_name} ({user.username})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Set the ticket's assignee when rule matches
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="assignTo"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Assign To</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a user" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {users.map((user) => (
                          <SelectItem key={user.id} value={user.id.toString()}>
                            {user.first_name} {user.last_name} ({user.username})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <DialogFooter className="flex flex-col gap-4">
                {error && (
                  <div className="text-sm text-red-500 font-medium">
                    {error}
                  </div>
                )}
                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowAddDialog(false)
                      onClose()
                      setError(null)
                      form.reset()
                    }}
                    disabled={isSubmitting}
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="submit"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? 'Saving...' : editingRule ? 'Update Rule' : 'Add Rule'}
                  </Button>
                </div>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
