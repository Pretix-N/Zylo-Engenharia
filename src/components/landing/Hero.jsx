import React from 'react'
import { ArrowRight } from 'lucide-react'
import { hero, CTA_ORCAMENTO } from '../../data/site'

export default function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-[#1e1e1e]">
      {/* Grid técnico de fundo, discreto */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-[0.16]"
        style={{
          backgroundImage:
            'linear-gradient(to right, #ffffff10 1px, transparent 1px), linear-gradient(to bottom, #ffffff10 1px, transparent 1px)',
          backgroundSize: '56px 56px',
          maskImage: 'radial-gradient(ellipse 80% 60% at 50% 0%, #000 40%, transparent 100%)',
          WebkitMaskImage: 'radial-gradient(ellipse 80% 60% at 50% 0%, #000 40%, transparent 100%)',
        }}
      />

      <div className="relative mx-auto w-full max-w-5xl px-5 pb-16 pt-16 sm:px-8 sm:pb-20 sm:pt-24">
        <p className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#2a2a2a] bg-[#141414] px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-500">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
          BIM · Hidrossanitário
        </p>

        <h1 className="max-w-3xl text-[2rem] font-black leading-[1.12] tracking-tight text-white sm:text-5xl lg:text-[3.4rem]">
          {hero.titulo}
        </h1>

        <p className="mt-6 max-w-2xl text-base leading-relaxed text-gray-400 sm:text-lg">
          {hero.subtitulo}
        </p>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
          <a
            href={CTA_ORCAMENTO}
            target="_blank"
            rel="noopener noreferrer"
            className="group inline-flex items-center justify-center gap-2 rounded-xl bg-amber-500 px-7 py-4 text-base font-bold text-black transition-colors hover:bg-amber-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0f0f0f]"
          >
            Solicitar Orçamento
            <ArrowRight size={18} className="transition-transform group-hover:translate-x-0.5" />
          </a>
          <a
            href="#portfolio"
            className="inline-flex items-center justify-center rounded-xl border border-[#2a2a2a] px-7 py-4 text-base font-semibold text-gray-300 transition-colors hover:border-[#3a3a3a] hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
          >
            Ver projetos
          </a>
        </div>

        <ul className="mt-10 flex flex-wrap gap-x-6 gap-y-3 border-t border-[#1e1e1e] pt-6 text-[13px] text-gray-500">
          {hero.marcadores.map((m) => (
            <li key={m} className="flex items-center gap-2">
              <span className="h-1 w-1 rounded-full bg-amber-500/70" />
              {m}
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
