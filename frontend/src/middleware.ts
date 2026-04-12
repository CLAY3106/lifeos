import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

const PUBLIC_PATHS = ["/auth/login", "/auth/register"]

export function middleware(request: NextRequest) {
  const token = request.cookies.get("access_token")
  const pathname = request.nextUrl.pathname
  const isPublicPath = PUBLIC_PATHS.some(path => pathname.startsWith(path))

  if (!token && !isPublicPath) {
    return NextResponse.redirect(new URL("/auth/login", request.url))
  }

  if (token && isPublicPath) {
    return NextResponse.redirect(new URL("/dashboard", request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"]
}
