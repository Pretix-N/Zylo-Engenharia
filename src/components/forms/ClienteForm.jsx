import React, { useState } from 'react'
import { useApp } from '../../context/AppContext'

const empty = { nome: '', empresa: '', email: '', telefone: '', cidade: '', estado: '', status: 'Ativo' }
const estados = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']

export default function ClienteForm({ cliente, onClose }) {
  const { dispatch } = useApp()
  const [form, setForm] = useState(cliente || empty)
  const [error, setError] = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  function submit(e) {
    e.preventDefault()
    if (!form.nome || !form.empresa || !form.email) { setError('Nome, empresa e e-mail são obrigatórios.'); return }
    dispatch({ type: cliente ? 'UPDATE_CLIENTE' : 'ADD_CLIENTE', payload: form })
    onClose()
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      {error && <p className="text-red-400 text-sm bg-red-400/10 px-3 py-2 rounded-lg">{error}</p>}
      <Field label="Nome *"><input className={inp} value={form.nome} onChange={e => set('nome', e.target.value)} placeholder="Nome do contato" /></Field>
      <Field label="Empresa *"><input className={inp} value={form.empresa} onChange={e => set('empresa', e.target.value)} placeholder="Nome da empresa" /></Field>
      <Field label="E-mail *"><input type="email" className={inp} value={form.email} onChange={e => set('email', e.target.value)} placeholder="contato@empresa.com.br" /></Field>
      <Field label="Telefone"><input className={inp} value={form.telefone} onChange={e => set('telefone', e.target.value)} placeholder="(11) 99999-9999" /></Field>
      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2"><Field label="Cidade"><input className={inp} value={form.cidade} onChange={e => set('cidade', e.target.value)} placeholder="São Paulo" /></Field></div>
        <Field label="Estado">
          <select className={inp} value={form.estado} onChange={e => set('estado', e.target.value)}>
            <option value="">UF</option>
            {estados.map(uf => <option key={uf}>{uf}</option>)}
          </select>
        </Field>
      </div>
      <Field label="Status">
        <select className={inp} value={form.status} onChange={e => set('status', e.target.value)}>
          <option>Ativo</option><option>Inativo</option>
        </select>
      </Field>
      <div className="flex gap-3 pt-2">
        <button type="button" onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-[#3a3a3a] text-gray-400 hover:text-white transition-all text-sm font-medium">Cancelar</button>
        <button type="submit" className="flex-1 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-sm transition-all">
          {cliente ? 'Salvar Alterações' : 'Adicionar Cliente'}
        </button>
      </div>
    </form>
  )
}

function Field({ label, children }) {
  return <div><label className="block text-xs font-semibold text-gray-400 mb-1.5">{label}</label>{children}</div>
}

const inp = 'w-full bg-[#222] border border-[#3a3a3a] text-white rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-amber-500 transition-colors placeholder-gray-600'
