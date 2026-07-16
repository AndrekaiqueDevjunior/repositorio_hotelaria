'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { CalendarDays } from 'lucide-react'
import NotificationBell from '../NotificationBell'
import CalendarioReservasModal from '../CalendarioReservasModal'
import { useAuth } from '../../contexts/AuthContext'
import { useTheme } from '../../contexts/ThemeContext'
import { api } from '../../lib/api'

export default function Header({ user, onMenuToggle, isSidebarOpen }) {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const [isCalendarioOpen, setIsCalendarioOpen] = useState(false)
  const router = useRouter()
  const { logout } = useAuth()
  const { theme, toggleTheme } = useTheme()

  const apiBase = api.defaults.baseURL || ''
  const backendOrigin = apiBase.replace(/\/api\/v1\/?$/, '')
  const avatarSrc = user?.fotoUrl
    ? (user.fotoUrl.startsWith('http') ? user.fotoUrl : `${backendOrigin}${user.fotoUrl}`)
    : null

  const handleLogout = () => {
    logout()
  }

  return (
    <header className="header h-16 px-4 lg:px-6">
      <div className="flex items-center justify-between h-full">
        {/* Left Section - Menu Toggle + Welcome */}
        <div className="flex items-center space-x-4">
          {/* Mobile Menu Toggle */}
          <button
            onClick={onMenuToggle}
            className="lg:hidden p-2 rounded-lg text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-neutral-100 dark:hover:bg-neutral-800 transition-colors duration-200"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isSidebarOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
          
          {/* Welcome Message - Hidden on Mobile */}
          <div className="hidden lg:block">
            <h1 className="text-lg font-semibold text-neutral-900 dark:text-white">
              Bem-vindo(a), <span className="text-primary-600">{user?.nome || 'Usuário'}</span>
            </h1>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              {user?.perfil || 'Funcionário'} • {new Date().toLocaleDateString('pt-BR', { weekday: 'long' })}
            </p>
          </div>
        </div>

        {/* Center Section - Calendario de Reservas */}
        <div className="flex flex-1 justify-center mx-4">
          <button
            type="button"
            onClick={() => setIsCalendarioOpen(true)}
            className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary-600 to-primary-700 px-4 py-2 text-sm font-semibold text-white shadow-md transition-all duration-200 hover:shadow-lg hover:brightness-110 active:scale-95"
            title="Abrir calendário de reservas"
          >
            <CalendarDays className="h-4 w-4 transition-transform duration-200 group-hover:scale-110" aria-hidden="true" />
            <span className="hidden sm:inline">Calendário</span>
          </button>
        </div>

        {/* Right Section - Actions */}
        <div className="flex items-center space-x-2">
          {/* Notifications - Componente Melhorado */}
          <NotificationBell />

          {/* Dark Mode Toggle */}
          <button 
            onClick={toggleTheme}
            className="p-2 rounded-lg text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-neutral-100 dark:hover:bg-neutral-800 transition-colors duration-200"
            title={theme === 'dark' ? 'Modo Claro' : 'Modo Escuro'}
          >
            {theme === 'dark' ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center space-x-2 p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors duration-200"
            >
              <div className="w-8 h-8 rounded-full overflow-hidden bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                {avatarSrc ? (
                  <img
                    src={avatarSrc}
                    alt={user?.nome || 'Usuário'}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-primary-600 dark:text-primary-300 text-sm font-medium">
                    {user?.nome?.charAt(0) || 'U'}
                  </span>
                )}
              </div>
              <svg className="hidden md:block w-4 h-4 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Dropdown Menu */}
            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 glass-card shadow-large z-50">
                <div className="p-3 border-b border-neutral-200 dark:border-neutral-700">
                  <p className="text-sm font-medium text-neutral-900 dark:text-white">
                    {user?.nome || 'Usuário'}
                  </p>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400">
                    {user?.email || 'usuario@hotel.com'}
                  </p>
                  <p className="text-xs text-primary-600 dark:text-primary-400 mt-1">
                    {user?.perfil || 'Funcionário'}
                  </p>
                </div>
                <div className="py-2">
                  <button className="w-full text-left px-4 py-2 text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors duration-200">
                    ⚙️ Configurações
                  </button>
                  <button className="w-full text-left px-4 py-2 text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors duration-200">
                    👤 Meu Perfil
                  </button>
                  <button 
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-sm text-danger-600 dark:text-danger-400 hover:bg-danger-50 dark:hover:bg-danger-900/20 transition-colors duration-200"
                  >
                    🚪 Sair
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <CalendarioReservasModal isOpen={isCalendarioOpen} onClose={() => setIsCalendarioOpen(false)} />
    </header>
  )
}