'use client'

import { useState, useEffect } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import * as z from 'zod'
import { Button } from '@/components/ui/button'
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { UserAssignment } from './user-assignment'
import type { Ticket, TicketTemplate, CustomField, RoutingRule, TicketCreateRequest } from '@/app/types/ticket'
import type { User } from '@/app/types/user'
import { formatDateTime } from '@/app/utils/date'
import { getUsers } from '@/app/lib/api/users'
import { applyRoutingRules } from '@/app/lib/api/tickets'

const ticketFormSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().min(1, 'Description is required'),
  priority: z.enum(['low', 'medium', 'high', 'urgent']),
  template: z.string(),  
  custom_fields: z.record(z.any()).optional(),
  assigned_to: z.string().optional(),
})

type TicketFormValues = z.infer<typeof ticketFormSchema>

interface TicketFormProps {
  templates: TicketTemplate[]
  onSubmit: (data: TicketCreateRequest) => void
  initialData?: Partial<Ticket>
  routingRules?: RoutingRule[]
}

export function TicketForm({ templates, onSubmit, initialData, routingRules = [] }: TicketFormProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<TicketTemplate | null>(null)
  const [customFields, setCustomFields] = useState<Record<string, any>>({})
  const [suggestedUsers, setSuggestedUsers] = useState<User[]>([])
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [users, setUsers] = useState<User[]>([])

  useEffect(() => {
    let mounted = true;
    const loadUsers = async () => {
      try {
        const users = await getUsers()
        if (mounted && Array.isArray(users)) {  
          setSuggestedUsers(users)
          setUsers(users)
        }
      } catch (error) {
        console.error('Error loading users:', error)
        if (mounted) {
          setSuggestedUsers([])
          setUsers([])
        }
      }
    }
    loadUsers()
    return () => { mounted = false }
  }, [])

  const form = useForm<TicketFormValues>({
    resolver: zodResolver(ticketFormSchema),
    defaultValues: {
      title: initialData?.title || '',
      description: initialData?.description || '',
      priority: initialData?.priority || 'medium',
      template: '',
      custom_fields: initialData?.custom_fields || {},
      assigned_to: initialData?.assigned_to?.id || undefined,
    },
  })

  const editor = useEditor({
    extensions: [StarterKit],
    content: initialData?.description || '',
    onUpdate: ({ editor }) => {
      form.setValue('description', editor.getHTML())
    },
  })

  useEffect(() => {
    if (form.watch('template')) {
      const template = templates.find(t => t.id === form.watch('template'))
      if (template) {
        setSelectedTemplate(template)
        // Initialize custom fields with default values from template
        const initialCustomFields: Record<string, any> = {}
        Object.entries(template.custom_fields || {}).forEach(([fieldId, field]) => {
          initialCustomFields[fieldId] = field.value || ''
        })
        setCustomFields(initialCustomFields)
        form.setValue('custom_fields', initialCustomFields)

        // Set default priority if specified in template
        if (template.default_priority) {
          form.setValue('priority', template.default_priority)
        }

        // Set default assignee if specified in template
        if (template.default_assignee) {
          form.setValue('assigned_to', template.default_assignee)
        }
      }
    }
  }, [form.watch('template'), templates])

  const handleUserAssign = (user: User | null) => {
    setSelectedUser(user);
    form.setValue('assigned_to', user?.id);
  }

  const handleTemplateChange = async (templateId: string) => {
    const template = templates.find(t => t.id === templateId)
    if (template) {
      setSelectedTemplate(template)
      
      // Set custom fields
      const initialCustomFields: Record<string, any> = {}
      Object.entries(template.custom_fields || {}).forEach(([fieldId, field]) => {
        initialCustomFields[fieldId] = ''  // Initialize with empty string
      })
      setCustomFields(initialCustomFields)
      form.setValue('custom_fields', initialCustomFields)

      // Set default priority if specified in template
      if (template.default_priority) {
        form.setValue('priority', template.default_priority)
      }

      // Set default assignee if specified in template
      if (template.default_assignee) {
        const defaultUser = suggestedUsers.find(u => u.id === template.default_assignee)
        if (defaultUser) {
          setSelectedUser(defaultUser)
          form.setValue('assigned_to', defaultUser.id)
        }
      }
    } else {
      setSelectedTemplate(null)
      setCustomFields({})
      form.setValue('custom_fields', {})
    }
  }

  const handleSubmit = async (values: TicketFormValues) => {
    let assignedUserId = values.assigned_to;
    let priority: "low" | "medium" | "high" | "urgent" = values.priority;

    // Apply routing rules if no assignee is specified
    if (!assignedUserId && routingRules?.length > 0) {
      try {
        // Create a mock ticket object for routing rules
        const mockTicket = {
          id: 'temp-id', // Temporary ID for routing rules
          title: values.title,
          description: values.description,
          priority: values.priority,
          custom_fields: values.custom_fields || {},
        };

        const { assigneeId, updatedPriority } = await applyRoutingRules(mockTicket, routingRules);
        
        if (assigneeId) {
          assignedUserId = assigneeId;
        }
        if (updatedPriority && (updatedPriority === 'low' || updatedPriority === 'medium' || 
            updatedPriority === 'high' || updatedPriority === 'urgent')) {
          priority = updatedPriority;
        }
      } catch (error) {
        console.error('Error applying routing rules:', error);
      }
    }

    onSubmit({
      title: values.title,
      description: values.description,
      priority,
      assigned_to: assignedUserId,
      custom_fields: customFields,
      template: values.template || undefined
    });
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        {initialData && (
          <div className="flex justify-between text-sm text-gray-500">
            <div>Created: {formatDateTime(initialData.created_at)}</div>
          </div>
        )}

        <FormField
          control={form.control}
          name="template"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Template</FormLabel>
              <Select 
                value={field.value || "none"}
                onValueChange={(value) => {
                  const finalValue = value === "none" ? "" : value;
                  field.onChange(finalValue);
                  handleTemplateChange(finalValue);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a template" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No Template</SelectItem>
                  {templates.map((template) => (
                    <SelectItem key={template.id} value={template.id}>
                      {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormDescription>
                Choose a template to pre-fill fields and add custom fields
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Title</FormLabel>
              <FormControl>
                <Input placeholder="Enter ticket title" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description</FormLabel>
              <FormControl>
                <div className="border rounded-md p-4">
                  <div className="border-b pb-2 mb-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => editor?.chain().focus().toggleBold().run()}
                      className={editor?.isActive('bold') ? 'bg-slate-200' : ''}
                    >
                      Bold
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => editor?.chain().focus().toggleItalic().run()}
                      className={editor?.isActive('italic') ? 'bg-slate-200' : ''}
                    >
                      Italic
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => editor?.chain().focus().toggleBulletList().run()}
                      className={editor?.isActive('bulletList') ? 'bg-slate-200' : ''}
                    >
                      Bullet List
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => editor?.chain().focus().toggleOrderedList().run()}
                      className={editor?.isActive('orderedList') ? 'bg-slate-200' : ''}
                    >
                      Numbered List
                    </Button>
                  </div>
                  <EditorContent editor={editor} className="min-h-[200px] prose max-w-none" />
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="priority"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Priority</FormLabel>
              <Select 
                onValueChange={field.onChange}
                defaultValue={field.value}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="space-y-2">
          <FormLabel>Assignee</FormLabel>
          <UserAssignment
            selectedUser={selectedUser}
            onUserSelect={handleUserAssign}
            suggestedUsers={suggestedUsers || []}
          />
        </div>

        {selectedTemplate && Object.entries(selectedTemplate.custom_fields || {}).map(([fieldId, field]) => (
          <FormItem key={fieldId}>
            <FormLabel>{fieldId.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}</FormLabel>
            {field.type === 'text' && (
              <FormControl>
                <Textarea
                  value={customFields[fieldId] || ''}
                  onChange={(e) => {
                    const newFields = { ...customFields, [fieldId]: e.target.value }
                    setCustomFields(newFields)
                    form.setValue('custom_fields', newFields)
                  }}
                  placeholder={field.description}
                />
              </FormControl>
            )}
            {field.type === 'select' && field.options && (
              <Select
                value={customFields[fieldId] || ''}
                onValueChange={(value) => {
                  const newFields = { ...customFields, [fieldId]: value }
                  setCustomFields(newFields)
                  form.setValue('custom_fields', newFields)
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder={field.description || 'Select an option'} />
                </SelectTrigger>
                <SelectContent>
                  {field.options.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {field.type === 'date' && (
              <FormControl>
                <Input
                  type="date"
                  value={customFields[fieldId] || ''}
                  onChange={(e) => {
                    const newFields = { ...customFields, [fieldId]: e.target.value }
                    setCustomFields(newFields)
                    form.setValue('custom_fields', newFields)
                  }}
                />
              </FormControl>
            )}
            {field.type === 'number' && (
              <FormControl>
                <Input
                  type="number"
                  value={customFields[fieldId] || ''}
                  onChange={(e) => {
                    const newFields = { ...customFields, [fieldId]: e.target.value }
                    setCustomFields(newFields)
                    form.setValue('custom_fields', newFields)
                  }}
                  placeholder={field.description}
                />
              </FormControl>
            )}
            {field.description && (
              <FormDescription>{field.description}</FormDescription>
            )}
            {field.required && (
              <FormMessage>This field is required</FormMessage>
            )}
          </FormItem>
        ))}

        <div className="flex justify-end">
          <Button type="submit">Create Ticket</Button>
        </div>
      </form>
    </Form>
  )
}
