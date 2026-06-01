import React from 'react'
import { projetos, clientes, financeiro } from '../data/mockData'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { FolderKanban, Clock, DollarSign, Users, TrendingUp, AlertTriangle } from 'lucide-react'

const statusColors = {
  'Em Andamento': 'bg-blue-100 text-blue-700',
  'Concluído': 'bg-green-100 text-green-700',
  'Aguardando Aprovação': 'bg-yellow-100 text-yellow-700',
  'Atrasado': 'bg-red-100 text-red-700',
}

const tipoColors = ['#3b82f6', '#f97316', '#10b981', '#8b5cf6']
const tipos = ['Arquitetônico', 'Estrutural', 'Hidráulico', 'Elétrico']

function formatBRL(value) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(value)
}

export default function Dashboard() {
  const emAndamento = projetos.filter(p => p.status === 'Em Andamento').length
  const concluidos = projetos.filter(p => p.status === 'Concluído').length
  const atrasados = projetos.filter(p => p.status === 'Atrasado').length
  const clientesAtivos = clientes.filter(c => c.status === 'Ativo').length
  const receitaMes = financeiro.mensal[5].receita

  const pieData = tipos.map(tipo => ({
    name: tipo,
    value: projetos.filter(p => p.tipo === tipo).length
  }))

  const barData = financeiro.mensal.slice(0, 8)

  const recentes = [...projetos].sort((a, b) => new Date(b.dataInicio) - new Date(a.dataInicio)).slice(0, 5)

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard icon={FolderKanban} label="Total de Projetos" value={projetos.length} sub="15 projetos cadastrados" color="blue" />
        <StatCard icon={Clock} label="Em Andamento" value={emAndamento} sub={`${atrasados} atrasado(s)`} color="orange" alert={atrasados > 0} />
        <StatCard icon={DollarSign} label="Receita do Mês" value={formatBRL(receitaMes)} sub="Junho 2024" color="green" />
        <StatCard icon={Users} label="Clientes Ativos" value={clientesAtivos} sub={`de ${clientes.length} clientes`} color="purple" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 bg-white rounded-xl p-5 shadow-sm border border-slate-100">
          <h2 className="text-base font-semibold text-slate-700 mb-4">Receita vs Despesas (2024)</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={barData} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="mes" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={v => `R$${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={(v) => formatBRL(v)} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="receita" name="Receita" fill="#3b82f6" radius={[4,4,0,0]} />
              <Bar dataKey="despesas" name="Despesas" fill="#f97316" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
          <h2 className="text-base font-semibold text-slate-700 mb-4">Projetos por Tipo</h2>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value">
                {pieData.map((_, i) => <Cell key={i} fill={tipoColors[i]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-1.5 mt-2">
            {pieData.map((item, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: tipoColors[i] }}></span>
                  <span className="text-slate-600 text-xs">{item.name}</span>
                </div>
                <span className="font-semibold text-slate-700 text-xs">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Projetos Recentes */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-700">Projetos Recentes</h2>
          <span className="text-xs text-slate-400">{concluidos} concluídos · {atrasados} atrasados</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50">
                <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Projeto</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Tipo</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Cliente</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Progresso</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {recentes.map(p => (
                <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="font-medium text-slate-800 truncate max-w-[200px]">{p.nome}</div>
                    <div className="text-xs text-slate-400">{p.responsavel}</div>
                  </td>
                  <td className="px-4 py-3.5"><TipoBadge tipo={p.tipo} /></td>
                  <td className="px-4 py-3.5 text-slate-600 text-xs truncate max-w-[140px]">{p.cliente}</td>
                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-100 rounded-full h-1.5 w-20">
                        <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${p.progresso}%` }}></div>
                      </div>
                      <span className="text-xs text-slate-500 w-8">{p.progresso}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[p.status]}`}>{p.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon: Icon, label, value, sub, color, alert }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    orange: 'bg-orange-50 text-orange-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
  }
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-500 font-medium">{label}</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{value}</p>
          <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
            {alert && <AlertTriangle size={11} className="text-red-400" />}
            {sub}
          </p>
        </div>
        <div className={`p-2.5 rounded-lg ${colors[color]}`}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  )
}

function TipoBadge({ tipo }) {
  const map = {
    'Arquitetônico': 'bg-blue-50 text-blue-600',
    'Estrutural': 'bg-purple-50 text-purple-600',
    'Hidráulico': 'bg-cyan-50 text-cyan-600',
    'Elétrico': 'bg-yellow-50 text-yellow-600',
  }
  return <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${map[tipo] || 'bg-slate-100 text-slate-600'}`}>{tipo}</span>
}
