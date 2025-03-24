'use client'

import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/app/contexts/AuthContext'
import { useToast } from '@/hooks/use-toast'
import { fetchWithAuth } from '@/app/utils/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Paperclip, X } from 'lucide-react'

interface EmailFormState {
  type: string;
  subject: string;
  message: string;
  attachments: FileList | null;
  recipients: string[];
}

export default function NotificationSettings() {
  const router = useRouter()
  const { user, isAuthenticated } = useAuth()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [testingError, setTestingError] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null)
  const [showAttachDialog, setShowAttachDialog] = useState(false)
  const [currentTestType, setCurrentTestType] = useState<string | null>(null)
  const [preferences, setPreferences] = useState({
    email_enabled: true,
    email_digest: false,
    email_immediate: true,
    notify_scan_errors: true,
    notify_pdf_errors: true,
    notify_computer_offline: true,
    computer_offline_threshold: 10, // 10 minutes default
  })

  useEffect(() => {
    // Redirect if not admin
    if (isAuthenticated && !user?.is_staff) {
      router.push('/')
      return
    }

    // Fetch current preferences
    const fetchPreferences = async () => {
      try {
        const response = await fetchWithAuth('/api/notifications/preferences/')
        setPreferences(response)
      } catch (error) {
        console.error('Failed to fetch preferences:', error)
        toast({
          title: 'Error',
          description: 'Failed to load notification preferences',
          variant: 'destructive',
        })
      }
    }

    if (isAuthenticated && user?.is_staff) {
      fetchPreferences()
    }
  }, [isAuthenticated, user, router])

  const updatePreferences = async (updates: Partial<typeof preferences>) => {
    setLoading(true)
    try {
      const response = await fetchWithAuth('/api/notifications/preferences/', {
        method: 'PUT',
        body: JSON.stringify({ ...preferences, ...updates }),
      })
      setPreferences(response)
      toast({
        title: 'Success',
        description: 'Notification preferences updated',
      })
    } catch (error) {
      console.error('Failed to update preferences:', error)
      toast({
        title: 'Error',
        description: 'Failed to update preferences',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const testErrorNotification = async (errorType: string) => {
    setCurrentTestType(errorType)
    setShowAttachDialog(true)
  }

  const handleSendTest = async () => {
    setTestingError(true)
    try {
      const formData = new FormData()
      formData.append('error_type', currentTestType || 'scan_error')
      
      // Append selected files if any
      if (selectedFiles) {
        Array.from(selectedFiles).forEach((file: File) => {
          formData.append('attachments', file)
        })
      }

      const response = await fetchWithAuth('/api/notifications/test/error/', {
        method: 'POST',
        body: formData,
      })
      toast({
        title: 'Success',
        description: response.message,
      })
      setShowAttachDialog(false)
      setSelectedFiles(null)
    } catch (error: any) {
      console.error('Failed to send test notification:', error)
      toast({
        title: 'Error',
        description: error.message || 'Failed to send test notification',
        variant: 'destructive',
      })
    } finally {
      setTestingError(false)
    }
  }

  const [emailForm, setEmailForm] = useState<EmailFormState>({
    type: 'info',
    subject: '',
    message: '',
    attachments: null,
    recipients: [],
  })

  const defaultEmailForm: EmailFormState = {
    type: 'info',
    subject: '',
    message: '',
    attachments: null,
    recipients: [],
  }

  const [adminUsers, setAdminUsers] = useState([
    { email: 'admin@example.com', isAdmin: true },
    { email: 'test@example.com', isAdmin: false },
  ])

  const [sending, setSending] = useState(false)

  const handleSendEmail = async () => {
    setSending(true)
    try {
      const formData = new FormData()
      formData.append('type', emailForm.type)
      formData.append('subject', emailForm.subject)
      formData.append('message', emailForm.message)
      
      // Append selected files if any
      if (emailForm.attachments) {
        Array.from(emailForm.attachments as FileList).forEach((file) => {
          formData.append('attachments', file)
        })
      }

      formData.append('recipients', JSON.stringify(emailForm.recipients) as string)

      const response = await fetchWithAuth('/api/notifications/send/email/', {
        method: 'POST',
        body: formData,
      })
      toast({
        title: 'Success',
        description: response.message,
      })
      setEmailForm(defaultEmailForm)
    } catch (error: any) {
      console.error('Failed to send email:', error)
      toast({
        title: 'Error',
        description: error.message || 'Failed to send email',
        variant: 'destructive',
      })
    } finally {
      setSending(false)
    }
  }

  if (!isAuthenticated || !user?.is_staff) {
    return null
  }

  return (
    <div className="container mx-auto py-8">
      <Card className="p-6">
        <h1 className="text-2xl font-bold mb-6">Error Notification Settings</h1>
        
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <h3 className="font-medium">Email Notifications</h3>
              <p className="text-sm text-gray-500">Enable or disable email notifications</p>
            </div>
            <Switch
              checked={preferences.email_enabled}
              onCheckedChange={(checked) => updatePreferences({ email_enabled: checked })}
              disabled={loading}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <h3 className="font-medium">Immediate Notifications</h3>
              <p className="text-sm text-gray-500">Send notifications immediately when they occur</p>
            </div>
            <Switch
              checked={preferences.email_immediate}
              onCheckedChange={(checked) => updatePreferences({ email_immediate: checked })}
              disabled={!preferences.email_enabled || loading}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <h3 className="font-medium">Daily Digest</h3>
              <p className="text-sm text-gray-500">Receive a daily digest of notifications</p>
            </div>
            <Switch
              checked={preferences.email_digest}
              onCheckedChange={(checked) => updatePreferences({ email_digest: checked })}
              disabled={!preferences.email_enabled || loading}
            />
          </div>

          <div className="border-t pt-6">
            <h2 className="text-xl font-semibold mb-4">Error Notifications</h2>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">Scanning Errors</h3>
                  <p className="text-sm text-gray-500">Notify when scanning errors occur</p>
                </div>
                <div className="flex items-center space-x-4">
                  <Switch
                    checked={preferences.notify_scan_errors}
                    onCheckedChange={(checked) => updatePreferences({ notify_scan_errors: checked })}
                    disabled={loading || !preferences.email_enabled}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => testErrorNotification('scan_error')}
                    disabled={testingError || !preferences.email_enabled || !preferences.notify_scan_errors}
                  >
                    Test
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">PDF Processing Errors</h3>
                  <p className="text-sm text-gray-500">Notify when PDF processing errors occur</p>
                </div>
                <div className="flex items-center space-x-4">
                  <Switch
                    checked={preferences.notify_pdf_errors}
                    onCheckedChange={(checked) => updatePreferences({ notify_pdf_errors: checked })}
                    disabled={loading || !preferences.email_enabled}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => testErrorNotification('pdf_error')}
                    disabled={testingError || !preferences.email_enabled || !preferences.notify_pdf_errors}
                  >
                    Test
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Computer Offline Notifications</h3>
                    <p className="text-sm text-gray-500">Notify when computers go offline</p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <Switch
                      checked={preferences.notify_computer_offline}
                      onCheckedChange={(checked) => updatePreferences({ notify_computer_offline: checked })}
                      disabled={loading || !preferences.email_enabled}
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => testErrorNotification('computer_offline')}
                      disabled={testingError || !preferences.email_enabled || !preferences.notify_computer_offline}
                    >
                      Test
                    </Button>
                  </div>
                </div>
                
                {preferences.notify_computer_offline && (
                  <div className="ml-6 mt-2">
                    <label className="text-sm font-medium">Offline Threshold (minutes)</label>
                    <div className="flex items-center space-x-2 mt-1">
                      <input
                        type="number"
                        min="1"
                        max="60"
                        value={preferences.computer_offline_threshold}
                        onChange={(e) => updatePreferences({ 
                          computer_offline_threshold: Math.max(1, Math.min(60, parseInt(e.target.value) || 10))
                        })}
                        className="w-20 h-8 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors"
                        disabled={loading || !preferences.email_enabled}
                      />
                      <span className="text-sm text-gray-500">minutes</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Send Admin Email</Label>
                <p className="text-muted-foreground text-sm">Send an email to selected administrators</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Notification Type</Label>
                <select 
                  className="w-full p-2 border rounded-md"
                  value={emailForm.type}
                  onChange={(e) => setEmailForm({...emailForm, type: e.target.value})}
                >
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="error">Error</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label>Subject</Label>
                <Input
                  placeholder="Enter email subject"
                  value={emailForm.subject}
                  onChange={(e) => setEmailForm({...emailForm, subject: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <Label>Message</Label>
                <textarea
                  className="w-full p-2 border rounded-md min-h-[100px]"
                  placeholder="Enter email message"
                  value={emailForm.message}
                  onChange={(e) => setEmailForm({...emailForm, message: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <Label>Attachments</Label>
                <div className="relative">
                  <Input
                    type="file"
                    multiple
                    accept=".pdf"
                    className="hidden"
                    id="file-upload"
                    onChange={(e) => setEmailForm({...emailForm, attachments: e.target.files})}
                  />
                  <label
                    htmlFor="file-upload"
                    className="flex items-center gap-2 w-full px-3 py-2 text-sm border rounded-md hover:bg-gray-50 cursor-pointer"
                  >
                    <Paperclip className="h-4 w-4" />
                    <span className="text-muted-foreground">
                      {emailForm.attachments 
                        ? `${Array.from(emailForm.attachments).length} file(s) selected`
                        : 'Attach PDF files'}
                    </span>
                  </label>
                  {emailForm.attachments && emailForm.attachments.length > 0 && (
                    <div className="mt-2 space-y-2">
                      {Array.from(emailForm.attachments).map((file, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                          <span className="text-sm truncate">{file.name}</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={() => {
                              const dt = new DataTransfer()
                              const files = Array.from(emailForm.attachments!)
                              files.splice(index, 1)
                              files.forEach(file => dt.items.add(file))
                              setEmailForm({...emailForm, attachments: dt.files})
                            }}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  Select one or more PDF files to attach to this email
                </p>
              </div>

              <div className="space-y-2">
                <Label>Recipients</Label>
                <div className="space-y-2">
                  {adminUsers.map((user) => (
                    <div key={user.email} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={user.email}
                        checked={emailForm.recipients.includes(user.email)}
                        onChange={(e) => {
                          const newRecipients = e.target.checked
                            ? [...emailForm.recipients, user.email]
                            : emailForm.recipients.filter(r => r !== user.email)
                          setEmailForm({...emailForm, recipients: newRecipients})
                        }}
                      />
                      <label htmlFor={user.email}>{user.email} ({user.isAdmin ? 'admin' : 'test'})</label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end space-x-2">
                <Button
                  variant="outline"
                  onClick={() => setEmailForm(defaultEmailForm)}
                >
                  Clear
                </Button>
                <Button
                  onClick={handleSendEmail}
                  disabled={sending || !emailForm.subject || !emailForm.message || emailForm.recipients.length === 0}
                >
                  Send Email
                </Button>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Test Notifications</Label>
                <p className="text-muted-foreground text-sm">Test different types of notifications</p>
              </div>
            </div>

            <div className="flex flex-col space-y-4">
              <Button
                onClick={() => testErrorNotification('scan_error')}
                disabled={testingError}
                variant="outline"
              >
                Test Scan Error
              </Button>
              <Button
                onClick={() => testErrorNotification('pdf_error')}
                disabled={testingError}
                variant="outline"
              >
                Test PDF Error
              </Button>
              <Button
                onClick={() => testErrorNotification('computer_offline')}
                disabled={testingError}
                variant="outline"
              >
                Test Computer Offline
              </Button>
            </div>
          </div>

          <Dialog open={showAttachDialog} onOpenChange={setShowAttachDialog}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Send Test Notification</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Attach PDF Files (Optional)</Label>
                  <Input
                    type="file"
                    multiple
                    accept=".pdf"
                    onChange={(e) => setSelectedFiles(e.target.files)}
                  />
                  <p className="text-sm text-muted-foreground">
                    Select one or more PDF files to attach to this notification
                  </p>
                </div>
                <div className="flex justify-end space-x-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowAttachDialog(false)
                      setSelectedFiles(null)
                    }}
                  >
                    Cancel
                  </Button>
                  <Button onClick={handleSendTest} disabled={testingError}>
                    Send Test
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </Card>
    </div>
  )
}
