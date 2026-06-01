import React from 'react'
import { useApp } from '../context/AppContext'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { FolderKanban, Clock, DollarSign, Users, AlertTriangle } from 'lucide-react'

const statusColors = { 'Em Andamento': 'text-blue-400 bg-blue-400/10', 'Concluído': 'text-green-400 bg-green-400/10', 'Aguardando Aprovação': 'text-amber-400 bg-amber-400/10', 'Atrasado': 'text-red-400 bg-red-400/10' }
const PIE_COLORS = ['#F59E0B','#10b981','#3b82f6','#8b5cf6']

function fBRL(v) { return new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:0}).format(v) }

export default function Dashboard() {
  const { state } = useApp()
  const { projetos, clientes, financeiro, equipe } = state

  const emAndamento = projetos.filter(p => p.status === 'Em Andamento').length
  const atrasados = projetos.filter(p => p.status === 'Atrasado').length
  const concluidos = projetos.filter(p => p.status === 'Concluído').length
  const clientesAtivos = clientes.filter(c => c.status === 'Ativo').length
  const receitaMes = financeiro.mensal[new Date().getMonth()]?.receita || 0

  const tipos = ['Arquitetônico','Estrutural','Hidráulico','Elétrico']
  const pieData = tipos.map(tipo => ({ name: tipo, value: projetos.filter(p => p.tipo === tipo).length })).filter(d => d.value > 0)

  const recentes = [...projetos].slice(-5).reverse()

  function getCliente(id) { return clientes.find(c => c.id === id) }
  function getMembro(id) { return equipe.find(m => m.id === id) }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KPI icon={FolderKanban} label="Total de Projetos" value={projetos.length} sub={`${concluidos} concluídos`} color="amber" />
        <KPI icon={Clock} label="Em Andamento" value={emAndamento} sub={atrasados > 0 ? `${atrasados} atrasado(s)` : 'Em dia'} color="blue" alert={atrasados > 0} />
        <KPI icon={DollarSign} label="Receita do Mês" value={fBRL(receitaMes)} sub="Mês atual" color="green" />
        <KPI icon={Users} label="Clientes Ativos" value={clientesAtivos} sub={`de ${clientes.length} clientes`} color="purple" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 bg-[#141414] border border-[#2a2a2a] rounded-2xl p-5">
          <h2 className="text-sm font-bold text-white mb-4">Receita vs Despesas (2024)</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={financeiro.mensal} barGap={3}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis dataKey="mes" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} tickFormatter={v => `R$${(v/1000).toFixed(0)}k`} />
              <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 12, color: '#fff' }} formatter={v => fBRL(v)} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#9ca3af' }} />
              <Bar dataKey="receita" name="Receita" fill="#F59E0B" radius={[4,4,0,0]} />
              <Bar dataKey="despesas" name="Despesas" fill="#3b82f6" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-5">
          <h2 className="text-sm font-bold text-white mb-2">Projetos por Tipo</h2>
          {pieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="value">
                    {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 12, color: '#fff' }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1.5">
                {pieData.map((item, i) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }}></span>
                      <span className="text-gray-400">{item.name}</span>
                    </div>
                    <span className="font-bold text-white">{item.value}</span>
                  </div>
                ))}
              </div>
            </>
          ) : <p className="text-gray-600 text-sm text-center py-8">Nenhum projeto cadastrado</p>}
        </div>
      </div>

      <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-[#2a2a2a] flex items-center justify-between">
          <h2 className="text-sm font-bold text-white">Projetos Recentes</h2>
          <span className="text-xs text-gray-600">{concluidos} concluídos · {atrasados} atrasados</span>
        </div>
        {recentes.length === 0 ? (
          <p className="text-gray-600 text-sm text-center py-10">Nenhum projeto cadastrado ainda.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="bg-[#0f0f0f]">
                {['Projeto','Tipo','Cliente','Progresso','Status'].map(h => <th key={h} className="text-left px-5 py-3 text-xs font-bold text-amber-500 uppercase tracking-wider">{h}</th>)}
              </tr></thead>
              <tbody className="divide-y divide-[#1e1e1e]">
                {recentes.map(p => {
                  const cli = getCliente(p.clienteId)
                  return (
                    <tr key={p.id} className="hover:bg-[#1a1a1a] transition-colors">
                      <td className="px-5 py-3.5">
                        <p className="font-semibold text-white text-xs truncate max-w-[160px]">{p.nome}</p>
                        <p className="text-xs text-gray-600">{getMembro(p.responsavelId)?.nome || '—'}</p>
                      </td>
                      <td className="px-4 py-3.5"><TipoBadge tipo={p.tipo} /></td>
                      <td className="px-4 py-3.5 text-gray-400 text-xs">{cli?.empresa || '—'}</td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-[#2a2a2a] rounded-full h-1.5 w-16">
                            <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: `${p.progresso}%` }}></div>
                          </div>
                          <span className="text-xs text-gray-500">{p.progresso}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColors[p.status]}`}>{p.status}</span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function KPI({ icon: Icon, label, value, sub, color, alert }) {
  const c = { amber: 'text-amber-500 bg-amber-500/10', blue: 'text-blue-400 bg-blue-400/10', green: 'text-green-400 bg-green-400/10', purple: 'text-purple-400 bg-purple-400/10' }
  return (
    <div className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 font-medium">{label}</p>
          <p className="text-2xl font-black text-white mt-1">{value}</p>
          <p className="text-xs text-gray-600 mt-1 flex items-center gap-1">
            {alert && <AlertTriangle size={10} className="text-red-400" />}{sub}
          </p>
        </div>
        <div className={`p-2.5 rounded-xl ${c[color]}`}><Icon size={18} /></div>
      </div>
    </div>
  )
}

function TipoBadge({ tipo }) {
  const m = { 'Arquitetônico':'text-amber-400 bg-amber-400/10', 'Estrutural':'text-purple-400 bg-purple-400/10', 'Hidráulico':'text-blue-400 bg-blue-400/10', 'Elétrico':'text-yellow-300 bg-yellow-300/10' }
  return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${m[tipo]||'text-gray-400 bg-gray-400/10'}`}>{tipo}</span>
}
