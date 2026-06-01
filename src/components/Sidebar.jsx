import React from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, FolderKanban, Users, UserSquare2, TrendingUp, Zap } from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/projetos', icon: FolderKanban, label: 'Projetos' },
  { to: '/clientes', icon: UserSquare2, label: 'Clientes' },
  { to: '/equipe', icon: Users, label: 'Equipe' },
  { to: '/financeiro', icon: TrendingUp, label: 'Financeiro' },
]

export default function Sidebar({ isOpen }) {
  return (
    <aside className={`flex flex-col bg-[#0a0a0a] border-r border-[#1e1e1e] transition-all duration-300 ease-in-out flex-shrink-0 ${isOpen ? 'w-60' : 'w-16'}`}>
      <div className="flex items-center gap-3 px-4 py-5 border-b border-[#1e1e1e] min-h-[72px]">
        <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-amber-500 flex-shrink-0">
          <Zap size={18} className="text-black" />
        </div>
        {isOpen && (
          <div>
            <p className="font-black text-lg text-white leading-tight tracking-tight">ZYLO</p>
            <p className="text-[10px] text-amber-500 font-bold tracking-widest">ENGENHARIA</p>
          </div>
        )}
      </div>

      <nav className="flex-1 py-4 px-2 space-y-1">
        {isOpen && <p className="text-[10px] font-bold text-gray-600 uppercase tracking-widest px-3 pb-2">Menu</p>}
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-150
              ${isActive ? 'bg-amber-500 text-black font-bold' : 'text-gray-500 hover:bg-[#1a1a1a] hover:text-amber-400'}
              ${!isOpen ? 'justify-center' : ''}`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={18} className="flex-shrink-0" />
                {isOpen && <span className="text-sm truncate">{label}</span>}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {isOpen && (
        <div className="px-4 py-4 border-t border-[#1e1e1e]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-amber-500 flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-black text-black">Z</span>
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Zylo Engenharia</p>
              <p className="text-xs text-gray-500">Sistema de Gestão</p>
            </div>
          </div>
        </div>
      )}
    </aside>
  )
}
