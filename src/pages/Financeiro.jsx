import React from 'react'
import { financeiro } from '../data/mockData'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts'
import { DollarSign, TrendingUp, TrendingDown, Percent } from 'lucide-react'

function formatBRL(value) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(value)
}

function KPICard({ label, value, icon: Icon, color, sub }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    purple: 'bg-purple-50 text-purple-600',
  }
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-500 font-medium">{label}</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{value}</p>
          {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
        </div>
        <div className={`p-3 rounded-xl ${colors[color]}`}>
          <Icon size={22} />
        </div>
      </div>
    </div>
  )
}

export default function Financeiro() {
  const mensal = financeiro.mensal
  const receitaTotal = mensal.reduce((s, m) => s + m.receita, 0)
  const despesasTotal = mensal.reduce((s, m) => s + m.despesas, 0)
  const lucroTotal = mensal.reduce((s, m) => s + m.lucro, 0)
  const margem = ((lucroTotal / receitaTotal) * 100).toFixed(1)

  const statusColorCR = {
    'Pendente': 'bg-yellow-100 text-yellow-700',
    'Vencido': 'bg-red-100 text-red-700',
    'Pago': 'bg-green-100 text-green-700',
  }

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KPICard label="Receita Total (Ano)" value={formatBRL(receitaTotal)} icon={DollarSign} color="blue" sub="Jan–Dez 2024" />
        <KPICard label="Despesas Total (Ano)" value={formatBRL(despesasTotal)} icon={TrendingDown} color="red" sub="Jan–Dez 2024" />
        <KPICard label="Lucro Líquido" value={formatBRL(lucroTotal)} icon={TrendingUp} color="green" sub="Acumulado 2024" />
        <KPICard label="Margem de Lucro" value={`${margem}%`} icon={Percent} color="purple" sub="Sobre a receita total" />
      </div>

      {/* Area Chart */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
        <h2 className="text-base font-semibold text-slate-700 mb-4">Receita, Despesas e Lucro — 2024</h2>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={mensal}>
            <defs>
              <linearGradient id="gradReceita" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradDespesas" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradLucro" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="mes" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={v => `R$${(v / 1000).toFixed(0)}k`} />
            <Tooltip formatter={(v) => formatBRL(v)} labelStyle={{ color: '#1e293b', fontWeight: 600 }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Area type="monotone" dataKey="receita" name="Receita" stroke="#3b82f6" strokeWidth={2} fill="url(#gradReceita)" />
            <Area type="monotone" dataKey="despesas" name="Despesas" stroke="#f97316" strokeWidth={2} fill="url(#gradDespesas)" />
            <Area type="monotone" dataKey="lucro" name="Lucro" stroke="#10b981" strokeWidth={2} fill="url(#gradLucro)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Bar Chart */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
        <h2 className="text-base font-semibold text-slate-700 mb-4">Comparação Mensal — Receita vs Despesas</h2>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={mensal} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="mes" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={v => `R$${(v / 1000).toFixed(0)}k`} />
            <Tooltip formatter={(v) => formatBRL(v)} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="receita" name="Receita" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="despesas" name="Despesas" fill="#f97316" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Contas Tables */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Contas a Receber */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100">
            <h2 className="text-base font-semibold text-slate-700">Contas a Receber</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Cliente</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Valor</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Vencimento</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {financeiro.contasReceber.map(c => (
                  <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800 text-xs">{c.cliente}</p>
                      <p className="text-xs text-slate-400">{c.descricao}</p>
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-700 text-xs">{formatBRL(c.valor)}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{new Date(c.vencimento).toLocaleDateString('pt-BR')}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColorCR[c.status]}`}>{c.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Contas a Pagar */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100">
            <h2 className="text-base font-semibold text-slate-700">Contas a Pagar</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Fornecedor</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Valor</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Vencimento</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {financeiro.contasPagar.map(c => (
                  <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800 text-xs">{c.fornecedor}</p>
                      <p className="text-xs text-slate-400">{c.descricao}</p>
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-700 text-xs">{formatBRL(c.valor)}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{new Date(c.vencimento).toLocaleDateString('pt-BR')}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${c.status === 'Pago' ? 'bg-green-100 text-green-700' : c.status === 'Vencido' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>{c.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
