import React, { useState } from 'react'
import { useApp } from '../context/AppContext'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { TrendingUp, TrendingDown, DollarSign, Percent, Plus, Pencil, Trash2, Settings2 } from 'lucide-react'
import Modal from '../components/Modal'
import ContaForm from '../components/forms/ContaForm'

function fBRL(v) { return new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:0}).format(v) }

const stCR = { 'Pendente':'text-amber-400 bg-amber-400/10', 'Vencido':'text-red-400 bg-red-400/10', 'Recebido':'text-green-400 bg-green-400/10' }
const stCP = { 'Pendente':'text-amber-400 bg-amber-400/10', 'Vencido':'text-red-400 bg-red-400/10', 'Pago':'text-green-400 bg-green-400/10' }

export default function Financeiro() {
  const { state, dispatch } = useApp()
  const { financeiro } = state
  const [modalCR, setModalCR] = useState(null)
  const [modalCP, setModalCP] = useState(null)
  const [confirmDel, setConfirmDel] = useState(null)
  const [editMensal, setEditMensal] = useState(false)
  const [mensalForm, setMensalForm] = useState(null)

  const receitaTotal = financeiro.mensal.reduce((s,m)=>s+m.receita,0)
  const despesasTotal = financeiro.mensal.reduce((s,m)=>s+m.despesas,0)
  const lucroTotal = financeiro.mensal.reduce((s,m)=>s+m.lucro,0)
  const margem = receitaTotal > 0 ? ((lucroTotal/receitaTotal)*100).toFixed(1) : '0.0'

  const ttCR = <div className="flex justify-between items-center"><span>Total:</span><span className="font-black text-amber-400">{fBRL(financeiro.contasReceber.reduce((s,c)=>s+c.valor,0))}</span></div>
  const ttCP = <div className="flex justify-between items-center"><span>Total:</span><span className="font-black text-amber-400">{fBRL(financeiro.contasPagar.reduce((s,c)=>s+c.valor,0))}</span></div>

  function delCR(id) {
    if(confirmDel===`CR-${id}`){dispatch({type:'DELETE_CONTA_RECEBER',payload:id});setConfirmDel(null)}
    else setConfirmDel(`CR-${id}`)
  }
  function delCP(id) {
    if(confirmDel===`CP-${id}`){dispatch({type:'DELETE_CONTA_PAGAR',payload:id});setConfirmDel(null)}
    else setConfirmDel(`CP-${id}`)
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KPI icon={DollarSign} label="Receita Total (Ano)" value={fBRL(receitaTotal)} color="amber" />
        <KPI icon={TrendingDown} label="Despesas Total (Ano)" value={fBRL(despesasTotal)} color="red" />
        <KPI icon={TrendingUp} label="Lucro Líquido" value={fBRL(lucroTotal)} color="green" />
        <KPI icon={Percent} label="Margem de Lucro" value={`${margem}%`} color="purple" />
      </div>

      <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-white">Evolução Financeira 2024</h2>
          <button onClick={() => { setMensalForm(financeiro.mensal.map(m => ({ ...m }))); setEditMensal(true) }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-gray-400 hover:text-amber-400 hover:bg-[#1a1a1a] border border-[#3a3a3a] transition-all">
            <Settings2 size={13} /> Editar valores
          </button>
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={financeiro.mensal}>
            <defs>
              <linearGradient id="gR" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#F59E0B" stopOpacity={0.2}/><stop offset="95%" stopColor="#F59E0B" stopOpacity={0}/></linearGradient>
              <linearGradient id="gL" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/><stop offset="95%" stopColor="#10b981" stopOpacity={0}/></linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
            <XAxis dataKey="mes" tick={{fontSize:11,fill:'#6b7280'}} axisLine={false} tickLine={false} />
            <YAxis tick={{fontSize:10,fill:'#6b7280'}} axisLine={false} tickLine={false} tickFormatter={v=>`R$${(v/1000).toFixed(0)}k`} />
            <Tooltip contentStyle={{background:'#1a1a1a',border:'1px solid #2a2a2a',borderRadius:12,color:'#fff'}} formatter={v=>fBRL(v)} />
            <Legend wrapperStyle={{fontSize:11,color:'#9ca3af'}} />
            <Area type="monotone" dataKey="receita" name="Receita" stroke="#F59E0B" strokeWidth={2} fill="url(#gR)" />
            <Area type="monotone" dataKey="despesas" name="Despesas" stroke="#3b82f6" strokeWidth={2} fill="none" strokeDasharray="5 4" />
            <Area type="monotone" dataKey="lucro" name="Lucro" stroke="#10b981" strokeWidth={2} fill="url(#gL)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-white">Comparação Mensal</h2>
          <button onClick={() => { setMensalForm(financeiro.mensal.map(m => ({ ...m }))); setEditMensal(true) }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-gray-400 hover:text-amber-400 hover:bg-[#1a1a1a] border border-[#3a3a3a] transition-all">
            <Settings2 size={13} /> Editar valores
          </button>
        </div>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={financeiro.mensal} barGap={3}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
            <XAxis dataKey="mes" tick={{fontSize:11,fill:'#6b7280'}} axisLine={false} tickLine={false} />
            <YAxis tick={{fontSize:10,fill:'#6b7280'}} axisLine={false} tickLine={false} tickFormatter={v=>`R$${(v/1000).toFixed(0)}k`} />
            <Tooltip contentStyle={{background:'#1a1a1a',border:'1px solid #2a2a2a',borderRadius:12,color:'#fff'}} formatter={v=>fBRL(v)} />
            <Legend wrapperStyle={{fontSize:11,color:'#9ca3af'}} />
            <Bar dataKey="receita" name="Receita" fill="#F59E0B" radius={[4,4,0,0]} />
            <Bar dataKey="despesas" name="Despesas" fill="#3b82f6" radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <ContaTable title="Contas a Receber" total={ttCR} onAdd={() => setModalCR('novo')}
          items={financeiro.contasReceber.map(c => ({
            id: c.id,
            parte: c.cliente,
            descricao: c.descricao,
            valor: c.valor,
            vencimento: c.vencimento,
            status: c.status,
            statusClass: stCR[c.status],
            onEdit: () => setModalCR(c),
            onDelete: () => delCR(c.id),
            confirmingDelete: confirmDel === `CR-${c.id}`,
            onCancelDelete: () => setConfirmDel(null),
          }))}
        />
        <ContaTable title="Contas a Pagar" total={ttCP} onAdd={() => setModalCP('novo')}
          items={financeiro.contasPagar.map(c => ({
            id: c.id,
            parte: c.fornecedor,
            descricao: c.descricao,
            valor: c.valor,
            vencimento: c.vencimento,
            status: c.status,
            statusClass: stCP[c.status],
            onEdit: () => setModalCP(c),
            onDelete: () => delCP(c.id),
            confirmingDelete: confirmDel === `CP-${c.id}`,
            onCancelDelete: () => setConfirmDel(null),
          }))}
        />
      </div>

      {editMensal && mensalForm && (
        <Modal title="Editar Dados Mensais" onClose={() => setEditMensal(false)}>
          <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
            <div className="grid grid-cols-4 gap-2 text-xs font-bold text-gray-500 uppercase px-1">
              <span>Mês</span><span>Receita (R$)</span><span>Despesas (R$)</span><span>Lucro (R$)</span>
            </div>
            {mensalForm.map((m, i) => (
              <div key={m.mes} className="grid grid-cols-4 gap-2 items-center">
                <span className="text-xs font-bold text-amber-400">{m.mes}</span>
                <input type="number" value={m.receita} min="0"
                  onChange={e => { const f = [...mensalForm]; f[i] = { ...f[i], receita: Number(e.target.value), lucro: Number(e.target.value) - f[i].despesas }; setMensalForm(f) }}
                  className="bg-[#222] border border-[#3a3a3a] text-white rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-amber-500" />
                <input type="number" value={m.despesas} min="0"
                  onChange={e => { const f = [...mensalForm]; f[i] = { ...f[i], despesas: Number(e.target.value), lucro: f[i].receita - Number(e.target.value) }; setMensalForm(f) }}
                  className="bg-[#222] border border-[#3a3a3a] text-white rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-amber-500" />
                <span className={`text-xs font-bold ${m.lucro >= 0 ? 'text-green-400' : 'text-red-400'}`}>{fBRL(m.lucro)}</span>
              </div>
            ))}
          </div>
          <div className="flex gap-3 pt-4 border-t border-[#2a2a2a] mt-2">
            <button type="button" onClick={() => setEditMensal(false)} className="flex-1 py-2.5 rounded-xl border border-[#3a3a3a] text-gray-400 hover:text-white transition-all text-sm font-medium">Cancelar</button>
            <button onClick={() => { dispatch({ type: 'UPDATE_MENSAL', payload: mensalForm }); setEditMensal(false) }}
              className="flex-1 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-sm transition-all">Salvar</button>
          </div>
        </Modal>
      )}
      {modalCR && <Modal title={modalCR==='novo'?'Nova Conta a Receber':'Editar Conta'} onClose={() => setModalCR(null)}>
        <ContaForm conta={modalCR==='novo'?null:modalCR} tipo="receber" onClose={() => setModalCR(null)} />
      </Modal>}
      {modalCP && <Modal title={modalCP==='novo'?'Nova Conta a Pagar':'Editar Conta'} onClose={() => setModalCP(null)}>
        <ContaForm conta={modalCP==='novo'?null:modalCP} tipo="pagar" onClose={() => setModalCP(null)} />
      </Modal>}
    </div>
  )
}

function ContaTable({ title, total, onAdd, items }) {
  return (
    <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl overflow-hidden">
      <div className="px-5 py-4 border-b border-[#2a2a2a] flex items-center justify-between">
        <div><h2 className="text-sm font-bold text-white">{title}</h2><div className="text-xs text-gray-600 mt-0.5">{total}</div></div>
        <button onClick={onAdd} className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs transition-all">
          <Plus size={13}/> Adicionar
        </button>
      </div>
      {items.length === 0 ? <p className="text-gray-600 text-sm text-center py-8">Nenhum lançamento.</p> : (
        <div className="divide-y divide-[#1e1e1e]">
          {items.map(item => (
            <div key={item.id} className="px-5 py-3 hover:bg-[#1a1a1a] transition-colors">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-white text-xs truncate">{item.parte}</p>
                  <p className="text-xs text-gray-600 truncate mt-0.5">{item.descricao}</p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${item.statusClass}`}>{item.status}</span>
                  {item.confirmingDelete ? (
                    <div className="flex gap-1">
                      <button onClick={item.onCancelDelete} className="text-xs text-gray-500 hover:text-white px-2 py-1 rounded-lg hover:bg-[#2a2a2a]">Não</button>
                      <button onClick={item.onDelete} className="text-xs text-red-400 bg-red-400/10 px-2 py-1 rounded-lg font-bold">Sim</button>
                    </div>
                  ) : (
                    <div className="flex gap-1">
                      <button onClick={item.onEdit} className="p-1.5 rounded-lg text-gray-600 hover:text-amber-400 hover:bg-[#2a2a2a] transition-all"><Pencil size={12}/></button>
                      <button onClick={item.onDelete} className="p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-[#2a2a2a] transition-all"><Trash2 size={12}/></button>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-4 mt-1.5">
                <span className="font-bold text-amber-400 text-xs">{fBRL(item.valor)}</span>
                <span className="text-gray-600 text-xs">Venc. {new Date(item.vencimento).toLocaleDateString('pt-BR')}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function KPI({ icon: Icon, label, value, color }) {
  const c = { amber:'text-amber-500 bg-amber-500/10', red:'text-red-400 bg-red-400/10', green:'text-green-400 bg-green-400/10', purple:'text-purple-400 bg-purple-400/10' }
  return (
    <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-5">
      <div className="flex items-center justify-between">
        <div><p className="text-xs text-gray-500 font-medium mb-1">{label}</p><p className="text-xl font-black text-white">{value}</p></div>
        <div className={`p-2.5 rounded-xl ${c[color]}`}><Icon size={18}/></div>
      </div>
    </div>
  )
}
