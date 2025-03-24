import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const response = await fetch(`${apiUrl}/api/scan/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error in scan status route:', error)
    // Return a default status if the backend is not reachable
    return NextResponse.json({
      status: "idle",
      message: "Unable to fetch scan status",
      timestamp: new Date().toISOString(),
      schedule: {
        type: "daily",
        minutes: 0,
        seconds: 0
      }
    }, { status: 200 }) // Return 200 with default data instead of 500
  }
}
