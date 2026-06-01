import React from 'react'
import { useLocation } from 'react-router-dom'
import { Menu, Bell } from 'lucide-react'

const titles = { '/': 'Dashboard', '/projetos': 'Gestão de Projetos', '/clientes': 'Clientes e Contratos', '/equipe': 'Equipe', '/financeiro': 'Financeiro' }

export default function Header({ onToggleSidebar }) {
  const location = useLocation()
  const title = titles[location.pathname] || 'Dashboard'
  return (
    <header className="flex items-center justify-between px-6 py-4 bg-[#0f0f0f] border-b border-[#1e1e1e] min-h-[72px]">
      <div className="flex items-center gap-4">
        <button onClick={onToggleSidebar} className="p-2 rounded-xl text-gray-500 hover:text-amber-400 hover:bg-[#1a1a1a] transition-colors">
          <Menu size={20} />
        </button>
        <div>
          <h1 className="text-lg font-black text-white">{title}</h1>
          <p className="text-xs text-gray-600">Zylo Engenharia</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button className="relative p-2 rounded-xl text-gray-500 hover:text-amber-400 hover:bg-[#1a1a1a] transition-colors">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-amber-500 rounded-full"></span>
        </button>
        <div className="w-8 h-8 rounded-xl bg-amber-500 flex items-center justify-center">
          <span className="text-xs font-black text-black">Z</span>
        </div>
      </div>
    </header>
  )
}
