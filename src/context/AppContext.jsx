import React, { createContext, useContext, useReducer, useEffect } from 'react'

const initialState = {
  projetos: [
    { id: '1', nome: 'Residencial Alto das Flores', tipo: 'Arquitetônico', clienteId: '1', responsavelId: '1', dataInicio: '2024-01-15', dataPrazo: '2024-08-30', progresso: 78, valor: 245000, status: 'Em Andamento', descricao: 'Projeto arquitetônico de condomínio residencial com 48 unidades.' },
    { id: '2', nome: 'Centro Empresarial Paulista', tipo: 'Estrutural', clienteId: '2', responsavelId: '2', dataInicio: '2023-10-01', dataPrazo: '2024-04-15', progresso: 100, valor: 580000, status: 'Concluído', descricao: 'Projeto estrutural de torre comercial de 22 andares na Av. Paulista.' },
    { id: '3', nome: 'Shopping Meridiano', tipo: 'Hidráulico', clienteId: '3', responsavelId: '3', dataInicio: '2024-02-01', dataPrazo: '2024-10-30', progresso: 45, valor: 320000, status: 'Em Andamento', descricao: 'Sistema hidráulico e sanitário para shopping center com 35.000 m².' },
    { id: '4', nome: 'Hospital São Lucas', tipo: 'Elétrico', clienteId: '4', responsavelId: '4', dataInicio: '2024-03-10', dataPrazo: '2024-07-20', progresso: 15, valor: 410000, status: 'Atrasado', descricao: 'Projeto elétrico completo para nova ala hospitalar com subestação própria.' },
    { id: '5', nome: 'Ponte Sobre o Rio Verde', tipo: 'Estrutural', clienteId: '1', responsavelId: '2', dataInicio: '2024-01-20', dataPrazo: '2024-12-31', progresso: 30, valor: 1200000, status: 'Aguardando Aprovação', descricao: 'Projeto estrutural de ponte estaiada com extensão de 180m.' },
  ],
  clientes: [
    { id: '1', nome: 'Rodrigo Meirelles', empresa: 'Construtora Viva S.A.', email: 'rodrigo@viva.com.br', telefone: '(11) 99234-5678', cidade: 'São Paulo', estado: 'SP', status: 'Ativo' },
    { id: '2', nome: 'Fernanda Costa', empresa: 'Grupo Empreende', email: 'fernanda@empreende.com.br', telefone: '(11) 97654-3210', cidade: 'São Paulo', estado: 'SP', status: 'Ativo' },
    { id: '3', nome: 'Marcelo Trajano', empresa: 'Meridiano Investimentos', email: 'mtrajano@meridiano.com.br', telefone: '(21) 98765-4321', cidade: 'Rio de Janeiro', estado: 'RJ', status: 'Ativo' },
    { id: '4', nome: 'Dr. Henrique Bastos', empresa: 'Rede Hospitalar São Lucas', email: 'h.bastos@saolucas.com.br', telefone: '(41) 99123-4567', cidade: 'Curitiba', estado: 'PR', status: 'Ativo' },
  ],
  equipe: [
    { id: '1', nome: 'Ana Rodrigues', cargo: 'Arquiteta Sênior', especialidade: 'Arquitetura', email: 'ana@zylo.com.br', telefone: '(11) 98765-1234' },
    { id: '2', nome: 'Carlos Mendes', cargo: 'Engenheiro Estrutural', especialidade: 'Estrutural', email: 'carlos@zylo.com.br', telefone: '(11) 97654-5678' },
    { id: '3', nome: 'Paula Fernandes', cargo: 'Engenheira Hidráulica', especialidade: 'Hidráulica', email: 'paula@zylo.com.br', telefone: '(11) 99123-9012' },
    { id: '4', nome: 'Ricardo Alves', cargo: 'Engenheiro Elétrico', especialidade: 'Elétrica', email: 'ricardo@zylo.com.br', telefone: '(11) 98901-3456' },
    { id: '5', nome: 'Mariana Lima', cargo: 'Gerente de Projetos', especialidade: 'Gestão', email: 'mariana@zylo.com.br', telefone: '(11) 99012-6789' },
  ],
  financeiro: {
    mensal: [
      { mes: 'Jan', receita: 320000, despesas: 210000, lucro: 110000 },
      { mes: 'Fev', receita: 285000, despesas: 195000, lucro: 90000 },
      { mes: 'Mar', receita: 410000, despesas: 250000, lucro: 160000 },
      { mes: 'Abr', receita: 375000, despesas: 230000, lucro: 145000 },
      { mes: 'Mai', receita: 490000, despesas: 280000, lucro: 210000 },
      { mes: 'Jun', receita: 520000, despesas: 310000, lucro: 210000 },
      { mes: 'Jul', receita: 445000, despesas: 270000, lucro: 175000 },
      { mes: 'Ago', receita: 610000, despesas: 340000, lucro: 270000 },
      { mes: 'Set', receita: 580000, despesas: 325000, lucro: 255000 },
      { mes: 'Out', receita: 630000, despesas: 360000, lucro: 270000 },
      { mes: 'Nov', receita: 720000, despesas: 390000, lucro: 330000 },
      { mes: 'Dez', receita: 850000, despesas: 420000, lucro: 430000 },
    ],
    contasReceber: [
      { id: '1', cliente: 'Construtora Viva S.A.', descricao: 'Medição #5 - Residencial Alto das Flores', valor: 48000, vencimento: '2024-07-15', status: 'Pendente' },
      { id: '2', cliente: 'SANEPAR', descricao: 'Relatório Técnico - ETA Curitiba', valor: 120000, vencimento: '2024-07-20', status: 'Pendente' },
      { id: '3', cliente: 'Grupo Empreende', descricao: 'Parcela Final - Centro Empresarial', valor: 95000, vencimento: '2024-06-30', status: 'Vencido' },
    ],
    contasPagar: [
      { id: '1', fornecedor: 'AutoCAD / Autodesk', descricao: 'Licenças anuais software', valor: 18500, vencimento: '2024-07-05', status: 'Pendente' },
      { id: '2', fornecedor: 'Escritório SP - Aluguel', descricao: 'Aluguel Av. Paulista - Jul/2024', valor: 22000, vencimento: '2024-07-10', status: 'Pendente' },
      { id: '3', fornecedor: 'Folha de Pagamento', descricao: 'Salários Junho/2024', valor: 165000, vencimento: '2024-07-05', status: 'Pago' },
    ],
  },
}

function reducer(state, action) {
  const newId = () => Date.now().toString()
  switch (action.type) {
    case 'ADD_PROJETO': return { ...state, projetos: [...state.projetos, { ...action.payload, id: newId() }] }
    case 'UPDATE_PROJETO': return { ...state, projetos: state.projetos.map(p => p.id === action.payload.id ? action.payload : p) }
    case 'DELETE_PROJETO': return { ...state, projetos: state.projetos.filter(p => p.id !== action.payload) }
    case 'ADD_CLIENTE': return { ...state, clientes: [...state.clientes, { ...action.payload, id: newId() }] }
    case 'UPDATE_CLIENTE': return { ...state, clientes: state.clientes.map(c => c.id === action.payload.id ? action.payload : c) }
    case 'DELETE_CLIENTE': return { ...state, clientes: state.clientes.filter(c => c.id !== action.payload) }
    case 'ADD_MEMBRO': return { ...state, equipe: [...state.equipe, { ...action.payload, id: newId() }] }
    case 'UPDATE_MEMBRO': return { ...state, equipe: state.equipe.map(m => m.id === action.payload.id ? action.payload : m) }
    case 'DELETE_MEMBRO': return { ...state, equipe: state.equipe.filter(m => m.id !== action.payload) }
    case 'ADD_CONTA_RECEBER': return { ...state, financeiro: { ...state.financeiro, contasReceber: [...state.financeiro.contasReceber, { ...action.payload, id: newId() }] } }
    case 'UPDATE_CONTA_RECEBER': return { ...state, financeiro: { ...state.financeiro, contasReceber: state.financeiro.contasReceber.map(c => c.id === action.payload.id ? action.payload : c) } }
    case 'DELETE_CONTA_RECEBER': return { ...state, financeiro: { ...state.financeiro, contasReceber: state.financeiro.contasReceber.filter(c => c.id !== action.payload) } }
    case 'ADD_CONTA_PAGAR': return { ...state, financeiro: { ...state.financeiro, contasPagar: [...state.financeiro.contasPagar, { ...action.payload, id: newId() }] } }
    case 'UPDATE_CONTA_PAGAR': return { ...state, financeiro: { ...state.financeiro, contasPagar: state.financeiro.contasPagar.map(c => c.id === action.payload.id ? action.payload : c) } }
    case 'DELETE_CONTA_PAGAR': return { ...state, financeiro: { ...state.financeiro, contasPagar: state.financeiro.contasPagar.filter(c => c.id !== action.payload) } }
    default: return state
  }
}

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const saved = localStorage.getItem('zylo-data')
  const [state, dispatch] = useReducer(reducer, saved ? JSON.parse(saved) : initialState)

  useEffect(() => {
    localStorage.setItem('zylo-data', JSON.stringify(state))
  }, [state])

  return <AppContext.Provider value={{ state, dispatch }}>{children}</AppContext.Provider>
}

export function useApp() {
  return useContext(AppContext)
}
