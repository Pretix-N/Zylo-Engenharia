import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { onAuthStateChanged, signOut } from 'firebase/auth'
import { auth } from './firebase'
import { AppProvider } from './context/AppContext'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import Projetos from './pages/Projetos'
import Clientes from './pages/Clientes'
import Equipe from './pages/Equipe'
import Financeiro from './pages/Financeiro'
import Login from './pages/Login'

export default function App() {
  const [user, setUser] = useState(undefined)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => setUser(u))
    return () => unsub()
  }, [])

  if (user === undefined) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0f0f0f]">
        <div className="w-10 h-10 rounded-xl bg-amber-500 flex items-center justify-center animate-pulse">
          <span className="text-black font-black text-lg">Z</span>
        </div>
      </div>
    )
  }

  if (!user) return <Login />

  return (
    <AppProvider>
      <Router>
        <div className="flex h-screen overflow-hidden bg-[#0f0f0f]">
          <Sidebar isOpen={sidebarOpen} />
          <div className="flex flex-col flex-1 overflow-hidden">
            <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} onLogout={() => signOut(auth)} user={user} />
            <main className="flex-1 overflow-y-auto p-6">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/projetos" element={<Projetos />} />
                <Route path="/clientes" element={<Clientes />} />
                <Route path="/equipe" element={<Equipe />} />
                <Route path="/financeiro" element={<Financeiro />} />
              </Routes>
            </main>
          </div>
        </div>
      </Router>
    </AppProvider>
  )
}
