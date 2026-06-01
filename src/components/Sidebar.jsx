import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderKanban,
  Users,
  UserSquare2,
  TrendingUp,
  Building2,
  Zap
} from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/projetos', icon: FolderKanban, label: 'Projetos' },
  { to: '/clientes', icon: UserSquare2, label: 'Clientes' },
  { to: '/equipe', icon: Users, label: 'Equipe' },
  { to: '/financeiro', icon: TrendingUp, label: 'Financeiro' },
]

export default function Sidebar({ isOpen }) {
  return (
    <aside
      className={`
        flex flex-col bg-[#1a1f2e] text-white transition-all duration-300 ease-in-out flex-shrink-0
        ${isOpen ? 'w-64' : 'w-16'}
      `}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/10 min-h-[72px]">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-blue-500 flex-shrink-0">
          <Building2 size={20} className="text-white" />
        </div>
        {isOpen && (
          <div className="overflow-hidden">
            <div className="flex items-center gap-1">
              <span className="font-bold text-lg leading-tight text-white">Zylo</span>
              <Zap size={14} className="text-orange-400 flex-shrink-0" />
            </div>
            <span className="text-xs text-slate-400 font-medium tracking-wider">ENGENHARIA</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {isOpen && (
          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest px-3 pb-2">Menu Principal</p>
        )}
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-150 group
              ${isActive
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                : 'text-slate-400 hover:bg-white/10 hover:text-white'
              }
              ${!isOpen ? 'justify-center' : ''}
              `
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={20} className={`flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'}`} />
                {isOpen && (
                  <span className="font-medium text-sm truncate">{label}</span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      {isOpen && (
        <div className="px-4 py-4 border-t border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-white">ML</span>
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-medium text-white truncate">Mariana Lima</p>
              <p className="text-xs text-slate-400 truncate">Gerente de Projetos</p>
            </div>
          </div>
        </div>
      )}
    </aside>
  )
}
