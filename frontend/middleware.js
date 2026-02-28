import { NextResponse } from 'next/server'

export function middleware(request) {
  const { pathname } = request.nextUrl

  // Rotas protegidas
  const protectedRoutes = ['/dashboard', '/admin', '/relatorios', '/configuracoes']
  
  // Verificar se a rota atual precisa de proteção
  const isProtectedRoute = protectedRoutes.some(route => 
    pathname.startsWith(route)
  )

  if (isProtectedRoute) {
    const accessToken = request.cookies.get('hotel_auth_token')?.value
    const refreshToken = request.cookies.get('hotel_auth_token_refresh')?.value

    if (!accessToken && !refreshToken) {
      // Redirecionar para login
      const loginUrl = new URL('/login', request.url)
      loginUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(loginUrl)
    }

    return NextResponse.next()
  }

  // Para rotas não protegidas, permitir acesso
  return NextResponse.next()
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/admin/:path*',
    '/relatorios/:path*',
    '/configuracoes/:path*'
  ]
}
