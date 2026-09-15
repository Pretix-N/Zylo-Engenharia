import React, { useEffect, useState } from 'react'
import { Download, ImageOff, MessageCircle } from 'lucide-react'
import { projetos, PORTFOLIO_PDF, whatsappLink } from '../../data/site'

function ProjetoCard({ projeto }) {
  const [falhou, setFalhou] = useState(false)

  return (
    <figure className="group overflow-hidden rounded-2xl border border-[#1e1e1e] bg-[#111] transition-colors hover:border-[#2e2e2e]">
      <div className="relative aspect-[4/3] w-full overflow-hidden bg-[#0a0a0a]">
        {falhou ? (
          <div className="flex h-full w-full flex-col items-center justify-center gap-3 px-6 text-center">
            <ImageOff size={26} className="text-[#3a3a3a]" />
            <p className="text-xs leading-relaxed text-gray-600">
              Imagem pendente — adicione o arquivo em
              <br />
              <code className="text-[11px] text-gray-500">public{projeto.imagem}</code>
            </p>
          </div>
        ) : (
          <img
            src={projeto.imagem}
            alt={projeto.alt}
            loading="lazy"
            onError={() => setFalhou(true)}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
          />
        )}
      </div>

      <figcaption className="border-t border-[#1e1e1e] p-6">
        <h3 className="text-lg font-bold tracking-tight text-white">{projeto.titulo}</h3>
        <p className="mt-2 text-sm leading-relaxed text-gray-400">{projeto.resumo}</p>

        {projeto.specs?.length > 0 && (
          <dl className="mt-4 space-y-1.5 border-t border-[#1e1e1e] pt-4">
            {projeto.specs.map((spec) => (
              <div key={spec.rotulo} className="flex justify-between gap-4 text-[13px]">
                <dt className="text-gray-600">{spec.rotulo}</dt>
                <dd className="text-right font-medium text-gray-300">{spec.valor}</dd>
              </div>
            ))}
          </dl>
        )}
      </figcaption>
    </figure>
  )
}

export default function Portfolio() {
  // O PDF é o CTA mais importante da página: se o arquivo ainda não foi
  // publicado, o botão vira WhatsApp em vez de entregar um 404.
  const [pdfDisponivel, setPdfDisponivel] = useState(true)

  useEffect(() => {
    let ativo = true
    fetch(PORTFOLIO_PDF, { method: 'HEAD' })
      .then((r) => {
        const ok = r.ok && !(r.headers.get('content-type') || '').includes('text/html')
        if (ativo) setPdfDisponivel(ok)
      })
      .catch(() => ativo && setPdfDisponivel(false))
    return () => {
      ativo = false
    }
  }, [])

  return (
    <section id="portfolio" className="scroll-mt-20 border-b border-[#1e1e1e] bg-[#0b0b0b]">
      <div className="mx-auto w-full max-w-5xl px-5 py-16 sm:px-8 sm:py-24">
        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-amber-500">Projetos</p>
        <h2 className="mt-3 max-w-2xl text-2xl font-black tracking-tight text-white sm:text-4xl">
          Modelos entregues, não promessas.
        </h2>

        <div className="mt-12 grid gap-6 sm:gap-8 lg:grid-cols-2">
          {projetos.map((p) => (
            <ProjetoCard key={p.id} projeto={p} />
          ))}
        </div>

        <div className="mt-12 rounded-2xl border border-amber-500/25 bg-amber-500/[0.06] p-6 sm:p-8">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-lg font-bold text-white">Portfólio completo</p>
              <p className="mt-1 text-sm text-gray-400">
                Plantas, isométricos e detalhamento executivo dos projetos.
              </p>
            </div>

            {pdfDisponivel ? (
              <a
                href={PORTFOLIO_PDF}
                download
                className="inline-flex flex-shrink-0 items-center justify-center gap-2 rounded-xl bg-amber-500 px-6 py-4 text-base font-bold text-black transition-colors hover:bg-amber-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0b0b0b]"
              >
                <Download size={18} />
                Baixar Portfólio Completo (PDF)
              </a>
            ) : (
              <a
                href={whatsappLink('Olá, João. Vim pelo site da Zylo e quero receber o portfólio completo em PDF.')}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex flex-shrink-0 items-center justify-center gap-2 rounded-xl bg-amber-500 px-6 py-4 text-base font-bold text-black transition-colors hover:bg-amber-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
              >
                <MessageCircle size={18} />
                Receber Portfólio Completo (PDF)
              </a>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
