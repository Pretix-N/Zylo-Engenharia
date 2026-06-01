import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AppProvider } from './context/AppContext'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import Projetos from './pages/Projetos'
import Clientes from './pages/Clientes'
import Equipe from './pages/Equipe'
import Financeiro from './pages/Financeiro'

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  return (
    <AppProvider>
      <Router>
        <div className="flex h-screen overflow-hidden bg-[#0f0f0f]">
          <Sidebar isOpen={sidebarOpen} />
          <div className="flex flex-col flex-1 overflow-hidden">
            <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
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
