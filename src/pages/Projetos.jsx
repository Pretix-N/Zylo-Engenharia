import React, { useState } from 'react'
import { useApp } from '../context/AppContext'
import Modal from '../components/Modal'
import ProjetoForm from '../components/forms/ProjetoForm'
import { Search, Filter, Plus, Pencil, Trash2, Calendar, User, DollarSign } from 'lucide-react'

const statusColors = { 'Em Andamento':'text-blue-400 bg-blue-400/10 border-blue-400/20', 'Concluído':'text-green-400 bg-green-400/10 border-green-400/20', 'Aguardando Aprovação':'text-amber-400 bg-amber-400/10 border-amber-400/20', 'Atrasado':'text-red-400 bg-red-400/10 border-red-400/20' }
const tipoBorder = { 'Arquitetônico':'border-t-amber-500', 'Estrutural':'border-t-purple-500', 'Hidráulico':'border-t-blue-500', 'Elétrico':'border-t-yellow-400' }

function fBRL(v) { return new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:0}).format(v) }

export default function Projetos() {
  const { state, dispatch } = useApp()
  const { projetos, clientes, equipe } = state
  const [search, setSearch] = useState('')
  const [filterTipo, setFilterTipo] = useState('Todos')
  const [filterStatus, setFilterStatus] = useState('Todos')
  const [modal, setModal] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(null)

  const getCliente = id => clientes.find(c => c.id === id)
  const getMembro = id => equipe.find(m => m.id === id)

  const filtered = projetos.filter(p => {
    const s = search.toLowerCase()
    const cli = getCliente(p.clienteId)
    return (p.nome.toLowerCase().includes(s) || cli?.empresa?.toLowerCase().includes(s) || s === '')
      && (filterTipo === 'Todos' || p.tipo === filterTipo)
      && (filterStatus === 'Todos' || p.status === filterStatus)
  })

  function handleDelete(id) {
    if (confirmDelete === id) { dispatch({ type: 'DELETE_PROJETO', payload: id }); setConfirmDelete(null) }
    else setConfirmDelete(id)
  }

  return (
    <div className="space-y-5">
      <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-4 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[180px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar projeto ou cliente..."
            className="w-full pl-9 pr-3 py-2 text-sm bg-[#222] border border-[#3a3a3a] text-white rounded-xl focus:outline-none focus:border-amber-500 placeholder-gray-600" />
        </div>
        <div className="flex items-center gap-2">
          <Filter size={14} className="text-gray-600" />
          <select value={filterTipo} onChange={e => setFilterTipo(e.target.value)} className="text-sm bg-[#222] border border-[#3a3a3a] text-white rounded-xl px-3 py-2 focus:outline-none focus:border-amber-500">
            {['Todos','Arquitetônico','Estrutural','Hidráulico','Elétrico'].map(t => <option key={t}>{t}</option>)}
          </select>
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="text-sm bg-[#222] border border-[#3a3a3a] text-white rounded-xl px-3 py-2 focus:outline-none focus:border-amber-500">
            {['Todos','Em Andamento','Concluído','Aguardando Aprovação','Atrasado'].map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
        <span className="text-sm text-gray-600">{filtered.length} projeto(s)</span>
        <button onClick={() => setModal('novo')} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-sm transition-all ml-auto">
          <Plus size={15} /> Novo Projeto
        </button>
      </div>

      {filtered.length === 0 ? (
        <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-12 text-center">
          <p className="text-gray-600 text-sm">Nenhum projeto encontrado.</p>
          <button onClick={() => setModal('novo')} className="mt-3 text-amber-500 text-sm hover:text-amber-400">+ Adicionar primeiro projeto</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(p => {
            const cli = getCliente(p.clienteId)
            const resp = getMembro(p.responsavelId)
            return (
              <div key={p.id} className={`bg-[#141414] border border-[#2a2a2a] border-t-2 ${tipoBorder[p.tipo]||'border-t-gray-600'} rounded-2xl overflow-hidden hover:border-[#3a3a3a] transition-all`}>
                <div className="p-4">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-bold text-white text-sm truncate">{p.nome}</h3>
                      <p className="text-xs text-gray-600 truncate">{cli?.empresa || 'Cliente não encontrado'}</p>
                    </div>
                    <span className={`flex-shrink-0 text-xs px-2 py-0.5 rounded-full border font-medium ${statusColors[p.status]}`}>{p.status}</span>
                  </div>
                  <p className="text-xs text-gray-600 mb-3 line-clamp-2">{p.descricao}</p>
                  <div className="space-y-1.5 text-xs text-gray-500 mb-3">
                    <div className="flex items-center gap-1.5"><User size={11} /><span>{resp?.nome || '—'}</span></div>
                    <div className="flex items-center gap-1.5"><Calendar size={11} /><span>Prazo: {new Date(p.dataPrazo).toLocaleDateString('pt-BR')}</span></div>
                    <div className="flex items-center gap-1.5"><DollarSign size={11} /><span className="font-semibold text-amber-500">{fBRL(p.valor)}</span></div>
                  </div>
                  <div className="mb-3">
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>Progresso</span><span className="font-bold text-white">{p.progresso}%</span>
                    </div>
                    <div className="w-full bg-[#2a2a2a] rounded-full h-1.5">
                      <div className={`h-1.5 rounded-full ${p.progresso===100?'bg-green-500':p.status==='Atrasado'?'bg-red-500':'bg-amber-500'}`} style={{ width:`${p.progresso}%` }}></div>
                    </div>
                  </div>
                  <div className="flex gap-2 pt-2 border-t border-[#2a2a2a]">
                    <button onClick={() => setModal(p)} className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs text-gray-400 hover:text-amber-400 hover:bg-[#1a1a1a] transition-all">
                      <Pencil size={12} /> Editar
                    </button>
                    {confirmDelete === p.id ? (
                      <div className="flex gap-1 flex-1">
                        <button onClick={() => setConfirmDelete(null)} className="flex-1 py-1.5 rounded-lg text-xs text-gray-400 hover:bg-[#1a1a1a] transition-all">Cancelar</button>
                        <button onClick={() => handleDelete(p.id)} className="flex-1 py-1.5 rounded-lg text-xs text-red-400 bg-red-400/10 hover:bg-red-400/20 transition-all font-bold">Confirmar</button>
                      </div>
                    ) : (
                      <button onClick={() => handleDelete(p.id)} className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs text-gray-400 hover:text-red-400 hover:bg-[#1a1a1a] transition-all">
                        <Trash2 size={12} /> Excluir
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {modal && (
        <Modal title={modal === 'novo' ? 'Novo Projeto' : 'Editar Projeto'} onClose={() => setModal(null)}>
          <ProjetoForm projeto={modal === 'novo' ? null : modal} onClose={() => setModal(null)} />
        </Modal>
      )}
    </div>
  )
}
