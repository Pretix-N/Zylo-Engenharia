import React, { useState } from 'react'
import { projetos } from '../data/mockData'
import { Search, Filter, Calendar, User, TrendingUp } from 'lucide-react'

const statusColors = {
  'Em Andamento': 'bg-blue-100 text-blue-700 border-blue-200',
  'Concluído': 'bg-green-100 text-green-700 border-green-200',
  'Aguardando Aprovação': 'bg-yellow-100 text-yellow-700 border-yellow-200',
  'Atrasado': 'bg-red-100 text-red-700 border-red-200',
}

const tipoBg = {
  'Arquitetônico': 'bg-blue-500',
  'Estrutural': 'bg-purple-500',
  'Hidráulico': 'bg-cyan-500',
  'Elétrico': 'bg-yellow-500',
}

function formatBRL(value) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(value)
}

export default function Projetos() {
  const [search, setSearch] = useState('')
  const [filterTipo, setFilterTipo] = useState('Todos')
  const [filterStatus, setFilterStatus] = useState('Todos')

  const tipos = ['Todos', 'Arquitetônico', 'Estrutural', 'Hidráulico', 'Elétrico']
  const statuses = ['Todos', 'Em Andamento', 'Concluído', 'Aguardando Aprovação', 'Atrasado']

  const filtered = projetos.filter(p => {
    const matchSearch = p.nome.toLowerCase().includes(search.toLowerCase()) || p.cliente.toLowerCase().includes(search.toLowerCase())
    const matchTipo = filterTipo === 'Todos' || p.tipo === filterTipo
    const matchStatus = filterStatus === 'Todos' || p.status === filterStatus
    return matchSearch && matchTipo && matchStatus
  })

  return (
    <div className="space-y-5">
      {/* Filters */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[180px]">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar projeto ou cliente..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter size={15} className="text-slate-400" />
          <select value={filterTipo} onChange={e => setFilterTipo(e.target.value)} className="text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white">
            {tipos.map(t => <option key={t}>{t}</option>)}
          </select>
        </div>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white">
          {statuses.map(s => <option key={s}>{s}</option>)}
        </select>
        <span className="text-sm text-slate-400 ml-auto">{filtered.length} projeto(s)</span>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map(p => (
          <div key={p.id} className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden hover:shadow-md transition-shadow">
            <div className={`h-1.5 ${tipoBg[p.tipo] || 'bg-slate-400'}`}></div>
            <div className="p-4">
              <div className="flex items-start justify-between gap-2 mb-3">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-slate-800 text-sm leading-tight truncate">{p.nome}</h3>
                  <p className="text-xs text-slate-400 mt-0.5 truncate">{p.cliente}</p>
                </div>
                <span className={`inline-flex flex-shrink-0 px-2 py-0.5 rounded-full text-xs font-medium border ${statusColors[p.status]}`}>{p.status}</span>
              </div>

              <p className="text-xs text-slate-500 mb-3 line-clamp-2">{p.descricao}</p>

              <div className="space-y-2 text-xs text-slate-500 mb-3">
                <div className="flex items-center gap-1.5">
                  <User size={12} />
                  <span>{p.responsavel}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Calendar size={12} />
                  <span>Prazo: {new Date(p.dataPrazo).toLocaleDateString('pt-BR')}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <TrendingUp size={12} />
                  <span className="font-semibold text-slate-700">{formatBRL(p.valor)}</span>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-500 mb-1">
                  <span>Progresso</span>
                  <span className="font-medium">{p.progresso}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${p.progresso === 100 ? 'bg-green-500' : p.status === 'Atrasado' ? 'bg-red-500' : 'bg-blue-500'}`}
                    style={{ width: `${p.progresso}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="bg-white rounded-xl p-12 text-center shadow-sm border border-slate-100">
          <p className="text-slate-400">Nenhum projeto encontrado com os filtros selecionados.</p>
        </div>
      )}
    </div>
  )
}
