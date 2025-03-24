import { NextResponse } from 'next/server'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function GET() {
  try {
    const response = await fetch(`${API_URL}/api/computers`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store'
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    
    // Check if the response contains an error
    if (data && data.error) {
      console.error('Server error:', data.error)
      return NextResponse.json([], { status: 200 })
    }

    // Ensure we have an array
    if (!Array.isArray(data)) {
      console.error('Invalid data format received:', data)
      return NextResponse.json([], { status: 200 })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching computers:', error)
    return NextResponse.json([], { status: 200 })
  }
}
