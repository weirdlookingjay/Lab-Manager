import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const publicPaths = ['/login', '/api/login']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Allow public paths
  if (publicPaths.some(path => pathname.startsWith(path))) {
    return NextResponse.next()
  }

  // Check for authentication
  const token = request.cookies.get('token')?.value
  const user = request.cookies.get('user')?.value
  
  // If accessing admin routes, verify admin status
  if (pathname.startsWith('/admin')) {
    if (!token || !user) {
      return NextResponse.redirect(new URL('/login', request.url))
    }
    
    try {
      const userData = JSON.parse(user)
      if (!userData.is_staff) {
        return NextResponse.redirect(new URL('/', request.url))
      }
    } catch (error) {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }
  
  // For non-admin routes, just check authentication
  if (!token || !user) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|logo.png).*)',
  ],
}
