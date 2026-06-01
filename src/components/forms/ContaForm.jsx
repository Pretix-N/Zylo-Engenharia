import React, { useState } from 'react'
import { useApp } from '../../context/AppContext'

export default function ContaForm({ conta, tipo, onClose }) {
  const { dispatch } = useApp()
  const isReceber = tipo === 'receber'
  const empty = isReceber
    ? { cliente: '', descricao: '', valor: '', vencimento: '', status: 'Pendente' }
    : { fornecedor: '', descricao: '', valor: '', vencimento: '', status: 'Pendente' }
  const [form, setForm] = useState(conta || empty)
  const [error, setError] = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  function submit(e) {
    e.preventDefault()
    const parteKey = isReceber ? 'cliente' : 'fornecedor'
    if (!form[parteKey] || !form.valor || !form.vencimento) { setError('Preencha todos os campos obrigatórios.'); return }
    const action = conta
      ? (isReceber ? 'UPDATE_CONTA_RECEBER' : 'UPDATE_CONTA_PAGAR')
      : (isReceber ? 'ADD_CONTA_RECEBER' : 'ADD_CONTA_PAGAR')
    dispatch({ type: action, payload: { ...form, valor: parseFloat(form.valor) } })
    onClose()
  }

  const statusOpts = isReceber ? ['Pendente', 'Vencido', 'Recebido'] : ['Pendente', 'Vencido', 'Pago']

  return (
    <form onSubmit={submit} className="space-y-4">
      {error && <p className="text-red-400 text-sm bg-red-400/10 px-3 py-2 rounded-lg">{error}</p>}
      <Field label={isReceber ? 'Cliente *' : 'Fornecedor *'}>
        <input className={inp} value={isReceber ? form.cliente : form.fornecedor}
          onChange={e => set(isReceber ? 'cliente' : 'fornecedor', e.target.value)}
          placeholder={isReceber ? 'Nome do cliente' : 'Nome do fornecedor'} />
      </Field>
      <Field label="Descrição"><input className={inp} value={form.descricao} onChange={e => set('descricao', e.target.value)} placeholder="Descrição do lançamento" /></Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Valor (R$) *"><input type="number" className={inp} value={form.valor} onChange={e => set('valor', e.target.value)} placeholder="0,00" min="0" step="0.01" /></Field>
        <Field label="Vencimento *"><input type="date" className={inp} value={form.vencimento} onChange={e => set('vencimento', e.target.value)} /></Field>
      </div>
      <Field label="Status">
        <select className={inp} value={form.status} onChange={e => set('status', e.target.value)}>
          {statusOpts.map(s => <option key={s}>{s}</option>)}
        </select>
      </Field>
      <div className="flex gap-3 pt-2">
        <button type="button" onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-[#3a3a3a] text-gray-400 hover:text-white transition-all text-sm font-medium">Cancelar</button>
        <button type="submit" className="flex-1 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-sm transition-all">
          {conta ? 'Salvar' : 'Adicionar'}
        </button>
      </div>
    </form>
  )
}

function Field({ label, children }) {
  return <div><label className="block text-xs font-semibold text-gray-400 mb-1.5">{label}</label>{children}</div>
}

const inp = 'w-full bg-[#222] border border-[#3a3a3a] text-white rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-amber-500 transition-colors placeholder-gray-600'
