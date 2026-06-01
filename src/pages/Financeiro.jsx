import React from 'react'
import { financeiro } from '../data/mockData'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { TrendingUp, TrendingDown, DollarSign, Percent } from 'lucide-react'

function formatBRL(value) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(value)
}

const statusReceber = {
  'Pendente': 'bg-yellow-100 text-yellow-700',
  'Vencido': 'bg-red-100 text-red-700',
  'Recebido': 'bg-green-100 text-green-700',
}
const statusPagar = {
  'Pendente': 'bg-yellow-100 text-yellow-700',
  'Pago': 'bg-green-100 text-green-700',
}

export default function Financeiro() {
  const { mensal, contasReceber, contasPagar } = financeiro

  const receitaTotal = mensal.reduce((s, m) => s + m.receita, 0)
  const despesasTotal = mensal.reduce((s, m) => s + m.despesas, 0)
  const lucroTotal = mensal.reduce((s, m) => s + m.lucro, 0)
  const margem = ((lucroTotal / receitaTotal) * 100).toFixed(1)

  return (
    <div className="space-y-5">
      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KpiCard icon={TrendingUp} label="Receita Total (Ano)" value={formatBRL(receitaTotal)} color="blue" />
        <KpiCard icon={TrendingDown} label="Despesas Total (Ano)" value={formatBRL(despesasTotal)} color="red" />
        <KpiCard icon={DollarSign} label="Lucro Líquido (Ano)" value={formatBRL(lucroTotal)} color="green" />
        <KpiCard icon={Percent} label="Margem de Lucro" value={`${margem}%`} color="purple" />
      </div>

      {/* Area Chart */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
        <h2 className="text-base font-semibold text-slate-700 mb-4">Evolução Financeira 2024</h2>
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={mensal}>
            <defs>
              <linearGradient id="gradReceita" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="gradLucro" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.15}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="mes" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={v => `R$${(v/1000).toFixed(0)}k`} />
            <Tooltip formatter={v => formatBRL(v)} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Area type="monotone" dataKey="receita" name="Receita" stroke="#3b82f6" fill="url(#gradReceita)" strokeWidth={2} />
            <Area type="monotone" dataKey="despesas" name="Despesas" stroke="#f97316" fill="none" strokeWidth={2} strokeDasharray="4 4" />
            <Area type="monotone" dataKey="lucro" name="Lucro" stroke="#10b981" fill="url(#gradLucro)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Bar Chart */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
        <h2 className="text-base font-semibold text-slate-700 mb-4">Lucro Mensal</h2>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={mensal}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="mes" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={v => `R$${(v/1000).toFixed(0)}k`} />
            <Tooltip formatter={v => formatBRL(v)} />
            <Bar dataKey="lucro" name="Lucro" fill="#10b981" radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Tables */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Contas a Receber */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 bg-green-50">
            <h2 className="text-base font-semibold text-green-800">Contas a Receber</h2>
            <p className="text-xs text-green-600">
              Total: {formatBRL(contasReceber.reduce((s, c) => s + c.valor, 0))}
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 text-xs text-slate-500 font-semibold uppercase">
                  <th className="text-left px-4 py-3">Cliente</th>
                  <th className="text-left px-4 py-3">Valor</th>
                  <th className="text-left px-4 py-3">Venc.</th>
                  <th className="text-left px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {contasReceber.map(c => (
                  <tr key={c.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-700 text-xs">{c.cliente}</p>
                      <p className="text-xs text-slate-400 truncate max-w-[160px]">{c.descricao}</p>
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-800 text-xs whitespace-nowrap">{formatBRL(c.valor)}</td>
                    <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">{new Date(c.vencimento).toLocaleDateString('pt-BR')}</td>
                    <td className="px-4 py-3"><span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusReceber[c.status]}`}>{c.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Contas a Pagar */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 bg-red-50">
            <h2 className="text-base font-semibold text-red-800">Contas a Pagar</h2>
            <p className="text-xs text-red-600">
              Total: {formatBRL(contasPagar.reduce((s, c) => s + c.valor, 0))}
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 text-xs text-slate-500 font-semibold uppercase">
                  <th className="text-left px-4 py-3">Fornecedor</th>
                  <th className="text-left px-4 py-3">Valor</th>
                  <th className="text-left px-4 py-3">Venc.</th>
                  <th className="text-left px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {contasPagar.map(c => (
                  <tr key={c.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-700 text-xs">{c.fornecedor}</p>
                      <p className="text-xs text-slate-400 truncate max-w-[160px]">{c.descricao}</p>
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-800 text-xs whitespace-nowrap">{formatBRL(c.valor)}</td>
                    <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">{new Date(c.vencimento).toLocaleDateString('pt-BR')}</td>
                    <td className="px-4 py-3"><span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusPagar[c.status]}`}>{c.status}</span></td>
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

function KpiCard({ icon: Icon, label, value, color }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    red: 'bg-red-50 text-red-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
  }
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-500 font-medium mb-1">{label}</p>
          <p className="text-xl font-bold text-slate-800">{value}</p>
        </div>
        <div className={`p-2.5 rounded-lg ${colors[color]}`}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  )
}
