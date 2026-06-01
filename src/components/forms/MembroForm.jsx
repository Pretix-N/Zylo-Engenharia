import React, { useState } from 'react'
import { useApp } from '../../context/AppContext'

const empty = { nome: '', cargo: '', especialidade: 'Arquitetura', email: '', telefone: '' }

export default function MembroForm({ membro, onClose }) {
  const { dispatch } = useApp()
  const [form, setForm] = useState(membro || empty)
  const [error, setError] = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  function submit(e) {
    e.preventDefault()
    if (!form.nome || !form.cargo || !form.email) { setError('Nome, cargo e e-mail são obrigatórios.'); return }
    const avatar = form.nome.split(' ').filter(Boolean).slice(0, 2).map(n => n[0].toUpperCase()).join('')
    dispatch({ type: membro ? 'UPDATE_MEMBRO' : 'ADD_MEMBRO', payload: { ...form, avatar } })
    onClose()
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      {error && <p className="text-red-400 text-sm bg-red-400/10 px-3 py-2 rounded-lg">{error}</p>}
      <Field label="Nome Completo *"><input className={inp} value={form.nome} onChange={e => set('nome', e.target.value)} placeholder="Nome do colaborador" /></Field>
      <Field label="Cargo *"><input className={inp} value={form.cargo} onChange={e => set('cargo', e.target.value)} placeholder="Ex: Engenheiro Estrutural Sênior" /></Field>
      <Field label="Especialidade *">
        <select className={inp} value={form.especialidade} onChange={e => set('especialidade', e.target.value)}>
          {['Arquitetura','Estrutural','Hidráulica','Elétrica','Gestão','Civil','Ambiental'].map(s => <option key={s}>{s}</option>)}
        </select>
      </Field>
      <Field label="E-mail *"><input type="email" className={inp} value={form.email} onChange={e => set('email', e.target.value)} placeholder="nome@zylo.com.br" /></Field>
      <Field label="Telefone"><input className={inp} value={form.telefone} onChange={e => set('telefone', e.target.value)} placeholder="(11) 99999-9999" /></Field>
      <div className="flex gap-3 pt-2">
        <button type="button" onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-[#3a3a3a] text-gray-400 hover:text-white transition-all text-sm font-medium">Cancelar</button>
        <button type="submit" className="flex-1 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-sm transition-all">
          {membro ? 'Salvar Alterações' : 'Adicionar Membro'}
        </button>
      </div>
    </form>
  )
}

function Field({ label, children }) {
  return <div><label className="block text-xs font-semibold text-gray-400 mb-1.5">{label}</label>{children}</div>
}

const inp = 'w-full bg-[#222] border border-[#3a3a3a] text-white rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-amber-500 transition-colors placeholder-gray-600'
