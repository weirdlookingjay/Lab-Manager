import { NextResponse } from 'next/server'

export async function POST() {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/scan/start`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Failed to start scan')
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to start scan' },
      { status: 500 }
    )
  }
}
