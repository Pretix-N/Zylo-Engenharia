import React from 'react'
import { Zap } from 'lucide-react'
import Hero from '../components/landing/Hero'
import Portfolio from '../components/landing/Portfolio'
import Processo from '../components/landing/Processo'
import Contato from '../components/landing/Contato'
import { contato, CTA_ORCAMENTO } from '../data/site'

const secoes = [
  { href: '#portfolio', label: 'Projetos' },
  { href: '#processo', label: 'Como funciona' },
  { href: '#contato', label: 'Contato' },
]

function Marca() {
  return (
    <span className="flex items-center gap-2.5">
      <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-500">
        <Zap size={16} className="text-black" />
      </span>
      <span className="leading-none">
        <span className="block text-base font-black tracking-tight text-white">ZYLO</span>
        <span className="block text-[9px] font-bold tracking-[0.2em] text-amber-500">ENGENHARIA</span>
      </span>
    </span>
  )
}

export default function Landing() {
  return (
    <div className="min-h-screen bg-[#0f0f0f]">
      <header className="sticky top-0 z-50 border-b border-[#1e1e1e] bg-[#0f0f0f]/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-5 py-3.5 sm:px-8">
          <a href="#topo" aria-label="Zylo Engenharia — início">
            <Marca />
          </a>

          <nav className="hidden items-center gap-7 md:flex">
            {secoes.map((s) => (
              <a
                key={s.href}
                href={s.href}
                className="text-sm font-medium text-gray-400 transition-colors hover:text-white"
              >
                {s.label}
              </a>
            ))}
          </nav>

          <a
            href={CTA_ORCAMENTO}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-xl bg-amber-500 px-4 py-2.5 text-sm font-bold text-black transition-colors hover:bg-amber-400"
          >
            Solicitar Orçamento
          </a>
        </div>
      </header>

      <main id="topo">
        <Hero />
        <Portfolio />
        <Processo />
        <Contato />
      </main>

      <footer className="border-t border-[#1e1e1e] bg-[#0f0f0f]">
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-5 px-5 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <Marca />
          <div className="flex flex-col gap-1 text-sm text-gray-500 sm:items-end">
            <a href={`mailto:${contato.email}`} className="transition-colors hover:text-amber-400">
              {contato.email}
            </a>
            <a
              href={CTA_ORCAMENTO}
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-amber-400"
            >
              WhatsApp {contato.whatsappExibicao}
            </a>
          </div>
        </div>
        <div className="border-t border-[#1e1e1e]">
          <p className="mx-auto w-full max-w-5xl px-5 py-4 text-center text-xs text-gray-600 sm:px-8 sm:text-left">
            © {new Date().getFullYear()} Zylo · Modelagem e compatibilização hidrossanitária em Revit.
          </p>
        </div>
      </footer>
    </div>
  )
}
