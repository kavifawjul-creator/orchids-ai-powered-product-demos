import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/request'
import { createClient } from '@supabase/supabase-js'

export async function middleware(request: NextRequest) {
  const res = NextResponse.next()
  
  // We need to create a supabase client specifically for the middleware
  // because we need to check the session
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )

  // Check if we have a session
  // Note: This is a simplified version. For production, use @supabase/ssr
  const { data: { session } } = await supabase.auth.getSession()

  const url = new URL(request.url)
  
  // Protect dashboard routes
  if (url.pathname.startsWith('/dashboard')) {
    if (!session) {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }

  // Redirect logged in users away from auth pages
  if (url.pathname === '/login' || url.pathname === '/signup') {
    if (session) {
      return NextResponse.redirect(new URL('/dashboard', request.url))
    }
  }

  return res
}

export const config = {
  matcher: ['/dashboard/:path*', '/login', '/signup'],
}
