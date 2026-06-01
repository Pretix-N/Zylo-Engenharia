import React, { useState } from 'react'
import { useApp } from '../../context/AppContext'

const empty = { nome: '', tipo: 'Arquitetônico', clienteId: '', responsavelId: '', dataInicio: '', dataPrazo: '', valor: '', status: 'Em Andamento', progresso: 0, descricao: '' }

export default function ProjetoForm({ projeto, onClose }) {
  const { state, dispatch } = useApp()
  const [form, setForm] = useState(projeto || empty)
  const [error, setError] = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  function submit(e) {
    e.preventDefault()
    if (!form.nome || !form.clienteId || !form.responsavelId || !form.dataInicio || !form.dataPrazo || !form.valor) {
      setError('Preencha todos os campos obrigatórios.')
      return
    }
    const payload = { ...form, valor: parseFloat(form.valor), progresso: parseInt(form.progresso) }
    dispatch({ type: projeto ? 'UPDATE_PROJETO' : 'ADD_PROJETO', payload })
    onClose()
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      {error && <p className="text-red-400 text-sm bg-red-400/10 px-3 py-2 rounded-lg">{error}</p>}
      <Field label="Nome do Projeto *"><input className={inp} value={form.nome} onChange={e => set('nome', e.target.value)} placeholder="Ex: Residencial das Flores" /></Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Tipo *">
          <select className={inp} value={form.tipo} onChange={e => set('tipo', e.target.value)}>
            {['Arquitetônico','Estrutural','Hidráulico','Elétrico'].map(t => <option key={t}>{t}</option>)}
          </select>
        </Field>
        <Field label="Status *">
          <select className={inp} value={form.status} onChange={e => set('status', e.target.value)}>
            {['Em Andamento','Concluído','Aguardando Aprovação','Atrasado'].map(s => <option key={s}>{s}</option>)}
          </select>
        </Field>
      </div>
      <Field label="Cliente *">
        <select className={inp} value={form.clienteId} onChange={e => set('clienteId', e.target.value)}>
          <option value="">Selecione um cliente</option>
          {state.clientes.map(c => <option key={c.id} value={c.id}>{c.nome} — {c.empresa}</option>)}
        </select>
      </Field>
      <Field label="Responsável *">
        <select className={inp} value={form.responsavelId} onChange={e => set('responsavelId', e.target.value)}>
          <option value="">Selecione um responsável</option>
          {state.equipe.map(m => <option key={m.id} value={m.id}>{m.nome} — {m.cargo}</option>)}
        </select>
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Data Início *"><input type="date" className={inp} value={form.dataInicio} onChange={e => set('dataInicio', e.target.value)} /></Field>
        <Field label="Prazo *"><input type="date" className={inp} value={form.dataPrazo} onChange={e => set('dataPrazo', e.target.value)} /></Field>
      </div>
      <Field label="Valor do Contrato (R$) *"><input type="number" className={inp} value={form.valor} onChange={e => set('valor', e.target.value)} placeholder="Ex: 250000" min="0" step="1000" /></Field>
      <Field label={`Progresso: ${form.progresso}%`}>
        <input type="range" min="0" max="100" value={form.progresso} onChange={e => set('progresso', e.target.value)}
          className="w-full accent-amber-500" />
      </Field>
      <Field label="Descrição"><textarea className={`${inp} h-20 resize-none`} value={form.descricao} onChange={e => set('descricao', e.target.value)} placeholder="Descreva o projeto..." /></Field>
      <div className="flex gap-3 pt-2">
        <button type="button" onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-[#3a3a3a] text-gray-400 hover:text-white hover:border-[#555] transition-all text-sm font-medium">Cancelar</button>
        <button type="submit" className="flex-1 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-sm transition-all">
          {projeto ? 'Salvar Alterações' : 'Adicionar Projeto'}
        </button>
      </div>
    </form>
  )
}

function Field({ label, children }) {
  return <div><label className="block text-xs font-semibold text-gray-400 mb-1.5">{label}</label>{children}</div>
}

const inp = 'w-full bg-[#222] border border-[#3a3a3a] text-white rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-amber-500 transition-colors placeholder-gray-600'
