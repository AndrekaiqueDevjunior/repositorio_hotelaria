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
    // Verificar sessão via cookies
    const sessionData = request.cookies.get('hotel_session')?.value
    
    if (!sessionData) {
      // Redirecionar para login
      const loginUrl = new URL('/login', request.url)
      loginUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(loginUrl)
    }

    try {
      // Decodificar e validar sessão
      const session = JSON.parse(atob(sessionData))
      
      // Verificar se a sessão é válida
      if (!session.authenticated || !session.timestamp) {
        throw new Error('Sessão inválida')
      }

      // Verificar tempo da sessão (24 horas)
      const sessionAge = Date.now() - session.timestamp
      const maxAge = 24 * 60 * 60 * 1000 // 24 horas
      
      if (sessionAge > maxAge) {
        throw new Error('Sessão expirada')
      }

      // Sessão válida - permitir acesso
      return NextResponse.next()
      
    } catch (error) {
      // Sessão inválida - redirecionar para login
      const loginUrl = new URL('/login', request.url)
      loginUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(loginUrl)
    }
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
