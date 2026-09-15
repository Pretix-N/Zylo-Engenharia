import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { onAuthStateChanged, signOut } from 'firebase/auth'
import { auth } from '../firebase'
import { AppProvider } from '../context/AppContext'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'
import Dashboard from './Dashboard'
import Projetos from './Projetos'
import Clientes from './Clientes'
import Equipe from './Equipe'
import Financeiro from './Financeiro'
import Login from './Login'

export function Carregando() {
  return (
    <div className="flex h-screen items-center justify-center bg-[#0f0f0f]">
      <div className="flex h-10 w-10 animate-pulse items-center justify-center rounded-xl bg-amber-500">
        <span className="text-lg font-black text-black">Z</span>
      </div>
    </div>
  )
}

function Painel({ user }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <AppProvider>
      <div className="flex h-screen overflow-hidden bg-[#0f0f0f]">
        <Sidebar isOpen={sidebarOpen} />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header
            onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
            onLogout={() => signOut(auth)}
            user={user}
          />
          <main className="flex-1 overflow-y-auto p-6">
            <Routes>
              <Route index element={<Dashboard />} />
              <Route path="projetos" element={<Projetos />} />
              <Route path="clientes" element={<Clientes />} />
              <Route path="equipe" element={<Equipe />} />
              <Route path="financeiro" element={<Financeiro />} />
              <Route path="*" element={<Navigate to="/app" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </AppProvider>
  )
}

// Área autenticada. Carregada sob demanda: o site público não baixa
// Firebase Auth, Recharts nem as telas do dashboard.
export default function AreaInterna({ modo }) {
  const [user, setUser] = useState(undefined)

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => setUser(u))
    return () => unsub()
  }, [])

  if (user === undefined) return <Carregando />

  if (modo === 'login') {
    return user ? <Navigate to="/app" replace /> : <Login />
  }

  return user ? <Painel user={user} /> : <Navigate to="/login" replace />
}
