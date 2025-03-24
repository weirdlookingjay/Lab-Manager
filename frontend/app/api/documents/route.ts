import { NextResponse } from 'next/server'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const computer = searchParams.get('computer')
    const page = searchParams.get('page')
    const per_page = searchParams.get('per_page')

    // Forward the original request headers to the backend
    const headers = new Headers(request.headers)
    headers.set('Accept', 'application/json')

    // Get the file stats from the backend
    const response = await fetch(`${API_URL}/api/documents/?computer=${computer}&page=${page}&per_page=${per_page}`, {
      headers
    })

    if (!response.ok) {
      // Forward the error status from the backend
      return NextResponse.json(
        { error: 'Backend request failed' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error in documents API route:', error)
    return NextResponse.json(
      { error: 'Failed to fetch documents' },
      { status: 500 }
    )
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const headers = new Headers(request.headers)
    headers.set('Content-Type', 'application/json')

    const response = await fetch(`${API_URL}/api/documents/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to create document' },
      { status: 500 }
    )
  }
}
