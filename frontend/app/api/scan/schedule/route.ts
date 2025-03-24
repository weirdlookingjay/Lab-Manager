import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/scan/schedule`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    })
    if (!response.ok) throw new Error('Failed to update scan schedule')
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to update scan schedule' },
      { status: 500 }
    )
  }
}
