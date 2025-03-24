'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { use } from 'react'
import { getTicket, updateTicket, addComment } from '@/app/lib/api/tickets'
import { getUsers } from '@/app/lib/api/users'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import type { Ticket, TicketActivityLogEntry, TicketComment, TicketPriority, TicketStatus } from '@/app/types/ticket'
import { formatDateTime } from '@/app/utils/date'
import { UserAssignment } from '../components/user-assignment'
import type { User } from '@/app/types/user'
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch"

// Type guard for User object
const isUser = (value: any): value is User => {
  return value && typeof value === 'object' && 'first_name' in value && 'last_name' in value;
};

const formatUserString = (userStr: string | User): string => {
  if (typeof userStr === 'object' && userStr !== null && isUser(userStr)) {
    return `${userStr.first_name} ${userStr.last_name}`;
  }
  try {
    const user = JSON.parse(String(userStr));
    if (isUser(user)) {
      return `${user.first_name} ${user.last_name}`;
    }
  } catch {
    // If parsing fails, return the original string
  }
  return String(userStr);
};

function RichTextEditor({ content, onChange }: { content: string, onChange: (html: string) => void }) {
  const editor = useEditor({
    extensions: [StarterKit],
    content,
    editorProps: {
      attributes: {
        class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl focus:outline-none min-h-[200px] max-w-none',
      },
    },
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
  })

  return (
    <div className="border rounded-md p-4">
      <EditorContent editor={editor} />
    </div>
  )
}

export default function TicketPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editedTitle, setEditedTitle] = useState('')
  const [editedDescription, setEditedDescription] = useState('')
  const [editedPriority, setEditedPriority] = useState<TicketPriority>('medium')
  const [editedAssignedTo, setEditedAssignedTo] = useState<User | null>(null)
  const [newNote, setNewNote] = useState('')
  const [isInternalNote, setIsInternalNote] = useState(false)
  const [newStatus, setNewStatus] = useState<TicketStatus | ''>('')
  const [statusNote, setStatusNote] = useState('')
  const [noteFilter, setNoteFilter] = useState<'all' | 'public' | 'internal'>('all')
  const router = useRouter()

  useEffect(() => {
    const fetchTicket = async () => {
      try {
        const data = await getTicket(resolvedParams.id)
        console.log('Ticket data:', data)
        setTicket(data)
        setEditedTitle(data.title)
        setEditedDescription(data.description)
        setEditedPriority(data.priority as TicketPriority)
        setEditedAssignedTo(data.assigned_to || null)
      } catch (err) {
        setError('Failed to load ticket')
        console.error('Error fetching ticket:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchTicket()
  }, [resolvedParams.id])

  useEffect(() => {
    if (isEditing) {
      const loadUsers = async () => {
        try {
          const users = await getUsers()
          // setSuggestedUsers(users)
        } catch (error) {
          console.error('Error loading users:', error)
        }
      }
      loadUsers()
    }
  }, [isEditing])

  const handleSave = async () => {
    if (!ticket) return

    try {
      const updatedTicket = await updateTicket(ticket.id, {
        title: editedTitle,
        description: editedDescription,
        priority: editedPriority,
        assigned_to: editedAssignedTo?.id || null,
      })
      setTicket(updatedTicket)
      setIsEditing(false)
    } catch (error) {
      console.error('Error updating ticket:', error)
      setError('Failed to update ticket')
    }
  }

  const handlePriorityChange = (value: string) => {
    setEditedPriority(value as TicketPriority)
  }

  const handleAddNote = async () => {
    if (!ticket || !newNote.trim()) return;
    try {
      await addComment(ticket.id, newNote, isInternalNote);
      const updatedTicket = await getTicket(ticket.id);
      setTicket(updatedTicket);
      setNewNote('');
      setIsInternalNote(false);
    } catch (err) {
      console.error('Failed to add note:', err);
    }
  };

  const handleStatusChange = async () => {
    if (!ticket || !newStatus) return;
    try {
      await updateTicket(ticket.id, {
        status: newStatus as TicketStatus,
        statusNote: statusNote,
      });
      const updatedTicket = await getTicket(ticket.id);
      setTicket(updatedTicket);
      setNewStatus('');
      setStatusNote('');
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto py-10">
        <div className="bg-red-50 text-red-500 p-4 rounded-md">
          {error}
        </div>
      </div>
    )
  }

  if (!ticket) {
    return (
      <div className="container mx-auto py-10">
        <div className="bg-yellow-50 text-yellow-500 p-4 rounded-md">
          Ticket not found
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-10">
      {loading ? (
        <div>Loading...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : ticket ? (
        <div className="space-y-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold">{ticket.title}</h1>
              <div className="text-sm text-gray-500">Created {formatDateTime(ticket.created_at)}</div>
            </div>
            <Button onClick={() => setIsEditing(true)}>Edit Ticket</Button>
          </div>

          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div className="space-y-1">
                  <CardTitle>Ticket Details</CardTitle>
                  <CardDescription>Created by {ticket.created_by.first_name} {ticket.created_by.last_name}</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Badge variant={ticket.priority === 'urgent' ? 'destructive' : 'default'}>
                    {ticket.priority}
                  </Badge>
                  <Badge variant="outline">
                    {ticket.status}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm font-medium text-gray-500">Assigned To</div>
                  <div className="mt-1">
                    {ticket.assigned_to ? (
                      <span>{ticket.assigned_to.first_name} {ticket.assigned_to.last_name}</span>
                    ) : (
                      <span className="text-gray-400">Unassigned</span>
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-500">Due Date</div>
                  <div className="mt-1">
                    {ticket.due_date ? formatDateTime(ticket.due_date) : 'Not set'}
                  </div>
                </div>
              </div>

              <div>
                <div className="text-sm font-medium text-gray-500 mb-2">Description</div>
                <div className="prose prose-sm max-w-none bg-gray-50 rounded-lg p-4" dangerouslySetInnerHTML={{ __html: ticket.description }} />
              </div>

              <div className="border-t pt-6">
                <div className="flex gap-2 mb-4">
                  <Button 
                    variant={noteFilter === 'all' ? 'outline' : 'ghost'} 
                    size="sm" 
                    className="gap-2"
                    onClick={() => setNoteFilter('all')}
                  >
                    <span>Comments & Activity</span>
                    <Badge variant="secondary" className="ml-1">
                      {ticket.comments?.length || 0} / {ticket.activity_log?.length || 0}
                    </Badge>
                  </Button>
                  <Button 
                    variant={noteFilter === 'public' ? 'outline' : 'ghost'} 
                    size="sm" 
                    className="gap-2"
                    onClick={() => setNoteFilter('public')}
                  >
                    <span>Public Comments</span>
                    <Badge variant="secondary" className="ml-1">{ticket.comments?.filter(c => !c.is_internal).length || 0}</Badge>
                  </Button>
                  <Button 
                    variant={noteFilter === 'internal' ? 'outline' : 'ghost'} 
                    size="sm" 
                    className="gap-2"
                    onClick={() => setNoteFilter('internal')}
                  >
                    <span>Internal Notes</span>
                    <Badge variant="secondary" className="ml-1">{ticket.comments?.filter(c => c.is_internal).length || 0}</Badge>
                  </Button>
                </div>

                <div className="space-y-6">
                  {[
                    ...(noteFilter === 'all' ? (ticket.activity_log || [])
                      .filter(activity => {
                        console.log('Raw activity:', activity);
                        // Only show activities that are actual changes
                        // Ignore initial status entries and non-changes
                        if (activity.action === 'status_change') {
                          const isRealChange = activity.old_value !== null && activity.old_value !== activity.new_value;
                          console.log('Status change - showing:', isRealChange, {old: activity.old_value, new: activity.new_value});
                          return isRealChange;
                        }
                        const notCreate = activity.action !== 'CREATE';
                        console.log('Non-status change - showing:', notCreate, {action: activity.action});
                        return notCreate;
                      })
                      .map(activity => ({
                        id: activity.id,
                        itemType: 'activity' as const,
                        timestamp: activity.timestamp,
                        content: activity,
                      })) : []),
                    ...(ticket.comments || []).filter(comment => {
                      if (noteFilter === 'all') return true;
                      if (noteFilter === 'public') return !comment.is_internal;
                      return comment.is_internal;
                    }).map(comment => ({
                      id: comment.id,
                      itemType: 'comment' as const,
                      timestamp: comment.created_at,
                      content: comment,
                    }))
                  ]
                    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                    .map((item: ActivityStreamItem, index) => (
                      <div key={item.id || index} className="flex gap-4 group">
                        <div className="w-8 h-8 rounded-full bg-gray-100 flex-shrink-0 flex items-center justify-center">
                          {item.itemType === 'activity' ? (
                            item.content.action === 'status_change' ? '🔄' :
                            item.content.action === 'assignment' ? '👤' :
                            item.content.action === 'priority_change' ? '⚡' :
                            item.content.action === 'tag_change' ? '🏷️' : '📝'
                          ) : item.content.is_internal ? '🔒' : '💬'}
                        </div>
                        <div className="flex-1 space-y-1">
                          {item.itemType === 'activity' ? (
                            <>
                              <div className="text-sm">
                                {(() => {
                                  const activity = item.content;
                                  let actionText = '';
                                  if (activity.action === 'status_change') {
                                    actionText = `Status changed from ${activity.details?.old_value} to ${activity.details?.new_value}`;
                                  } else if (activity.action === 'assignment') {
                                    actionText = `Assigned to ${formatUserString(activity.details?.new_value || '')}`;
                                  } else if (activity.action === 'priority_change') {
                                    actionText = `Priority changed from ${activity.details?.old_value} to ${activity.details?.new_value}`;
                                  }
                                  return actionText;
                                })()}
                              </div>
                              {item.content.note && (
                                <div className="text-sm text-gray-600 bg-gray-50 rounded p-2 mt-1">
                                  {item.content.note}
                                </div>
                              )}
                              <div className="text-xs text-gray-500">
                                by {formatUserString(item.content.user)} • {formatDateTime(item.content.timestamp)}
                              </div>
                            </>
                          ) : (
                            <>
                              <div className="flex items-center gap-2">
                                <span className="font-medium">{item.content.author?.first_name} {item.content.author?.last_name}</span>
                                {item.content.is_internal && (
                                  <Badge variant="secondary" className="text-xs">Internal Note</Badge>
                                )}
                              </div>
                              <div className="text-sm">{item.content.content}</div>
                              <div className="text-xs text-gray-500">
                                {formatDateTime(item.content.created_at)}
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Dialog open={isEditing} onOpenChange={setIsEditing}>
            <DialogContent>
              <DialogTitle>Edit Ticket</DialogTitle>
              <div className="space-y-4">
                <Input
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                  placeholder="Ticket Title"
                />
                <div className="flex gap-4">
                  <Select value={editedPriority} onValueChange={handlePriorityChange}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select Priority" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="urgent">Urgent</SelectItem>
                    </SelectContent>
                  </Select>
                  <UserAssignment
                    selectedUser={editedAssignedTo}
                    onUserSelect={setEditedAssignedTo}
                    suggestedUsers={[]}
                  />
                </div>
                <RichTextEditor
                  content={editedDescription}
                  onChange={setEditedDescription}
                />
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsEditing(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleSave}>Save Changes</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          <div className="border-t pt-6 space-y-4">
            <div className="flex gap-4">
              <div className="flex-1">
                <Select 
                  value={newStatus} 
                  onValueChange={(value: TicketStatus | '') => setNewStatus(value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select new status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="open">Open</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="resolved">Resolved</SelectItem>
                    <SelectItem value="closed">Closed</SelectItem>
                  </SelectContent>
                </Select>
                {newStatus && (
                  <Input
                    className="mt-2"
                    placeholder="Add a note about this status change"
                    value={statusNote}
                    onChange={(e) => setStatusNote(e.target.value)}
                  />
                )}
              </div>
              <Button
                onClick={handleStatusChange}
                disabled={!newStatus}
              >
                Update Status
              </Button>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Switch
                  id="internal-note"
                  checked={isInternalNote}
                  onCheckedChange={setIsInternalNote}
                />
                <label htmlFor="internal-note" className="text-sm text-gray-600">
                  Internal Note
                </label>
              </div>
              <div className="flex gap-4">
                <Input
                  className="flex-1"
                  placeholder="Add a note to this ticket..."
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleAddNote();
                    }
                  }}
                />
                <Button
                  onClick={handleAddNote}
                  disabled={!newNote.trim()}
                >
                  Add Note
                </Button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-yellow-50 text-yellow-500 p-4 rounded-md">
          Ticket not found
        </div>
      )}
    </div>
  )
}

type ActivityStreamItem = {
  id: string;
} & (
  | {
      itemType: 'activity';
      timestamp: string;
      content: TicketActivityLogEntry;
    }
  | {
      itemType: 'comment';
      timestamp: string;
      content: TicketComment;
    }
);
