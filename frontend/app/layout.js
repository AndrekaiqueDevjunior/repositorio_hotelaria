import './globals.css'
import Providers from '../components/Providers'
import AccessibilityManager from '../components/AccessibilityPanel'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'

export const dynamic = 'force-dynamic'

export const metadata = {
  title: 'Hotel Real Cabo Frio',
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon.ico',
  },
  description: 'Sistema de Gestão Hoteleira',
}

const enableMobileDebug = process.env.NODE_ENV !== 'production'

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700;800;900&family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet" />
        {enableMobileDebug && (
          <>
            <script src="https://cdn.jsdelivr.net/npm/eruda"></script>
            <script dangerouslySetInnerHTML={{ __html: `
              if (window.location.hostname.includes('ngrok') && window.eruda) {
                window.eruda.init();
                console.log('Eruda Console ativado para debug mobile');
              }
            ` }} />
          </>
        )}
      </head>
      <body>
        <Providers>
          <AccessibilityManager>
            {children}
          </AccessibilityManager>
        </Providers>
        <ToastContainer position="top-right" autoClose={6000} newestOnTop />
      </body>
    </html>
  )
}
