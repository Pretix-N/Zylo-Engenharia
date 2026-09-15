import React, { useState } from 'react'
import { Mail, MessageCircle, Check, AlertTriangle } from 'lucide-react'
import { contato, whatsappLink, CTA_ORCAMENTO } from '../../data/site'
import { enviarLead, resumoParaWhatsapp } from '../../services/leads'

const VAZIO = { nome: '', empresa: '', email: '', mensagem: '' }

const campoClasse =
  'w-full rounded-xl border border-[#2a2a2a] bg-[#0f0f0f] px-4 py-3 text-sm text-white placeholder-gray-600 transition-colors focus:border-amber-500 focus:outline-none'

export default function Contato() {
  const [form, setForm] = useState(VAZIO)
  const [estado, setEstado] = useState('idle') // idle | enviando | ok | erro

  const set = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }))

  async function handleSubmit(e) {
    e.preventDefault()
    setEstado('enviando')
    try {
      await enviarLead(form)
      setEstado('ok')
      setForm(VAZIO)
    } catch {
      setEstado('erro')
    }
  }

  return (
    <section id="contato" className="scroll-mt-20 bg-[#0b0b0b]">
      <div className="mx-auto w-full max-w-5xl px-5 py-16 sm:px-8 sm:py-24">
        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-amber-500">Contato</p>
        <h2 className="mt-3 text-2xl font-black tracking-tight text-white sm:text-4xl">
          Envie o escopo. Retorno com o orçamento.
        </h2>

        <div className="mt-12 grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
          <div className="space-y-3">
            <a
              href={CTA_ORCAMENTO}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-4 rounded-2xl border border-[#1e1e1e] bg-[#111] p-5 transition-colors hover:border-amber-500/40"
            >
              <span className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-amber-500">
                <MessageCircle size={20} className="text-black" />
              </span>
              <span className="min-w-0">
                <span className="block text-[11px] font-bold uppercase tracking-widest text-gray-500">
                  WhatsApp
                </span>
                <span className="block truncate text-sm font-semibold text-white">
                  {contato.whatsappExibicao}
                </span>
              </span>
            </a>

            <a
              href={`mailto:${contato.email}`}
              className="flex items-center gap-4 rounded-2xl border border-[#1e1e1e] bg-[#111] p-5 transition-colors hover:border-amber-500/40"
            >
              <span className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl border border-[#2a2a2a] bg-[#0f0f0f]">
                <Mail size={20} className="text-amber-500" />
              </span>
              <span className="min-w-0">
                <span className="block text-[11px] font-bold uppercase tracking-widest text-gray-500">
                  E-mail
                </span>
                <span className="block truncate text-sm font-semibold text-white">{contato.email}</span>
              </span>
            </a>
          </div>

          <form
            onSubmit={handleSubmit}
            className="space-y-4 rounded-2xl border border-[#1e1e1e] bg-[#111] p-6 sm:p-7"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold text-gray-400">Nome</span>
                <input
                  type="text"
                  required
                  value={form.nome}
                  onChange={set('nome')}
                  placeholder="Seu nome"
                  className={campoClasse}
                />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold text-gray-400">Empresa</span>
                <input
                  type="text"
                  required
                  value={form.empresa}
                  onChange={set('empresa')}
                  placeholder="Escritório ou construtora"
                  className={campoClasse}
                />
              </label>
            </div>

            <label className="block">
              <span className="mb-1.5 block text-xs font-semibold text-gray-400">E-mail</span>
              <input
                type="email"
                required
                value={form.email}
                onChange={set('email')}
                placeholder="voce@empresa.com"
                className={campoClasse}
              />
            </label>

            <label className="block">
              <span className="mb-1.5 block text-xs font-semibold text-gray-400">Mensagem</span>
              <textarea
                required
                rows={5}
                value={form.mensagem}
                onChange={set('mensagem')}
                placeholder="Tipo de obra, metragem, prazo e o que você já tem de arquitetura/estrutura."
                className={`${campoClasse} resize-y`}
              />
            </label>

            <button
              type="submit"
              disabled={estado === 'enviando'}
              className="w-full rounded-xl bg-amber-500 px-6 py-3.5 text-base font-bold text-black transition-colors hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {estado === 'enviando' ? 'Enviando…' : 'Enviar mensagem'}
            </button>

            {estado === 'ok' && (
              <p className="flex items-center gap-2 rounded-xl bg-emerald-500/10 px-4 py-3 text-sm text-emerald-400">
                <Check size={16} className="flex-shrink-0" />
                Mensagem enviada. Retorno em até 1 dia útil.
              </p>
            )}

            {estado === 'erro' && (
              <div className="rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-300">
                <p className="flex items-center gap-2">
                  <AlertTriangle size={16} className="flex-shrink-0" />
                  Não consegui enviar agora.
                </p>
                <a
                  href={whatsappLink(resumoParaWhatsapp(form))}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-1 inline-block font-semibold text-amber-400 underline underline-offset-2"
                >
                  Enviar esta mensagem pelo WhatsApp →
                </a>
              </div>
            )}
          </form>
        </div>
      </div>
    </section>
  )
}
