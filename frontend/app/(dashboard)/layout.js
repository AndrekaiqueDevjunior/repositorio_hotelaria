'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '../../components/layout/Sidebar'
import Header from '../../components/layout/Header'
import { useAuth } from '../../contexts/AuthContext'
import { ThemeProvider } from '../../contexts/ThemeContext'
import ReservaNotificationManager from '../../components/ReservaNotificationManager'

export default function DashboardLayout({ children }) {
  const router = useRouter()
  const { user, loading, logout, isAuthenticated } = useAuth()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  const authenticated = isAuthenticated()

  useEffect(() => {
    if (!loading && !authenticated) {
      router.push('/login')
    }
  }, [loading, authenticated, router])

  useEffect(() => {
    // Close sidebar when clicking outside on mobile
    const handleOutsideClick = (e) => {
      if (isSidebarOpen && window.innerWidth < 1024) {
        const sidebar = document.getElementById('sidebar')
        if (sidebar && !sidebar.contains(e.target)) {
          setIsSidebarOpen(false)
        }
      }
    }

    // Handle escape key
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isSidebarOpen) {
        setIsSidebarOpen(false)
      }
    }

    // Handle window resize
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setIsSidebarOpen(false)
      }
    }

    if (isSidebarOpen) {
      document.addEventListener('mousedown', handleOutsideClick)
      document.addEventListener('keydown', handleEscape)
      window.addEventListener('resize', handleResize)
    }

    return () => {
      document.removeEventListener('mousedown', handleOutsideClick)
      document.removeEventListener('keydown', handleEscape)
      window.removeEventListener('resize', handleResize)
    }
  }, [isSidebarOpen])

  const handleMenuToggle = () => {
    setIsSidebarOpen(!isSidebarOpen)
  }

  if (!user) {
    return (
      <ThemeProvider>
        <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-900">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-neutral-600 dark:text-neutral-400">Carregando...</p>
          </div>
        </div>
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900">
        {/* Sidebar */}
        <Sidebar 
          id="sidebar"
          user={user} 
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
        />
        
        {/* Main Content */}
        <div className={`lg:ml-64 transition-all duration-300 ${isSidebarOpen ? 'lg:ml-64' : ''}`}>
          <Header 
            user={user}
            onMenuToggle={handleMenuToggle}
            isSidebarOpen={isSidebarOpen}
          />
          
          {/* Page Content */}
          <main className="min-h-[calc(100vh-4rem)]">
            {/* Mobile Padding */}
            <div className="lg:hidden h-2" />
            
            {/* Content Container */}
            <div className="p-4 lg:p-6 xl:p-8 animate-fade-in">
              <ReservaNotificationManager />
              {children}
            </div>
          </main>
        </div>
      </div>
    </ThemeProvider>
  )
}