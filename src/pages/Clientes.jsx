import React, { useState } from 'react'
import { clientes, projetos } from '../data/mockData'
import { Search, MapPin, Mail, Phone, FolderKanban, DollarSign } from 'lucide-react'

function formatBRL(value) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(value)
}

export default function Clientes() {
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)

  const filtered = clientes.filter(c =>
    c.nome.toLowerCase().includes(search.toLowerCase()) ||
    c.empresa.toLowerCase().includes(search.toLowerCase()) ||
    c.cidade.toLowerCase().includes(search.toLowerCase())
  )

  const clienteProjetos = selected ? projetos.filter(p => p.cliente === selected.empresa) : []

  return (
    <div className="space-y-5">
      <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100 flex gap-3 items-center">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar cliente, empresa ou cidade..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
        </div>
        <span className="text-sm text-slate-400">{filtered.length} cliente(s)</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map(c => (
          <div
            key={c.id}
            onClick={() => setSelected(c)}
            className="bg-white rounded-xl p-5 shadow-sm border border-slate-100 hover:shadow-md hover:border-blue-200 transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-sm">{c.nome.split(' ').slice(-2).map(n => n[0]).join('').slice(0,2)}</span>
              </div>
              <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${c.status === 'Ativo' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>{c.status}</span>
            </div>
            <h3 className="font-semibold text-slate-800 text-sm">{c.nome}</h3>
            <p className="text-xs text-blue-600 font-medium mb-3">{c.empresa}</p>
            <div className="space-y-1.5 text-xs text-slate-500">
              <div className="flex items-center gap-1.5"><MapPin size={11} /><span>{c.cidade}, {c.estado}</span></div>
              <div className="flex items-center gap-1.5"><Mail size={11} /><span className="truncate">{c.email}</span></div>
              <div className="flex items-center gap-1.5"><Phone size={11} /><span>{c.telefone}</span></div>
            </div>
            <div className="border-t border-slate-100 mt-4 pt-3 flex justify-between text-xs">
              <div className="flex items-center gap-1 text-slate-500"><FolderKanban size={11} /><span>{c.totalProjetos} projetos</span></div>
              <div className="flex items-center gap-1 font-semibold text-slate-700"><DollarSign size={11} /><span>{formatBRL(c.valorTotal)}</span></div>
            </div>
          </div>
        ))}
      </div>

      {/* Modal */}
      {selected && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setSelected(null)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-slate-100">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
                    <span className="text-white font-bold text-lg">{selected.nome.split(' ').slice(-2).map(n => n[0]).join('').slice(0,2)}</span>
                  </div>
                  <div>
                    <h2 className="font-bold text-slate-800 text-lg">{selected.nome}</h2>
                    <p className="text-blue-600 font-medium text-sm">{selected.empresa}</p>
                  </div>
                </div>
                <button onClick={() => setSelected(null)} className="text-slate-400 hover:text-slate-600 text-xl font-bold">×</button>
              </div>
            </div>
            <div className="p-6 space-y-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><p className="text-xs text-slate-400">Localização</p><p className="font-medium">{selected.cidade}, {selected.estado}</p></div>
                <div><p className="text-xs text-slate-400">Status</p><span className={`text-xs font-medium px-2 py-0.5 rounded-full ${selected.status === 'Ativo' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>{selected.status}</span></div>
                <div><p className="text-xs text-slate-400">E-mail</p><p className="font-medium text-sm">{selected.email}</p></div>
                <div><p className="text-xs text-slate-400">Telefone</p><p className="font-medium">{selected.telefone}</p></div>
                <div><p className="text-xs text-slate-400">Total de Projetos</p><p className="font-bold text-xl text-blue-600">{selected.totalProjetos}</p></div>
                <div><p className="text-xs text-slate-400">Valor Total</p><p className="font-bold text-xl text-green-600">{formatBRL(selected.valorTotal)}</p></div>
              </div>
              {clienteProjetos.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Projetos</p>
                  <div className="space-y-2">
                    {clienteProjetos.map(p => (
                      <div key={p.id} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg text-sm">
                        <span className="font-medium text-slate-700 truncate flex-1">{p.nome}</span>
                        <span className={`ml-2 text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${p.status === 'Concluído' ? 'bg-green-100 text-green-700' : p.status === 'Atrasado' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}>{p.status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
