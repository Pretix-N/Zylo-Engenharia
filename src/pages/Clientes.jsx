import React, { useState } from 'react'
import { useApp } from '../context/AppContext'
import Modal from '../components/Modal'
import ClienteForm from '../components/forms/ClienteForm'
import { Search, Plus, Pencil, Trash2, MapPin, Mail, Phone, FolderKanban, DollarSign, X } from 'lucide-react'

function fBRL(v) { return new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:0}).format(v) }

export default function Clientes() {
  const { state, dispatch } = useApp()
  const { clientes, projetos } = state
  const [search, setSearch] = useState('')
  const [modal, setModal] = useState(null)
  const [detail, setDetail] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(null)

  const filtered = clientes.filter(c =>
    c.nome.toLowerCase().includes(search.toLowerCase()) ||
    c.empresa.toLowerCase().includes(search.toLowerCase()) ||
    (c.cidade || '').toLowerCase().includes(search.toLowerCase())
  )

  const getProjetosCliente = (empresa) => projetos.filter(p => {
    const cli = clientes.find(c => c.id === p.clienteId)
    return cli?.empresa === empresa
  })

  const getValorTotal = (empresa) => getProjetosCliente(empresa).reduce((s, p) => s + (p.valor || 0), 0)

  function handleDelete(id) {
    if (confirmDelete === id) { dispatch({ type: 'DELETE_CLIENTE', payload: id }); setConfirmDelete(null); setDetail(null) }
    else setConfirmDelete(id)
  }

  const avatar = (nome) => nome.split(' ').filter(Boolean).slice(0,2).map(n=>n[0].toUpperCase()).join('')

  return (
    <div className="space-y-5">
      <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-4 flex gap-3 items-center">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar cliente ou empresa..."
            className="w-full pl-9 pr-3 py-2 text-sm bg-[#222] border border-[#3a3a3a] text-white rounded-xl focus:outline-none focus:border-amber-500 placeholder-gray-600" />
        </div>
        <span className="text-sm text-gray-600">{filtered.length} cliente(s)</span>
        <button onClick={() => setModal('novo')} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-sm transition-all">
          <Plus size={15} /> Novo Cliente
        </button>
      </div>

      {filtered.length === 0 ? (
        <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-12 text-center">
          <p className="text-gray-600 text-sm">Nenhum cliente encontrado.</p>
          <button onClick={() => setModal('novo')} className="mt-3 text-amber-500 text-sm hover:text-amber-400">+ Adicionar primeiro cliente</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(c => {
            const projsCli = getProjetosCliente(c.empresa)
            return (
              <div key={c.id} onClick={() => setDetail(c)} className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-5 hover:border-amber-500/30 hover:bg-[#1a1a1a] transition-all cursor-pointer">
                <div className="flex items-start justify-between mb-3">
                  <div className="w-11 h-11 rounded-xl bg-amber-500 flex items-center justify-center flex-shrink-0">
                    <span className="text-black font-black text-sm">{avatar(c.nome)}</span>
                  </div>
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${c.status==='Ativo'?'bg-green-400/10 text-green-400':'bg-gray-400/10 text-gray-500'}`}>{c.status}</span>
                </div>
                <h3 className="font-bold text-white text-sm">{c.nome}</h3>
                <p className="text-xs text-amber-500 font-semibold mb-3">{c.empresa}</p>
                <div className="space-y-1.5 text-xs text-gray-500">
                  {c.cidade && <div className="flex items-center gap-1.5"><MapPin size={11}/><span>{c.cidade}{c.estado?`, ${c.estado}`:''}</span></div>}
                  <div className="flex items-center gap-1.5"><Mail size={11}/><span className="truncate">{c.email}</span></div>
                  {c.telefone && <div className="flex items-center gap-1.5"><Phone size={11}/><span>{c.telefone}</span></div>}
                </div>
                <div className="border-t border-[#2a2a2a] mt-3 pt-3 flex justify-between text-xs">
                  <div className="flex items-center gap-1 text-gray-500"><FolderKanban size={11}/><span>{projsCli.length} projetos</span></div>
                  <div className="flex items-center gap-1 text-amber-500 font-bold"><DollarSign size={11}/><span>{fBRL(getValorTotal(c.empresa))}</span></div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Detail Modal */}
      {detail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70" onClick={() => { setDetail(null); setConfirmDelete(null) }}>
          <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl w-full max-w-lg shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#2a2a2a]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500 flex items-center justify-center">
                  <span className="text-black font-black text-sm">{avatar(detail.nome)}</span>
                </div>
                <div><h2 className="font-bold text-white">{detail.nome}</h2><p className="text-xs text-amber-500">{detail.empresa}</p></div>
              </div>
              <button onClick={() => setDetail(null)} className="text-gray-500 hover:text-white p-1"><X size={18}/></button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                {detail.cidade && <div><p className="text-xs text-gray-600 mb-1">Localização</p><p className="text-white font-medium">{detail.cidade}, {detail.estado}</p></div>}
                <div><p className="text-xs text-gray-600 mb-1">Status</p><span className={`text-xs font-bold px-2 py-0.5 rounded-full ${detail.status==='Ativo'?'bg-green-400/10 text-green-400':'bg-gray-400/10 text-gray-500'}`}>{detail.status}</span></div>
                <div className="col-span-2"><p className="text-xs text-gray-600 mb-1">E-mail</p><p className="text-white">{detail.email}</p></div>
                {detail.telefone && <div><p className="text-xs text-gray-600 mb-1">Telefone</p><p className="text-white">{detail.telefone}</p></div>}
              </div>
              {getProjetosCliente(detail.empresa).length > 0 && (
                <div>
                  <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Projetos</p>
                  <div className="space-y-2">
                    {getProjetosCliente(detail.empresa).map(p => (
                      <div key={p.id} className="flex items-center justify-between p-2.5 bg-[#1a1a1a] rounded-xl">
                        <span className="text-white text-xs font-medium truncate flex-1">{p.nome}</span>
                        <span className="ml-2 text-xs px-2 py-0.5 rounded-full text-amber-400 bg-amber-400/10">{p.status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex gap-2 pt-2 border-t border-[#2a2a2a]">
                <button onClick={() => { setModal(detail); setDetail(null) }} className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-sm text-gray-400 hover:text-amber-400 hover:bg-[#1a1a1a] transition-all border border-[#3a3a3a]">
                  <Pencil size={13}/> Editar
                </button>
                {confirmDelete === detail.id ? (
                  <div className="flex gap-2 flex-1">
                    <button onClick={() => setConfirmDelete(null)} className="flex-1 py-2 rounded-xl text-sm text-gray-400 border border-[#3a3a3a] hover:bg-[#1a1a1a] transition-all">Cancelar</button>
                    <button onClick={() => handleDelete(detail.id)} className="flex-1 py-2 rounded-xl text-sm text-red-400 bg-red-400/10 hover:bg-red-400/20 font-bold transition-all">Confirmar</button>
                  </div>
                ) : (
                  <button onClick={() => handleDelete(detail.id)} className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-sm text-gray-400 hover:text-red-400 hover:bg-[#1a1a1a] transition-all border border-[#3a3a3a]">
                    <Trash2 size={13}/> Excluir
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {modal && (
        <Modal title={modal === 'novo' ? 'Novo Cliente' : 'Editar Cliente'} onClose={() => setModal(null)}>
          <ClienteForm cliente={modal === 'novo' ? null : modal} onClose={() => setModal(null)} />
        </Modal>
      )}
    </div>
  )
}
