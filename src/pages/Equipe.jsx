import React, { useState } from 'react'
import { equipe } from '../data/mockData'
import { Mail, Phone, Briefcase } from 'lucide-react'

const especialidadeColors = {
  'Arquitetura': 'bg-blue-100 text-blue-700',
  'Estrutural': 'bg-purple-100 text-purple-700',
  'Hidráulica': 'bg-cyan-100 text-cyan-700',
  'Elétrica': 'bg-yellow-100 text-yellow-700',
  'Gestão': 'bg-green-100 text-green-700',
}

const avatarColors = [
  'from-blue-400 to-blue-600',
  'from-purple-400 to-purple-600',
  'from-cyan-400 to-cyan-600',
  'from-orange-400 to-orange-600',
  'from-pink-400 to-pink-600',
  'from-teal-400 to-teal-600',
  'from-green-400 to-green-600',
  'from-indigo-400 to-indigo-600',
]

export default function Equipe() {
  const [filter, setFilter] = useState('Todos')
  const especialidades = ['Todos', 'Arquitetura', 'Estrutural', 'Hidráulica', 'Elétrica', 'Gestão']

  const filtered = filter === 'Todos' ? equipe : equipe.filter(m => m.especialidade === filter)

  return (
    <div className="space-y-5">
      <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100 flex flex-wrap gap-2 items-center">
        <span className="text-sm font-medium text-slate-600 mr-1">Filtrar por:</span>
        {especialidades.map(e => (
          <button
            key={e}
            onClick={() => setFilter(e)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${filter === e ? 'bg-blue-600 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
          >
            {e}
          </button>
        ))}
        <span className="ml-auto text-sm text-slate-400">{filtered.length} colaborador(es)</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {filtered.map((m, i) => (
          <div key={m.id} className="bg-white rounded-xl p-5 shadow-sm border border-slate-100 hover:shadow-md transition-shadow text-center">
            <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${avatarColors[i % avatarColors.length]} flex items-center justify-center mx-auto mb-3 shadow-lg`}>
              <span className="text-white font-bold text-lg">{m.avatar}</span>
            </div>
            <h3 className="font-semibold text-slate-800 text-sm">{m.nome}</h3>
            <p className="text-xs text-slate-400 mb-2">{m.cargo}</p>
            <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${especialidadeColors[m.especialidade]}`}>{m.especialidade}</span>

            <div className="border-t border-slate-100 mt-4 pt-3 space-y-2 text-left">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Mail size={11} className="flex-shrink-0" />
                <span className="truncate">{m.email}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Phone size={11} className="flex-shrink-0" />
                <span>{m.telefone}</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <Briefcase size={11} className="text-slate-400 flex-shrink-0" />
                <span className="font-semibold text-blue-600">{m.projetosAtivos}</span>
                <span className="text-slate-400">projetos ativos</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
