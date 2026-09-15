import React from 'react'
import { processo } from '../../data/site'

export default function Processo() {
  return (
    <section id="processo" className="scroll-mt-20 border-b border-[#1e1e1e]">
      <div className="mx-auto w-full max-w-5xl px-5 py-16 sm:px-8 sm:py-24">
        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-amber-500">Como funciona</p>
        <h2 className="mt-3 text-2xl font-black tracking-tight text-white sm:text-4xl">
          Três etapas. Sem retrabalho.
        </h2>

        <ol className="mt-12 grid gap-6 md:grid-cols-3">
          {processo.map((etapa) => (
            <li
              key={etapa.numero}
              className="rounded-2xl border border-[#1e1e1e] bg-[#111] p-6 transition-colors hover:border-[#2e2e2e]"
            >
              <span className="text-2xl font-black tabular-nums text-amber-500">{etapa.numero}</span>
              <h3 className="mt-4 text-base font-bold tracking-tight text-white">{etapa.titulo}</h3>
              <p className="mt-2 text-sm leading-relaxed text-gray-400">{etapa.texto}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}
