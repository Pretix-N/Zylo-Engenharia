import React, { useState } from 'react'
import { useApp } from '../context/AppContext'
import Modal from '../components/Modal'
import MembroForm from '../components/forms/MembroForm'
import { Plus, Pencil, Trash2, Mail, Phone, Briefcase } from 'lucide-react'

const espColors = { 'Arquitetura':'text-amber-400 bg-amber-400/10', 'Estrutural':'text-purple-400 bg-purple-400/10', 'Hidráulica':'text-blue-400 bg-blue-400/10', 'Elétrica':'text-yellow-300 bg-yellow-300/10', 'Gestão':'text-green-400 bg-green-400/10', 'Civil':'text-orange-400 bg-orange-400/10', 'Ambiental':'text-teal-400 bg-teal-400/10' }
const avatarBg = ['bg-amber-500','bg-purple-500','bg-blue-500','bg-green-500','bg-red-500','bg-teal-500','bg-pink-500','bg-indigo-500']

export default function Equipe() {
  const { state, dispatch } = useApp()
  const { equipe, projetos } = state
  const [filter, setFilter] = useState('Todos')
  const [modal, setModal] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(null)

  const especialidades = ['Todos', ...new Set(equipe.map(m => m.especialidade))]
  const filtered = filter === 'Todos' ? equipe : equipe.filter(m => m.especialidade === filter)

  const projetosAtivos = (membroId) => projetos.filter(p => p.responsavelId === membroId && p.status === 'Em Andamento').length

  function handleDelete(id) {
    if (confirmDelete === id) { dispatch({ type: 'DELETE_MEMBRO', payload: id }); setConfirmDelete(null) }
    else setConfirmDelete(id)
  }

  return (
    <div className="space-y-5">
      <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-4 flex flex-wrap gap-2 items-center">
        <span className="text-xs font-bold text-gray-600 uppercase tracking-widest mr-1">Filtrar:</span>
        {especialidades.map(e => (
          <button key={e} onClick={() => setFilter(e)} className={`px-3 py-1.5 rounded-xl text-sm font-semibold transition-all ${filter===e?'bg-amber-500 text-black':'bg-[#222] text-gray-500 hover:text-amber-400 border border-[#3a3a3a]'}`}>{e}</button>
        ))}
        <span className="text-sm text-gray-600 ml-2">{filtered.length} membro(s)</span>
        <button onClick={() => setModal('novo')} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-sm transition-all ml-auto">
          <Plus size={15}/> Novo Membro
        </button>
      </div>

      {filtered.length === 0 ? (
        <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-12 text-center">
          <p className="text-gray-600 text-sm">Nenhum membro encontrado.</p>
          <button onClick={() => setModal('novo')} className="mt-3 text-amber-500 text-sm hover:text-amber-400">+ Adicionar membro</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {filtered.map((m, i) => {
            const ativosCount = projetosAtivos(m.id)
            const avatar = m.avatar || m.nome.split(' ').filter(Boolean).slice(0,2).map(n=>n[0].toUpperCase()).join('')
            return (
              <div key={m.id} className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-5 hover:border-[#3a3a3a] transition-all">
                <div className={`w-14 h-14 rounded-2xl ${avatarBg[i%avatarBg.length]} flex items-center justify-center mx-auto mb-3`}>
                  <span className="text-white font-black text-lg">{avatar}</span>
                </div>
                <div className="text-center mb-3">
                  <h3 className="font-bold text-white text-sm">{m.nome}</h3>
                  <p className="text-xs text-gray-500 mt-0.5">{m.cargo}</p>
                  <span className={`inline-flex mt-2 px-2.5 py-1 rounded-full text-xs font-bold ${espColors[m.especialidade]||'text-gray-400 bg-gray-400/10'}`}>{m.especialidade}</span>
                </div>
                <div className="border-t border-[#2a2a2a] pt-3 space-y-1.5 text-xs text-gray-500">
                  <div className="flex items-center gap-1.5"><Mail size={11} className="flex-shrink-0"/><span className="truncate">{m.email}</span></div>
                  {m.telefone && <div className="flex items-center gap-1.5"><Phone size={11}/><span>{m.telefone}</span></div>}
                  <div className="flex items-center gap-1.5"><Briefcase size={11}/><span className="text-amber-500 font-bold">{ativosCount}</span><span>proj. ativos</span></div>
                </div>
                <div className="flex gap-2 mt-3 pt-3 border-t border-[#2a2a2a]">
                  <button onClick={() => setModal(m)} className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg text-xs text-gray-500 hover:text-amber-400 hover:bg-[#1a1a1a] transition-all">
                    <Pencil size={11}/> Editar
                  </button>
                  {confirmDelete === m.id ? (
                    <div className="flex gap-1 flex-1">
                      <button onClick={() => setConfirmDelete(null)} className="flex-1 py-1.5 rounded-lg text-xs text-gray-500 hover:bg-[#1a1a1a]">Cancelar</button>
                      <button onClick={() => handleDelete(m.id)} className="flex-1 py-1.5 rounded-lg text-xs text-red-400 bg-red-400/10 font-bold">OK</button>
                    </div>
                  ) : (
                    <button onClick={() => handleDelete(m.id)} className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg text-xs text-gray-500 hover:text-red-400 hover:bg-[#1a1a1a] transition-all">
                      <Trash2 size={11}/> Excluir
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {modal && (
        <Modal title={modal==='novo'?'Novo Membro':'Editar Membro'} onClose={() => setModal(null)}>
          <MembroForm membro={modal==='novo'?null:modal} onClose={() => setModal(null)} />
        </Modal>
      )}
    </div>
  )
}
