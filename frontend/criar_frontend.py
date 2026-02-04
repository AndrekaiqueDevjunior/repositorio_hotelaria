# Salve como: criar_frontend.py
# Execute com: python criar_frontend.py

import os
from pathlib import Path
import json

def criar_frontend_completo():
    """
    Cria o frontend completo em Next.js para o Hotel Real Cabo Frio
    """
    
    base_dir = Path.cwd().parent / "frontend"
    
    print("🚀 Criando Frontend Next.js...")
    print("="*60)
    
    # Criar estrutura de diretórios
    dirs = [
        "app", "app/(auth)/login", "app/(dashboard)/dashboard",
        "app/(dashboard)/clientes", "app/(dashboard)/reservas",
        "components/ui", "components/layout", "lib", "styles", "public"
    ]
    
    for dir_path in dirs:
        (base_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Criar arquivos essenciais
    arquivos = {
        "package.json": json.dumps({
            "name": "hotel-real-cabo-frio",
            "version": "1.0.0",
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start"
            },
            "dependencies": {
                "next": "14.0.4",
                "react": "^18",
                "react-dom": "^18",
                "axios": "^1.6.2",
                "lucide-react": "^0.294.0",
                "tailwindcss": "^3.3.0"
            }
        }, indent=2),
        
        ".env.local": "NEXT_PUBLIC_API_URL=http://localhost:8000",
        
        "tailwind.config.js": """module.exports = {
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'real-blue': '#001C36',
        'real-gold': '#D4AF37',
        'real-white': '#FCFDFF',
        'real-gray': '#F5F7FA'
      }
    }
  },
  plugins: []
}""",

        "next.config.js": """module.exports = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }
}""",

        "styles/globals.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
}""",

        "lib/api.js": """import axios from 'axios';

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});""",

        "app/layout.js": """import '@/styles/globals.css'

export const metadata = {
  title: 'Hotel Real Cabo Frio',
  description: 'Sistema de Gestão Hoteleira',
}

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  )
}""",

        "app/page.js": """'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()
  useEffect(() => {
    router.push('/login')
  }, [])
  return <div>Redirecionando...</div>
}""",

        "app/(auth)/login/page.js": """'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

export default function Login() {
  const router = useRouter()
  const [email, setEmail] = useState('admin@hotelreal.com.br')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')

  const handleLogin = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post('/api/v1/auth/login', { email, password })
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('user', JSON.stringify(res.data.user))
      router.push('/dashboard')
    } catch (err) {
      setError('Credenciais inválidas')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-real-blue">
      <div className="bg-white p-8 rounded-lg shadow-xl w-96">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-real-blue">Hotel Real</h1>
          <p className="text-real-gold">Cabo Frio</p>
        </div>
        <form onSubmit={handleLogin}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-3 border rounded mb-4"
            required
          />
          <input
            type="password"
            placeholder="Senha"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-3 border rounded mb-4"
            required
          />
          {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
          <button
            type="submit"
            className="w-full bg-real-blue text-white p-3 rounded hover:bg-blue-800"
          >
            Entrar
          </button>
        </form>
      </div>
    </div>
  )
}""",

        "app/(dashboard)/layout.js": """'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'

export default function DashboardLayout({ children }) {
  const router = useRouter()
  const [user, setUser] = useState(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')
    if (!token) {
      router.push('/login')
    } else {
      setUser(JSON.parse(userData))
    }
  }, [])

  if (!user) return <div>Carregando...</div>

  return (
    <div className="flex h-screen bg-real-gray">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header user={user} />
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </div>
    </div>
  )
}""",

        "app/(dashboard)/dashboard/page.js": """'use client'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

export default function Dashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    api.get('/api/v1/dashboard/stats').then(res => setStats(res.data))
  }, [])

  if (!stats) return <div>Carregando...</div>

  return (
    <div>
      <h1 className="text-3xl font-bold text-real-blue mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-600 text-sm">Total Clientes</h3>
          <p className="text-3xl font-bold text-real-blue">{stats.total_clientes}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-600 text-sm">Reservas Ativas</h3>
          <p className="text-3xl font-bold text-green-600">{stats.reservas_ativas}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-600 text-sm">Pontos Distribuídos</h3>
          <p className="text-3xl font-bold text-real-gold">{stats.pontos_distribuidos}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-600 text-sm">Operações Pendentes</h3>
          <p className="text-3xl font-bold text-red-600">{stats.operacoes_antifraude_pendentes}</p>
        </div>
      </div>
    </div>
  )
}""",

        "app/(dashboard)/clientes/page.js": """'use client'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

export default function Clientes() {
  const [clientes, setClientes] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    nome_completo: '',
    documento: '',
    telefone: '',
    email: ''
  })

  useEffect(() => {
    loadClientes()
  }, [])

  const loadClientes = async () => {
    const res = await api.get('/api/v1/clientes')
    setClientes(res.data.clientes)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    await api.post('/api/v1/clientes', form)
    loadClientes()
    setShowForm(false)
    setForm({ nome_completo: '', documento: '', telefone: '', email: '' })
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-real-blue">Clientes</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-real-blue text-white px-4 py-2 rounded hover:bg-blue-800"
        >
          Novo Cliente
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
            <input
              placeholder="Nome Completo"
              value={form.nome_completo}
              onChange={(e) => setForm({...form, nome_completo: e.target.value})}
              className="p-2 border rounded"
              required
            />
            <input
              placeholder="Documento"
              value={form.documento}
              onChange={(e) => setForm({...form, documento: e.target.value})}
              className="p-2 border rounded"
              required
            />
            <input
              placeholder="Telefone"
              value={form.telefone}
              onChange={(e) => setForm({...form, telefone: e.target.value})}
              className="p-2 border rounded"
            />
            <input
              type="email"
              placeholder="Email"
              value={form.email}
              onChange={(e) => setForm({...form, email: e.target.value})}
              className="p-2 border rounded"
            />
            <button type="submit" className="col-span-2 bg-real-gold text-real-blue p-2 rounded hover:bg-yellow-500">
              Cadastrar
            </button>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <table className="w-full">
          <thead className="bg-real-blue text-white">
            <tr>
              <th className="p-3 text-left">Nome</th>
              <th className="p-3 text-left">Documento</th>
              <th className="p-3 text-left">Telefone</th>
              <th className="p-3 text-left">Email</th>
            </tr>
          </thead>
          <tbody>
            {clientes.map((cliente) => (
              <tr key={cliente.id} className="border-b">
                <td className="p-3">{cliente.nome_completo}</td>
                <td className="p-3">{cliente.documento}</td>
                <td className="p-3">{cliente.telefone}</td>
                <td className="p-3">{cliente.email}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}""",

        "components/layout/Sidebar.js": """'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const menuItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '🏠' },
  { href: '/clientes', label: 'Clientes', icon: '👥' },
  { href: '/reservas', label: 'Reservas', icon: '📅' },
  { href: '/pontos', label: 'Pontos', icon: '🎁' },
  { href: '/antifraude', label: 'Antifraude', icon: '🛡️' },
]

export default function Sidebar() {
  const pathname = usePathname()
  
  return (
    <div className="w-64 bg-real-blue text-white">
      <div className="p-6">
        <h2 className="text-2xl font-bold">Hotel Real</h2>
        <p className="text-real-gold">Cabo Frio</p>
      </div>
      <nav className="mt-6">
        {menuItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center px-6 py-3 hover:bg-blue-800 ${
              pathname === item.href ? 'bg-blue-800 border-l-4 border-real-gold' : ''
            }`}
          >
            <span className="mr-3">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
    </div>
  )
}""",

        "components/layout/Header.js": """export default function Header({ user }) {
  return (
    <header className="bg-white shadow px-6 py-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl text-gray-800">Bem-vindo, {user?.nome}!</h2>
        <button
          onClick={() => {
            localStorage.clear()
            window.location.href = '/login'
          }}
          className="text-red-600 hover:text-red-800"
        >
          Sair
        </button>
      </div>
    </header>
  )
}"""
    }
    
    # Criar arquivos
    for filepath, content in arquivos.items():
        full_path = base_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Criado: {filepath}")
    
    print("\n✨ Frontend criado com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. cd ../frontend")
    print("2. npm install")
    print("3. npm run dev")
    print("\n🌐 Acesse: http://localhost:3000")

if __name__ == "__main__":
    criar_frontend_completo()