'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'
import { api, invalidateCache } from '../../lib/api'
import { useAuth } from '../../contexts/AuthContext'

// Definição de menus com controle de acesso por perfil
const menuItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊', roles: ['ADMIN', 'GERENTE', 'RECEPCIONISTA', 'RECEPCAO', 'FUNCIONARIO'] },
  { href: '/reservas', label: 'Reservas', icon: '📅', roles: ['ADMIN', 'GERENTE', 'RECEPCIONISTA', 'RECEPCAO', 'FUNCIONARIO'] },
  { href: '/clientes', label: 'Clientes', icon: '👥', roles: ['ADMIN', 'GERENTE', 'RECEPCIONISTA', 'RECEPCAO'] },
  { href: '/pagamentos', label: 'Pagamentos', icon: '💳', roles: ['ADMIN', 'GERENTE', 'RECEPCIONISTA', 'RECEPCAO'] },
  { href: '/comprovantes', label: 'Comprovantes', icon: '🧾', roles: ['ADMIN', 'GERENTE'] },
  { href: '/auditoria', label: 'Auditoria', icon: '🕵️', roles: ['ADMIN', 'GERENTE'] },
  { href: '/pontos', label: 'Sistema de Pontos', icon: '💎', roles: ['ADMIN', 'GERENTE', 'RECEPCIONISTA', 'RECEPCAO', 'FUNCIONARIO'] },
  { href: '/tarifas', label: 'Tarifas', icon: '💰', roles: ['ADMIN', 'GERENTE'] },
  { href: '/antifraude', label: 'Antifraude', icon: '🛡️', roles: ['ADMIN', 'GERENTE'] },
  { href: '/notificacoes', label: 'Notificações', icon: '🔔', roles: ['ADMIN', 'GERENTE', 'RECEPCIONISTA', 'RECEPCAO', 'FUNCIONARIO'] },
]

export default function Sidebar({ user, isOpen, onClose, ...props }) {
  const pathname = usePathname()
  const { refreshUser } = useAuth()
  const [uploading, setUploading] = useState(false)

  const apiBase = api.defaults.baseURL || ''
  const backendOrigin = apiBase.replace(/\/api\/v1\/?$/, '')
  const avatarSrc = user?.fotoUrl
    ? (user.fotoUrl.startsWith('http') ? user.fotoUrl : `${backendOrigin}${user.fotoUrl}`)
    : null

  const handleAvatarChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      setUploading(true)
      const formData = new FormData()
      formData.append('file', file)
      await api.post('/me/avatar', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      invalidateCache()
      await refreshUser()
    } catch (err) {
      console.error('Erro ao enviar avatar:', err)
      alert('Erro ao enviar foto. Verifique o formato (JPG, PNG, WEBP) e tamanho (máx 5MB).')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  // Filtrar menus baseado no perfil do usuário
  const visibleItems = menuItems.filter(
    (item) => item.roles.includes(user?.perfil)
  )

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div
        {...props}
        className={`fixed top-0 left-0 h-full z-50 flex flex-col w-72 lg:w-64 bg-white dark:bg-neutral-800 border-r border-neutral-200 dark:border-neutral-700 ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'} transform transition-transform duration-300 ease-in-out ${props.className || ''}`}
      >
        {/* Logo Section */}
        <div className="p-6 py-8 border-b border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center justify-center">
            <img
              src="/images/hotel real cabo frio PNG.png"
              alt="Hotel Real Cabo Frio"
              width={336}
              height={140}
              className="w-full h-auto max-w-[336px] object-contain"
            />
          </div>
        </div>
        
        {/* User Profile Section */}
        <div className="p-4 border-b border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-full overflow-hidden bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
              {avatarSrc ? (
                <img
                  src={avatarSrc}
                  alt={user?.nome || 'Usuário'}
                  className="w-full h-full object-cover"
                />
              ) : (
                <span className="text-primary-600 dark:text-primary-300 text-lg font-medium">
                  {user?.nome?.charAt(0) || 'U'}
                </span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-neutral-900 dark:text-white truncate">
                {user?.nome || 'Usuário'}
              </p>
              <p className="text-xs text-neutral-500 dark:text-neutral-400">
                {user?.perfil || 'Funcionário'}
              </p>
            </div>
            <div className="flex-shrink-0">
              <label className={`text-xs px-2 py-1 rounded-md border border-neutral-200 dark:border-neutral-700 cursor-pointer ${uploading ? 'opacity-60 pointer-events-none' : ''}`}>
                {uploading ? 'Enviando...' : 'Foto'}
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  onChange={handleAvatarChange}
                />
              </label>
            </div>
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {visibleItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={`group flex items-center w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-200 ${
                  isActive
                    ? 'bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300'
                    : 'text-neutral-700 dark:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-700/60'
                }`}
              >
                <span className="text-lg mr-3 group-hover:scale-110 transition-transform duration-200">
                  {item.icon}
                </span>
                <span className="truncate">{item.label}</span>
                {isActive && (
                  <div className="ml-auto w-2 h-2 bg-primary-600 rounded-full animate-pulse" />
                )}
              </Link>
            )
          })}
        </nav>
        
        {/* Footer Section */}
        <div className="p-4 border-t border-neutral-200 dark:border-neutral-700">
          <div className="p-3 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white/60 dark:bg-neutral-800/60 backdrop-blur-md">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse" />
              <span className="text-xs text-neutral-600 dark:text-neutral-400">
                Sistema Online
              </span>
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-500 mt-1">
              v2.0.0 Premium
            </p>
          </div>
        </div>
      </div>
    </>
  )
}