import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// This is a dummy proxy. Person 2 will add Supabase Auth here later.
export function proxy(request: NextRequest) {
  return NextResponse.next()
}