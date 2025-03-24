'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { TicketForm } from '../components/ticket-form'
import type { Ticket, TicketTemplate, TicketCreateRequest } from '@/app/types/ticket'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { createTicket, getTicketTemplates } from '@/app/lib/api/tickets'

export default function NewTicketPage() {
  const [templates, setTemplates] = useState<TicketTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const data = await getTicketTemplates()
        setTemplates(data)
      } catch (err) {
        setError('Failed to load ticket templates')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchTemplates()
  }, [])

  const handleSubmit = async (data: TicketCreateRequest) => {
    setLoading(true)
    try {
      const ticket = await createTicket(data)
      router.push(`/tickets/${ticket.id}`)
    } catch (error) {
      console.error('Failed to create ticket:', error)
      setError('Failed to create ticket')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto py-10">
      {error && (
        <div className="bg-red-50 text-red-500 p-4 rounded-md mb-4">
          {error}
        </div>
      )}
      <div className="flex justify-between items-center mb-6">
        <Card className="w-full">
          <CardHeader>
            <CardTitle>Create New Ticket</CardTitle>
            <CardDescription>Fill out the form below to create a new ticket</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center items-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
              </div>
            ) : (
              <TicketForm 
                templates={templates || []} 
                onSubmit={handleSubmit} 
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
