'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/app/contexts/AuthContext'
import { useToast } from '@/hooks/use-toast'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { fetchWithAuth } from '@/app/utils/api'
import { useRouter } from 'next/navigation'
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Paperclip } from "lucide-react"
import { PDFSelector } from "@/components/pdf-selector"
import { File } from "lucide-react"
import { X } from "lucide-react"

interface User {
  id: string
  email: string
  username: string
}

interface SelectedPDF {
  id: string;
  file_url: string;
  original_filename: string;
}

const formSchema = z.object({
  type: z.enum(["info", "success", "warning", "error"], {
    required_error: "Please select a notification type.",
  }),
  subject: z.string().min(1, "Subject is required"),
  message: z.string().min(1, "Message is required"),
  userIds: z.array(z.string()).min(1, "Select at least one user"),
  attachments: z.array(z.object({
    id: z.string(),
    file_url: z.string(),
    original_filename: z.string()
  })).optional().default([])
})

export default function AdminEmailPage() {
  const { user, isAuthenticated } = useAuth()
  const router = useRouter()
  const { toast } = useToast()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [sendingTest, setSendingTest] = useState(false)
  const [selectedPDFs, setSelectedPDFs] = useState<SelectedPDF[]>([])

  useEffect(() => {
    // Redirect if not authenticated or not admin
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
    
    if (!user?.is_staff) {
      router.push('/')
      return
    }

    // Fetch users
    const fetchUsers = async () => {
      try {
        const response = await fetchWithAuth('/api/admin/users/')
        console.log('Users response:', response) // Debug log
        setUsers(response) // The API already returns the list of users directly
      } catch (error) {
        console.error('Failed to fetch users:', error)
        toast({
          title: 'Error',
          description: 'Failed to load users',
          variant: 'destructive',
        })
      }
    }

    fetchUsers()
  }, [isAuthenticated, user, router])

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      type: "info",
      subject: "",
      message: "",
      userIds: [],
      attachments: []
    }
  });

  // Debug form state changes
  useEffect(() => {
    const subscription = form.watch((value, { name, type }) => {
      console.log('Form value changed:', { name, type, value });
      console.log('Form state:', { 
        isDirty: form.formState.isDirty,
        isValid: form.formState.isValid,
        errors: form.formState.errors
      });
    });
    return () => subscription.unsubscribe();
  }, [form]);

  const handlePDFSelect = (pdfs: SelectedPDF[]) => {
    console.log('PDFs selected:', pdfs);
    setSelectedPDFs(pdfs);
  }

  const handleRemoveAttachment = (pdfId: string) => {
    setSelectedPDFs(current => current.filter(pdf => pdf.id !== pdfId));
  }

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      // Log form submission attempt
      console.log('Starting form submission...');
      console.log('Form values:', values);
      console.log('Selected PDFs:', selectedPDFs);
      
      // Prevent submission if already loading
      if (loading) {
        console.log('Submission blocked - already loading');
        return;
      }
      
      setLoading(true);
      
      // Prepare request data
      const requestData = {
        subject: values.subject,
        message: values.message,
        type: values.type,
        user_ids: values.userIds,
        attachments: selectedPDFs.map(pdf => pdf.file_url)
      };
      
      console.log('Request data:', requestData);
      
      // Send email
      const response = await fetchWithAuth('/api/notifications/admin/email/send/', {
        method: 'POST',
        body: JSON.stringify(requestData),
      });

      console.log('Server response:', response);

      toast({
        title: "Success",
        description: "Email sent successfully",
      });

      // Reset form and selected PDFs
      form.reset();
      setSelectedPDFs([]);
    } catch (error) {
      console.error('Failed to send email:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send email",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTestEmail = async () => {
    try {
      setSendingTest(true);
      
      const values = form.getValues();
      console.log('Test email values:', values);
      
      // Prepare request data
      const requestData = {
        subject: values.subject || 'Test Email',
        message: values.message || 'This is a test email.',
        type: values.type || 'info',
        user_ids: [user?.id], // Send only to current user
        attachments: selectedPDFs.map(pdf => pdf.file_url)
      };
      
      // Send test email
      const response = await fetchWithAuth('/api/notifications/admin/email/test/', {
        method: 'POST',
        body: JSON.stringify(requestData),
      });

      console.log('Test email response:', response);

      toast({
        title: "Success",
        description: "Test email sent",
      });
    } catch (error) {
      console.error('Failed to send test email:', error);
      toast({
        title: "Error",
        description: "Failed to send test email",
        variant: "destructive",
      });
    } finally {
      setSendingTest(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <Card className="p-6">
        <h1 className="text-2xl font-bold mb-4">Send Email</h1>
        
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Type</label>
            <Select
              value={form.getValues("type")}
              onValueChange={(value) => form.setValue("type", value as any)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="info">Info</SelectItem>
                <SelectItem value="success">Success</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Subject</label>
            <Input
              {...form.register("subject")}
              placeholder="Enter subject"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Message</label>
            <Textarea
              {...form.register("message")}
              placeholder="Enter message"
              rows={4}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Recipients</label>
            <div className="space-y-2">
              {users.map((user) => (
                <div key={user.id} className="flex items-center space-x-2">
                  <Checkbox
                    id={user.id}
                    checked={form.watch("userIds", []).includes(user.id)}
                    onCheckedChange={(checked) => {
                      const currentIds = form.getValues("userIds") || [];
                      const newIds = checked 
                        ? [...currentIds, user.id]
                        : currentIds.filter((id) => id !== user.id);
                      form.setValue("userIds", newIds, { shouldValidate: true, shouldDirty: true });
                    }}
                  />
                  <label
                    htmlFor={user.id}
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                  >
                    {user.email}
                  </label>
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Attachments</label>
            <PDFSelector onSelect={handlePDFSelect} />
            {selectedPDFs.length > 0 && (
              <div className="mt-2 space-y-2">
                {selectedPDFs.map((pdf) => (
                  <div key={pdf.id} className="flex items-center justify-between p-2 bg-accent rounded-lg">
                    <div className="flex items-center space-x-2">
                      <File className="h-4 w-4" />
                      <span className="text-sm">{pdf.original_filename}</span>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 hover:bg-destructive hover:text-destructive-foreground"
                      onClick={() => handleRemoveAttachment(pdf.id)}
                    >
                      <X className="h-4 w-4" />
                      <span className="sr-only">Remove {pdf.original_filename}</span>
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-between">
            <Button
              type="button"
              variant="outline"
              onClick={handleTestEmail}
              disabled={sendingTest}
            >
              {sendingTest ? "Sending..." : "Send Test Email"}
            </Button>
            <Button 
              type="submit"
              disabled={loading}
            >
              {loading ? "Sending..." : "Send Email"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
