import React from 'react'
import { useLocation } from 'react-router-dom'
import { Menu, Bell, Search } from 'lucide-react'

const titles = {
  '/': 'Dashboard',
  '/projetos': 'Gestão de Projetos',
  '/clientes': 'Clientes e Contratos',
  '/equipe': 'Equipe',
  '/financeiro': 'Financeiro',
}

export default function Header({ onToggleSidebar }) {
  const location = useLocation()
  const title = titles[location.pathname] || 'Dashboard'

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-white border-b border-slate-200 min-h-[72px]">
      <div className="flex items-center gap-4">
        <button onClick={onToggleSidebar} className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors">
          <Menu size={20} />
        </button>
        <div>
          <h1 className="text-xl font-bold text-slate-800">{title}</h1>
          <p className="text-xs text-slate-400">Zylo Engenharia — Sistema de Gestão</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="relative hidden sm:block">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input type="text" placeholder="Buscar..." className="pl-9 pr-4 py-2 text-sm bg-slate-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 w-48" />
        </div>
        <button className="relative p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors">
          <Bell size={20} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-orange-500 rounded-full"></span>
        </button>
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center">
          <span className="text-xs font-bold text-white">ML</span>
        </div>
      </div>
    </header>
  )
}
